from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from time import sleep
from typing import Callable, TypeVar

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_pack_registry import CurseForgePackRegistry
from src.core.mod.mod_compatibility_manager import ModCompatibilityManager
from src.core.mod.mod_capability_index import ModCapabilityIndex
from src.core.mod.mod_manager import ModManager
from src.core.mod.mod_provenance_registry import ModProvenanceRegistry
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.modrinth.modrinth_client import ModrinthClient
from src.core.modrinth.modrinth_mod_installer import ModrinthModInstaller
from src.core.modrinth.modrinth_pack_registry import ModrinthPackRegistry
from src.core.network.download_pause import download_pause_controller
from src.core.network.retry_policy import DownloadRetryPolicy
from src.core.progress.progress_reporter import ProgressReporter
from src.models.curseforge.file import CurseForgeDependency, CurseForgeFile
from src.models.instance.instance import Instance
from src.models.mod.dependency_resolution import DependencyResolutionResult, RequiredModDependenciesMissing
from src.models.mod.mod_info import ModInfo
from src.models.mod.mod_issue import ModIssue
from src.models.modrinth.version import ModrinthVersion
from src.models.progress.progress_stage import ProgressStage


T = TypeVar("T")


class ModpackDependencyResolver:
    """Completes required provider dependency graphs for managed modpacks.

    A provider manifest remains authoritative for files it explicitly pins.
    This resolver only appends missing *required* dependencies and never
    replaces a pack-pinned version.
    """

    MAX_DEPTH = 20
    MAX_DEPENDENCIES = 256
    MAX_ATTEMPTS = 3
    BLOCKING_CODES = {"dependency-missing", "dependency-disabled", "dependency-version"}

    @staticmethod
    def resolve(instance: Instance, reporter: ProgressReporter | None = None) -> DependencyResolutionResult:
        if getattr(instance, "instance_dir", None) is None:
            return DependencyResolutionResult()
        added: list[str] = []
        warnings: list[str] = []
        unresolved: list[str] = []

        modrinth = ModrinthPackRegistry.load(instance)
        if ModpackDependencyResolver._has_managed_mods(modrinth.get("managedFiles", [])):
            result = ModpackDependencyResolver._resolve_modrinth(instance, modrinth, reporter)
            added.extend(result.added_files)
            warnings.extend(result.warnings)
            unresolved.extend(result.unresolved)

        curseforge = CurseForgePackRegistry.load(Path(instance.instance_dir))
        if ModpackDependencyResolver._has_managed_mods(curseforge.get("managedFiles", [])):
            result = ModpackDependencyResolver._resolve_curseforge(instance, curseforge, reporter)
            added.extend(result.added_files)
            warnings.extend(result.warnings)
            unresolved.extend(result.unresolved)

        # Provider-declared relations are resolved first, matching Prism's
        # dependency flow. Once those files are present, use the downloaded
        # JAR metadata as a second source of truth and search providers for
        # still-missing required mod IDs. Avoid doing both in the same pass so
        # a dependency already scheduled by project ID is not duplicated by a
        # JAR-level search before it has been downloaded.
        if not added and ModpackDependencyResolver._is_managed_modpack(instance):
            recovery = ModpackDependencyResolver._recover_jar_declared_dependencies(instance, reporter)
            added.extend(recovery.added_files)
            warnings.extend(recovery.warnings)
            unresolved.extend(recovery.unresolved)

        if added:
            ModProvenanceRegistry.synchronize(instance)
        return DependencyResolutionResult(
            added_files=tuple(dict.fromkeys(added)),
            warnings=tuple(dict.fromkeys(warnings)),
            unresolved=tuple(dict.fromkeys(unresolved)),
        )

    @staticmethod
    def blocking_issues(instance: Instance) -> tuple:
        report = ModCompatibilityManager.scan(instance)
        return tuple(
            issue
            for issue in report.issues
            if issue.severity == "error" and issue.code in ModpackDependencyResolver.BLOCKING_CODES
        )

    @staticmethod
    def raise_for_required_dependencies(instance: Instance, unresolved: tuple[str, ...] | list[str] = ()) -> None:
        if not ModpackDependencyResolver._is_managed_modpack(instance):
            return
        issues = list(ModpackDependencyResolver.blocking_issues(instance))
        issues.extend(
            ModIssue(severity="error", code="dependency-unresolved", message=str(message), mod_ids=())
            for message in unresolved
            if str(message).strip()
        )
        if issues:
            raise RequiredModDependenciesMissing(instance.name, tuple(issues))

    @staticmethod
    def _resolve_modrinth(instance: Instance, registry: dict, reporter: ProgressReporter | None) -> DependencyResolutionResult:
        entries = [entry for entry in registry.get("managedFiles", []) if isinstance(entry, dict)]
        mod_entries = [entry for entry in entries if ModpackDependencyResolver._is_mod_entry(entry)]
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        loader_name = str(loader_name).strip().casefold()
        selected: dict[str, dict] = {}
        versions: dict[str, ModrinthVersion] = {}
        warnings: list[str] = []
        unresolved: list[str] = []
        added: list[str] = []
        changed = False

        ModpackDependencyResolver._report(reporter, "Resolving Modrinth modpack dependencies...", 0, max(1, len(mod_entries)))
        for completed, entry in enumerate(mod_entries, start=1):
            download_pause_controller.raise_if_requested()
            entry.setdefault("selectionReason", "pack_manifest")
            entry.setdefault("requiredBy", [])
            try:
                version = ModpackDependencyResolver._modrinth_version_for_entry(entry)
            except Exception as error:
                warnings.append(f"Could not identify Modrinth dependency metadata for {entry.get('fileName') or entry.get('path')}: {error}")
                ModpackDependencyResolver._report(reporter, "Resolving Modrinth modpack dependencies...", completed, max(1, len(mod_entries)))
                continue
            if version is None:
                warnings.append(f"Modrinth file identity is unavailable: {entry.get('fileName') or entry.get('path')}")
                ModpackDependencyResolver._report(reporter, "Resolving Modrinth modpack dependencies...", completed, max(1, len(mod_entries)))
                continue
            changed |= ModpackDependencyResolver._hydrate_modrinth_entry(entry, version)
            selected.setdefault(version.project_id, entry)
            versions[version.version_id] = version
            ModpackDependencyResolver._report(reporter, "Resolving Modrinth modpack dependencies...", completed, max(1, len(mod_entries)))

        queue: deque[tuple[ModrinthVersion, int, str]] = deque(
            (version, 0, ModpackDependencyResolver._entry_label(selected.get(version.project_id, {}), version.project_id))
            for version in versions.values()
        )
        visited_versions: set[str] = set()
        discovered = 0

        while queue:
            version, depth, parent_label = queue.popleft()
            if version.version_id in visited_versions:
                continue
            if depth > ModpackDependencyResolver.MAX_DEPTH:
                unresolved.append(f"Modrinth dependency depth exceeded {ModpackDependencyResolver.MAX_DEPTH} at {parent_label}.")
                continue
            visited_versions.add(version.version_id)
            for dependency in version.dependencies:
                if dependency.dependency_type != "required":
                    continue
                download_pause_controller.raise_if_requested()
                if dependency.project_id and dependency.project_id in selected:
                    target = selected[dependency.project_id]
                    changed |= ModpackDependencyResolver._append_required_by(target, parent_label)
                    if dependency.version_id and str(target.get("versionId") or "") not in {"", dependency.version_id}:
                        warnings.append(
                            f"{parent_label} requests Modrinth version {dependency.version_id}, but the modpack pins "
                            f"{target.get('versionId')}; the pack-pinned file was kept."
                        )
                    continue
                try:
                    dependency_version = ModpackDependencyResolver._retry(
                        lambda dependency=dependency: ModrinthModInstaller._resolve_dependency(
                            dependency.version_id,
                            dependency.project_id,
                            instance.version_id,
                            loader_name,
                            ("release", "beta", "alpha"),
                        )
                    )
                except Exception as error:
                    label = dependency.file_name or dependency.project_id or dependency.version_id or "unknown dependency"
                    unresolved.append(f"{parent_label} requires Modrinth dependency {label}: {error}")
                    continue
                if dependency_version is None:
                    label = dependency.file_name or dependency.project_id or dependency.version_id or "unknown dependency"
                    unresolved.append(f"{parent_label} requires external dependency {label}, which has no provider project/version ID.")
                    continue
                if dependency_version.project_id in selected:
                    target = selected[dependency_version.project_id]
                    changed |= ModpackDependencyResolver._append_required_by(target, parent_label)
                    continue
                try:
                    ModrinthModInstaller._validate_version(dependency_version, instance.version_id, loader_name)
                    project = ModpackDependencyResolver._retry(lambda: ModrinthClient.get_project(dependency_version.project_id))
                    file = dependency_version.primary_file(".jar")
                except Exception as error:
                    unresolved.append(f"{parent_label} dependency {dependency_version.project_id} is not installable: {error}")
                    continue
                if discovered >= ModpackDependencyResolver.MAX_DEPENDENCIES:
                    unresolved.append(f"The Modrinth dependency graph exceeds {ModpackDependencyResolver.MAX_DEPENDENCIES} added files.")
                    queue.clear()
                    break
                path = ModpackDependencyResolver._unique_mod_path(entries, file.filename, dependency_version.project_id, file.sha1)
                target = {
                    "path": path,
                    "fileName": PurePosixPath(path).name,
                    "sha1": file.sha1,
                    "sha512": file.sha512,
                    "size": file.size,
                    "source": "download",
                    "provider": "modrinth",
                    "projectId": dependency_version.project_id,
                    "versionId": dependency_version.version_id,
                    "versionNumber": dependency_version.version_number,
                    "downloads": [file.url] if file.url else [],
                    "required": True,
                    "selectionReason": "required_dependency",
                    "requiredBy": [parent_label],
                    "displayName": project.title,
                }
                entries.append(target)
                selected[dependency_version.project_id] = target
                added.append(project.title or target["fileName"])
                discovered += 1
                changed = True
                queue.append((dependency_version, depth + 1, project.title or target["fileName"]))

        if changed or unresolved:
            registry["managedFiles"] = entries
            registry["dependencyResolution"] = ModpackDependencyResolver._resolution_payload(added, unresolved)
            registry["verificationCache"] = ModrinthPackRegistry._normalize_verification_cache(
                registry.get("verificationCache", {}), entries
            )
            ModrinthPackRegistry.save(instance.instance_dir, registry)
        return DependencyResolutionResult(tuple(added), tuple(warnings), tuple(unresolved))

    @staticmethod
    def _resolve_curseforge(instance: Instance, registry: dict, reporter: ProgressReporter | None) -> DependencyResolutionResult:
        entries = [entry for entry in registry.get("managedFiles", []) if isinstance(entry, dict)]
        mod_entries = [entry for entry in entries if ModpackDependencyResolver._is_mod_entry(entry)]
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        loader_name = str(loader_name).strip().casefold()
        selected: dict[int, dict] = {}
        files: dict[int, CurseForgeFile] = {}
        warnings: list[str] = []
        unresolved: list[str] = []
        added: list[str] = []
        changed = False

        unresolved_file_ids: list[int] = []
        for entry in mod_entries:
            try:
                file_id = int(entry.get("fileId") or 0)
            except (TypeError, ValueError):
                file_id = 0
            if file_id > 0 and not bool(entry.get("dependencyMetadataResolved", False)):
                unresolved_file_ids.append(file_id)
        batch_files: dict[int, CurseForgeFile] = {}
        if unresolved_file_ids:
            try:
                batch_files = ModpackDependencyResolver._retry(lambda: CurseForgeClient.get_files_batch(unresolved_file_ids))
            except Exception as error:
                warnings.append(f"Could not batch-load CurseForge dependency metadata: {error}")

        ModpackDependencyResolver._report(reporter, "Resolving CurseForge modpack dependencies...", 0, max(1, len(mod_entries)))
        for completed, entry in enumerate(mod_entries, start=1):
            download_pause_controller.raise_if_requested()
            try:
                project_id = int(entry.get("projectId") or 0)
                file_id = int(entry.get("fileId") or 0)
            except (TypeError, ValueError):
                project_id = file_id = 0
            entry.setdefault("selectionReason", "pack_manifest")
            entry.setdefault("requiredBy", [])
            if project_id <= 0 or file_id <= 0:
                warnings.append(f"CurseForge file identity is unavailable: {entry.get('fileName') or entry.get('path')}")
                ModpackDependencyResolver._report(reporter, "Resolving CurseForge modpack dependencies...", completed, max(1, len(mod_entries)))
                continue
            try:
                if bool(entry.get("dependencyMetadataResolved", False)):
                    file = ModpackDependencyResolver._curseforge_file_from_entry(entry)
                else:
                    file = batch_files.get(file_id)
                    if file is None or file.project_id != project_id:
                        file = ModpackDependencyResolver._retry(lambda project_id=project_id, file_id=file_id: CurseForgeClient.get_file(project_id, file_id))
            except Exception as error:
                warnings.append(f"Could not load CurseForge dependency metadata for {entry.get('fileName')}: {error}")
                ModpackDependencyResolver._report(reporter, "Resolving CurseForge modpack dependencies...", completed, max(1, len(mod_entries)))
                continue
            changed |= ModpackDependencyResolver._hydrate_curseforge_entry(entry, file)
            selected.setdefault(project_id, entry)
            files[file_id] = file
            ModpackDependencyResolver._report(reporter, "Resolving CurseForge modpack dependencies...", completed, max(1, len(mod_entries)))

        queue: deque[tuple[CurseForgeFile, int, str]] = deque(
            (file, 0, ModpackDependencyResolver._entry_label(selected.get(file.project_id, {}), str(file.project_id)))
            for file in files.values()
        )
        visited_files: set[int] = set()
        discovered = 0

        while queue:
            file, depth, parent_label = queue.popleft()
            if file.file_id in visited_files:
                continue
            if depth > ModpackDependencyResolver.MAX_DEPTH:
                unresolved.append(f"CurseForge dependency depth exceeded {ModpackDependencyResolver.MAX_DEPTH} at {parent_label}.")
                continue
            visited_files.add(file.file_id)
            for dependency in file.dependencies:
                if not dependency.required:
                    continue
                download_pause_controller.raise_if_requested()
                if dependency.project_id in selected:
                    changed |= ModpackDependencyResolver._append_required_by(selected[dependency.project_id], parent_label)
                    continue
                try:
                    dependency_file = ModpackDependencyResolver._retry(
                        lambda dependency=dependency: CurseForgeClient.latest_compatible_file(
                            dependency.project_id,
                            instance.version_id,
                            loader=loader_name,
                            release_types=("release", "beta", "alpha"),
                        )
                    )
                except Exception as error:
                    unresolved.append(f"{parent_label} requires CurseForge project {dependency.project_id}: {error}")
                    continue
                if dependency_file.project_id in selected:
                    changed |= ModpackDependencyResolver._append_required_by(selected[dependency_file.project_id], parent_label)
                    continue
                if discovered >= ModpackDependencyResolver.MAX_DEPENDENCIES:
                    unresolved.append(f"The CurseForge dependency graph exceeds {ModpackDependencyResolver.MAX_DEPENDENCIES} added files.")
                    queue.clear()
                    break
                try:
                    project = ModpackDependencyResolver._retry(lambda: CurseForgeClient.get_project(dependency_file.project_id))
                    project_name = str(getattr(project, "name", "") or dependency_file.display_name).strip()
                    project_url = str(getattr(project, "project_url", "") or "").strip()
                except Exception:
                    project_name = dependency_file.display_name
                    project_url = ""
                path = ModpackDependencyResolver._unique_mod_path(entries, dependency_file.file_name, str(dependency_file.project_id), dependency_file.sha1)
                target = {
                    "projectId": dependency_file.project_id,
                    "fileId": dependency_file.file_id,
                    "fileName": PurePosixPath(path).name,
                    "path": path,
                    "displayName": project_name or dependency_file.file_name,
                    "sha1": dependency_file.sha1,
                    "size": dependency_file.file_length,
                    "downloadUrl": dependency_file.download_url,
                    "declaredLoaders": list(dependency_file.loaders),
                    "gameVersions": list(dependency_file.game_versions),
                    "releaseType": dependency_file.release_type,
                    "datePublished": dependency_file.file_date,
                    "required": True,
                    "provider": "curseforge",
                    "pendingDownload": True,
                    "resolvePathFromProvider": False,
                    "selectionReason": "required_dependency",
                    "requiredBy": [parent_label],
                    "projectUrl": project_url,
                    "dependencies": [{"projectId": dependency.project_id, "relationType": dependency.relation_type} for dependency in dependency_file.dependencies],
                    "dependencyMetadataResolved": True,
                }
                entries.append(target)
                selected[dependency_file.project_id] = target
                added.append(project_name or target["fileName"])
                discovered += 1
                changed = True
                queue.append((dependency_file, depth + 1, project_name or target["fileName"]))

        if changed or unresolved:
            registry["managedFiles"] = entries
            registry["dependencyResolution"] = ModpackDependencyResolver._resolution_payload(added, unresolved)
            CurseForgePackRegistry.save(Path(instance.instance_dir), registry)
        return DependencyResolutionResult(tuple(added), tuple(warnings), tuple(unresolved))

    @staticmethod
    def _recover_jar_declared_dependencies(instance: Instance, reporter: ProgressReporter | None) -> DependencyResolutionResult:
        mods = ModManager.list_mods(instance)
        if not mods:
            return DependencyResolutionResult()

        report = ModCompatibilityManager.scan(instance, mods=mods)
        missing = [issue for issue in report.issues if issue.severity == "error" and issue.code == "dependency-missing" and len(issue.mod_ids) >= 2]
        if not missing:
            return DependencyResolutionResult()

        by_id = {mod.mod_id.casefold(): mod for mod in mods if mod.enabled and mod.mod_id.casefold() != "unknown"}
        requests: dict[str, dict[str, object]] = {}
        for issue in missing:
            parent_id = str(issue.mod_ids[0]).strip().casefold()
            dependency_id = str(issue.mod_ids[1]).strip().casefold()
            if not dependency_id or dependency_id in ModCompatibilityManager.SYSTEM_DEPENDENCY_IDS:
                continue
            parent = by_id.get(parent_id)
            requirement = parent.dependencies.get(dependency_id, "*") if parent is not None else "*"
            entry = requests.setdefault(dependency_id, {"requiredBy": [], "requirements": []})
            parent_label = parent.name if parent is not None else parent_id or "Unknown mod"
            if parent_label not in entry["requiredBy"]:
                entry["requiredBy"].append(parent_label)
            requirement_text = ModCompatibilityManager._format_requirement(requirement)
            if requirement_text not in entry["requirements"]:
                entry["requirements"].append(requirement_text)

        if not requests:
            return DependencyResolutionResult()

        added: list[str] = []
        warnings: list[str] = []
        unresolved: list[str] = []
        total = len(requests)
        ModpackDependencyResolver._report(reporter, "Searching for missing mod dependencies...", 0, total)

        for completed, (dependency_id, request) in enumerate(sorted(requests.items()), start=1):
            download_pause_controller.raise_if_requested()
            pending = ModpackDependencyResolver._pending_candidate(instance, dependency_id)
            if pending:
                ModpackDependencyResolver._report(reporter, "Searching for missing mod dependencies...", completed, total)
                continue

            excluded = ModpackDependencyResolver._rejected_or_installed_candidates(instance, dependency_id)
            candidate, search_errors = ModpackDependencyResolver._find_dependency_candidate(instance, dependency_id, excluded)
            if candidate is None:
                requirement_text = " and ".join(str(value) for value in request["requirements"] if str(value).strip()) or "*"
                detail = "; ".join(search_errors)
                message = f"Could not resolve required dependency '{dependency_id}' ({requirement_text}) from Modrinth or CurseForge."
                if detail:
                    message += f" {detail}"
                unresolved.append(message)
                ModpackDependencyResolver._report(reporter, "Searching for missing mod dependencies...", completed, total)
                continue

            required_by = [str(value) for value in request["requiredBy"] if str(value).strip()]
            requirements = [str(value) for value in request["requirements"] if str(value).strip()]
            if candidate["provider"] == "modrinth":
                ModpackDependencyResolver._append_modrinth_search_candidate(instance, candidate, dependency_id, required_by, requirements)
            else:
                ModpackDependencyResolver._append_curseforge_search_candidate(instance, candidate, dependency_id, required_by, requirements)
            title = str(candidate.get("title") or dependency_id)
            added.append(title)
            warnings.append(f"Scheduled {title} from {candidate['provider'].title()} to satisfy missing dependency '{dependency_id}'.")
            ModpackDependencyResolver._report(reporter, "Searching for missing mod dependencies...", completed, total)

        return DependencyResolutionResult(tuple(added), tuple(warnings), tuple(unresolved))

    @staticmethod
    def _find_dependency_candidate(instance: Instance, dependency_id: str, excluded: dict[str, set[str]]) -> tuple[dict | None, list[str]]:
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        loader_name = str(loader_name).strip().casefold()
        errors: list[str] = []
        for provider in ModpackDependencyResolver._provider_priority(instance):
            try:
                if provider == "modrinth":
                    candidate = ModpackDependencyResolver._search_modrinth_by_mod_id(instance, dependency_id, loader_name, excluded.get("modrinth", set()))
                else:
                    candidate = ModpackDependencyResolver._search_curseforge_by_mod_id(instance, dependency_id, loader_name, excluded.get("curseforge", set()))
            except Exception as error:
                errors.append(f"{provider.title()} search failed: {error}")
                continue
            if candidate is not None:
                return candidate, errors
        return None, errors

    @staticmethod
    def _search_modrinth_by_mod_id(instance: Instance, dependency_id: str, loader_name: str, excluded: set[str]) -> dict | None:
        result = ModpackDependencyResolver._retry(
            lambda: ModrinthClient.search_projects(
                "mod",
                query=dependency_id,
                game_version=instance.version_id,
                loader=loader_name,
                index="relevance",
                offset=0,
                limit=10,
                force_refresh=False,
            )
        )
        projects = sorted(result.projects, key=lambda project: ModpackDependencyResolver._project_match_score(dependency_id, project.slug, project.title))
        for project in projects:
            score = ModpackDependencyResolver._project_match_score(dependency_id, project.slug, project.title)
            if score > 1 or project.project_id in excluded:
                continue
            try:
                version = ModpackDependencyResolver._retry(
                    lambda project_id=project.project_id: ModrinthClient.select_version(
                        project_id,
                        game_version=instance.version_id,
                        loader=loader_name,
                        version_types=("release", "beta", "alpha"),
                    )
                )
                ModrinthModInstaller._validate_version(version, instance.version_id, loader_name)
                file = version.primary_file(".jar")
            except Exception:
                continue
            return {
                "provider": "modrinth",
                "project": project,
                "version": version,
                "file": file,
                "title": project.title,
            }
        return None

    @staticmethod
    def _search_curseforge_by_mod_id(instance: Instance, dependency_id: str, loader_name: str, excluded: set[str]) -> dict | None:
        result = ModpackDependencyResolver._retry(
            lambda: CurseForgeClient.search_projects(
                "mod",
                query=dependency_id,
                game_version=instance.version_id,
                loader=loader_name,
                index=0,
                page_size=10,
                sort="popularity",
                force_refresh=False,
            )
        )
        projects = sorted(result.projects, key=lambda project: ModpackDependencyResolver._project_match_score(dependency_id, project.slug, project.name))
        for project in projects:
            score = ModpackDependencyResolver._project_match_score(dependency_id, project.slug, project.name)
            if score > 1 or str(project.project_id) in excluded:
                continue
            try:
                file = ModpackDependencyResolver._retry(
                    lambda project_id=project.project_id: CurseForgeClient.latest_compatible_file(
                        project_id,
                        instance.version_id,
                        loader=loader_name,
                        release_types=("release", "beta", "alpha"),
                    )
                )
                if not file.file_name.casefold().endswith(".jar"):
                    continue
            except Exception:
                continue
            return {
                "provider": "curseforge",
                "project": project,
                "file": file,
                "title": project.name,
            }
        return None

    @staticmethod
    def _append_modrinth_search_candidate(instance: Instance, candidate: dict, dependency_id: str, required_by: list[str], requirements: list[str]) -> None:
        registry = ModrinthPackRegistry.load(instance)
        entries = [entry for entry in registry.get("managedFiles", []) if isinstance(entry, dict)]
        all_entries = entries + [entry for entry in CurseForgePackRegistry.load(Path(instance.instance_dir)).get("managedFiles", []) if isinstance(entry, dict)]
        project = candidate["project"]
        version = candidate["version"]
        file = candidate["file"]
        path = ModpackDependencyResolver._unique_mod_path(all_entries, file.filename, version.project_id, file.sha1)
        entries.append({
            "path": path,
            "fileName": PurePosixPath(path).name,
            "sha1": file.sha1,
            "sha512": file.sha512,
            "size": file.size,
            "source": "download",
            "provider": "modrinth",
            "projectId": version.project_id,
            "versionId": version.version_id,
            "versionNumber": version.version_number,
            "downloads": [file.url] if file.url else [],
            "required": True,
            "selectionReason": "jar_audit_dependency",
            "requiredBy": required_by,
            "displayName": project.title,
            "providesModId": dependency_id,
            "requestedVersionRanges": requirements,
        })
        registry["managedFiles"] = entries
        registry["dependencyResolution"] = ModpackDependencyResolver._resolution_payload([project.title], [])
        registry["verificationCache"] = ModrinthPackRegistry._normalize_verification_cache(registry.get("verificationCache", {}), entries)
        ModrinthPackRegistry.save(instance.instance_dir, registry)

    @staticmethod
    def _append_curseforge_search_candidate(instance: Instance, candidate: dict, dependency_id: str, required_by: list[str], requirements: list[str]) -> None:
        registry = CurseForgePackRegistry.load(Path(instance.instance_dir))
        entries = [entry for entry in registry.get("managedFiles", []) if isinstance(entry, dict)]
        all_entries = entries + [entry for entry in ModrinthPackRegistry.load(instance).get("managedFiles", []) if isinstance(entry, dict)]
        project = candidate["project"]
        file = candidate["file"]
        path = ModpackDependencyResolver._unique_mod_path(all_entries, file.file_name, str(file.project_id), file.sha1)
        entries.append({
            "projectId": file.project_id,
            "fileId": file.file_id,
            "fileName": PurePosixPath(path).name,
            "path": path,
            "displayName": project.name or file.display_name,
            "sha1": file.sha1,
            "size": file.file_length,
            "downloadUrl": file.download_url,
            "declaredLoaders": list(file.loaders),
            "gameVersions": list(file.game_versions),
            "releaseType": file.release_type,
            "datePublished": file.file_date,
            "required": True,
            "provider": "curseforge",
            "pendingDownload": True,
            "resolvePathFromProvider": False,
            "selectionReason": "jar_audit_dependency",
            "requiredBy": required_by,
            "projectUrl": project.project_url,
            "dependencies": [{"projectId": dependency.project_id, "relationType": dependency.relation_type} for dependency in file.dependencies],
            "dependencyMetadataResolved": True,
            "providesModId": dependency_id,
            "requestedVersionRanges": requirements,
        })
        registry["managedFiles"] = entries
        registry["dependencyResolution"] = ModpackDependencyResolver._resolution_payload([project.name], [])
        CurseForgePackRegistry.save(Path(instance.instance_dir), registry)

    @staticmethod
    def _pending_candidate(instance: Instance, dependency_id: str) -> bool:
        wanted = dependency_id.casefold()
        for registry in (ModrinthPackRegistry.load(instance), CurseForgePackRegistry.load(Path(instance.instance_dir))):
            for entry in registry.get("managedFiles", []):
                if not isinstance(entry, dict) or str(entry.get("providesModId") or "").casefold() != wanted:
                    continue
                relative = str(entry.get("path") or "").replace("\\", "/").strip().lstrip("/")
                target = Path(instance.instance_dir).joinpath(*PurePosixPath(relative).parts) if relative else None
                if target is None or not target.is_file():
                    return True
        return False

    @staticmethod
    def _rejected_or_installed_candidates(instance: Instance, dependency_id: str) -> dict[str, set[str]]:
        wanted = dependency_id.casefold()
        excluded = {"modrinth": set(), "curseforge": set()}
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        for provider, registry in (
            ("modrinth", ModrinthPackRegistry.load(instance)),
            ("curseforge", CurseForgePackRegistry.load(Path(instance.instance_dir))),
        ):
            for entry in registry.get("managedFiles", []):
                if not isinstance(entry, dict):
                    continue
                project_id = str(entry.get("projectId") or "").strip()
                if project_id:
                    excluded[provider].add(project_id)
                if str(entry.get("providesModId") or "").casefold() != wanted:
                    continue
                relative = str(entry.get("path") or "").replace("\\", "/").strip().lstrip("/")
                target = Path(instance.instance_dir).joinpath(*PurePosixPath(relative).parts) if relative else None
                if target is not None and target.is_file() and ModCapabilityIndex.provides(target, dependency_id, str(loader_name)):
                    # A valid candidate should already remove the compatibility
                    # issue. Keep it excluded from repeated provider searches.
                    continue
        return excluded

    @staticmethod
    def _provider_priority(instance: Instance) -> tuple[str, str]:
        modrinth_count = sum(1 for entry in ModrinthPackRegistry.load(instance).get("managedFiles", []) if isinstance(entry, dict) and ModpackDependencyResolver._is_mod_entry(entry))
        curseforge_count = sum(1 for entry in CurseForgePackRegistry.load(Path(instance.instance_dir)).get("managedFiles", []) if isinstance(entry, dict) and ModpackDependencyResolver._is_mod_entry(entry))
        return ("modrinth", "curseforge") if modrinth_count >= curseforge_count else ("curseforge", "modrinth")

    @staticmethod
    def _project_match_score(dependency_id: str, slug: str, title: str) -> int:
        wanted = ModpackDependencyResolver._search_key(dependency_id)
        slug_key = ModpackDependencyResolver._search_key(slug)
        title_key = ModpackDependencyResolver._search_key(title)
        if wanted and wanted in {slug_key, title_key}:
            return 0
        if wanted and any(wanted in value or value in wanted for value in (slug_key, title_key) if value):
            return 1
        return 99

    @staticmethod
    def _search_key(value: str) -> str:
        return "".join(character for character in str(value or "").casefold() if character.isalnum())

    @staticmethod
    def _modrinth_version_for_entry(entry: dict) -> ModrinthVersion | None:
        version_id = str(entry.get("versionId") or "").strip()
        if not version_id:
            downloads = entry.get("downloads") if isinstance(entry.get("downloads"), list) else []
            for url in downloads:
                identity = ModProvenanceRegistry._modrinth_identity_from_url(str(url))
                if identity is None:
                    continue
                project_id, version_id, remote_name = identity
                entry["projectId"] = str(entry.get("projectId") or project_id)
                entry["versionId"] = version_id
                entry["fileName"] = str(entry.get("fileName") or remote_name)
                break
        if version_id:
            return ModpackDependencyResolver._retry(lambda: ModrinthClient.get_version(version_id))
        for algorithm in ("sha512", "sha1"):
            value = str(entry.get(algorithm) or "").strip().casefold()
            if not value:
                continue
            version = ModpackDependencyResolver._retry(lambda value=value, algorithm=algorithm: ModrinthClient.get_version_from_hash(value, algorithm))
            if version is not None:
                return version
        return None

    @staticmethod
    def _hydrate_modrinth_entry(entry: dict, version: ModrinthVersion) -> bool:
        file = version.primary_file(".jar")
        updates = {
            "projectId": version.project_id,
            "versionId": version.version_id,
            "versionNumber": version.version_number,
            "sha1": str(entry.get("sha1") or file.sha1).casefold(),
            "sha512": str(entry.get("sha512") or file.sha512).casefold(),
            "size": max(0, int(entry.get("size", 0) or file.size)),
            "downloads": list(entry.get("downloads") or ([file.url] if file.url else [])),
        }
        changed = False
        for key, value in updates.items():
            if entry.get(key) != value:
                entry[key] = value
                changed = True
        return changed

    @staticmethod
    def _hydrate_curseforge_entry(entry: dict, file: CurseForgeFile) -> bool:
        updates = {
            "fileName": Path(str(entry.get("fileName") or file.file_name)).name,
            "displayName": str(entry.get("displayName") or file.display_name),
            "sha1": str(entry.get("sha1") or file.sha1).casefold(),
            "size": max(0, int(entry.get("size", 0) or file.file_length)),
            "downloadUrl": str(entry.get("downloadUrl") or file.download_url),
            "declaredLoaders": list(entry.get("declaredLoaders") or file.loaders),
            "gameVersions": list(entry.get("gameVersions") or file.game_versions),
            "releaseType": str(entry.get("releaseType") or file.release_type),
            "datePublished": str(entry.get("datePublished") or file.file_date),
            "dependencies": [{"projectId": dependency.project_id, "relationType": dependency.relation_type} for dependency in file.dependencies],
            "dependencyMetadataResolved": True,
        }
        changed = False
        for key, value in updates.items():
            if entry.get(key) != value:
                entry[key] = value
                changed = True
        return changed

    @staticmethod
    def _curseforge_file_from_entry(entry: dict) -> CurseForgeFile:
        dependencies = tuple(
            CurseForgeDependency(
                project_id=int(raw.get("projectId") or 0),
                relation_type=int(raw.get("relationType") or 0),
            )
            for raw in entry.get("dependencies", [])
            if isinstance(raw, dict) and int(raw.get("projectId") or 0) > 0 and int(raw.get("relationType") or 0) > 0
        )
        return CurseForgeFile(
            file_id=int(entry.get("fileId") or 0),
            project_id=int(entry.get("projectId") or 0),
            display_name=str(entry.get("displayName") or entry.get("fileName") or "Unknown file").strip(),
            file_name=Path(str(entry.get("fileName") or "download.jar")).name,
            release_type=str(entry.get("releaseType") or "release").strip().casefold(),
            file_date=str(entry.get("datePublished") or "").strip(),
            file_length=max(0, int(entry.get("size", 0) or 0)),
            download_url=str(entry.get("downloadUrl") or "").strip(),
            sha1=str(entry.get("sha1") or "").strip().casefold(),
            game_versions=tuple(str(value) for value in entry.get("gameVersions", []) if str(value).strip()),
            dependencies=dependencies,
            is_available=True,
            loaders=tuple(str(value).strip().casefold() for value in entry.get("declaredLoaders", []) if str(value).strip()),
        )

    @staticmethod
    def _append_required_by(entry: dict, parent: str) -> bool:
        existing = entry.get("requiredBy") if isinstance(entry.get("requiredBy"), list) else []
        normalized = list(dict.fromkeys(str(value).strip() for value in existing if str(value).strip()))
        if parent and parent not in normalized:
            normalized.append(parent)
        changed = entry.get("requiredBy") != normalized
        entry["requiredBy"] = normalized
        return changed

    @staticmethod
    def _unique_mod_path(entries: list[dict], filename: str, project_id: str, sha1: str) -> str:
        safe_name = Path(str(filename or "dependency.jar")).name or "dependency.jar"
        candidate = f"mods/{safe_name}"
        existing = {str(entry.get("path") or "").replace("\\", "/").casefold(): entry for entry in entries if isinstance(entry, dict)}
        current = existing.get(candidate.casefold())
        if current is None or (sha1 and str(current.get("sha1") or "").casefold() == sha1.casefold()):
            return candidate
        prefix = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in str(project_id)).strip("-") or "dependency"
        return f"mods/{prefix}-{safe_name}"

    @staticmethod
    def _entry_label(entry: dict, fallback: str) -> str:
        return str(entry.get("displayName") or entry.get("title") or entry.get("fileName") or fallback).strip()

    @staticmethod
    def _resolution_payload(added: list[str], unresolved: list[str]) -> dict:
        return {
            "status": "unresolved" if unresolved else "complete",
            "added": list(dict.fromkeys(added)),
            "unresolved": list(dict.fromkeys(unresolved)),
            "resolvedAt": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _retry(call: Callable[[], T]) -> T:
        last_error: Exception | None = None
        for attempt in range(1, ModpackDependencyResolver.MAX_ATTEMPTS + 1):
            download_pause_controller.raise_if_requested()
            try:
                return call()
            except Exception as error:
                last_error = error
                lowered = str(error).casefold()
                if any(marker in lowered for marker in ("http 400", "http 401", "http 403", "http 404", "not available", "no allowed", "invalid", "unsupported")):
                    break
                decision = DownloadRetryPolicy.decide(error, attempt, ModpackDependencyResolver.MAX_ATTEMPTS)
                if not decision.retry:
                    break
                sleep(min(max(decision.delay_seconds, 0.0), 1.0))
        assert last_error is not None
        raise last_error

    @staticmethod
    def _is_mod_entry(entry: dict) -> bool:
        path = str(entry.get("path") or "").replace("\\", "/").strip().lstrip("/")
        pure = PurePosixPath(path)
        return len(pure.parts) >= 2 and pure.parts[0].casefold() == "mods" and pure.name.casefold().endswith(".jar")

    @staticmethod
    def _has_managed_mods(value: object) -> bool:
        return isinstance(value, list) and any(isinstance(entry, dict) and ModpackDependencyResolver._is_mod_entry(entry) for entry in value)

    @staticmethod
    def _is_managed_modpack(instance: Instance) -> bool:
        if getattr(instance, "instance_dir", None) is None:
            return False
        return bool(ModrinthPackRegistry.load(instance).get("managedFiles") or CurseForgePackRegistry.load(Path(instance.instance_dir)).get("managedFiles"))

    @staticmethod
    def _report(reporter: ProgressReporter | None, message: str, current: int, total: int) -> None:
        if reporter is not None:
            reporter.files(stage=ProgressStage.CHECKING_MODPACK, message=message, current=current, total=total)
