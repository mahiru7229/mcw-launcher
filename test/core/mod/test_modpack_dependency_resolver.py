from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_pack_registry import CurseForgePackRegistry
from src.core.mod.mod_compatibility_manager import ModCompatibilityManager
from src.core.mod.mod_provenance_registry import ModProvenanceRegistry
from src.core.mod.modpack_dependency_resolver import ModpackDependencyResolver
from src.core.modrinth.modrinth_client import ModrinthClient
from src.core.modrinth.modrinth_pack_registry import ModrinthPackRegistry
from src.models.curseforge.file import CurseForgeDependency, CurseForgeFile
from src.models.mod.dependency_resolution import RequiredModDependenciesMissing
from src.models.mod.mod_info import ModInfo
from src.models.mod.mod_issue import ModHealthReport, ModIssue
from src.models.modrinth.project import ModrinthProject
from src.models.modrinth.version import ModrinthDependency, ModrinthFile, ModrinthVersion


def instance(tmp_path, loader="neoforge"):
    return SimpleNamespace(name="Pack", version_id="1.21.1", mod_loader=(loader, "21.1.200"), instance_dir=tmp_path / "Pack")


def mr_version(version_id: str, project_id: str, filename: str, dependencies=()):
    return ModrinthVersion(
        version_id=version_id,
        project_id=project_id,
        name=version_id,
        version_number=version_id,
        version_type="release",
        game_versions=("1.21.1",),
        loaders=("neoforge",),
        files=(ModrinthFile(url=f"https://cdn.modrinth.com/data/{project_id}/versions/{version_id}/{filename}", filename=filename, sha1=(project_id[0] * 40), sha512=(project_id[0] * 128), size=10, primary=True),),
        dependencies=tuple(dependencies),
    )


def cf_file(project_id: int, file_id: int, filename: str, dependencies=()):
    return CurseForgeFile(
        file_id=file_id,
        project_id=project_id,
        display_name=filename,
        file_name=filename,
        release_type="release",
        file_date="2026-01-01T00:00:00Z",
        file_length=10,
        download_url=f"https://edge.forgecdn.net/files/{file_id}/{filename}",
        sha1=(str(project_id)[0] * 40),
        game_versions=("1.21.1",),
        dependencies=tuple(dependencies),
        loaders=("neoforge",),
    )


def test_modrinth_resolver_adds_recursive_required_dependencies(tmp_path, monkeypatch):
    root = mr_version("root-v", "root", "root.jar", (ModrinthDependency("required", project_id="dep-a"),))
    dep_a = mr_version("a-v", "dep-a", "a.jar", (ModrinthDependency("required", project_id="dep-b"),))
    dep_b = mr_version("b-v", "dep-b", "b.jar")
    versions = {item.version_id: item for item in (root, dep_a, dep_b)}
    projects = {project_id: ModrinthProject(project_id=project_id, slug=project_id, title=project_id.title(), description="", project_type="mod") for project_id in ("root", "dep-a", "dep-b")}
    registry = {"projectId": "pack", "versionId": "pack-v", "managedFiles": [{"path": "mods/root.jar", "fileName": "root.jar", "source": "download", "provider": "modrinth", "projectId": "root", "versionId": "root-v", "sha1": "r" * 40, "sha512": "r" * 128, "size": 10, "downloads": ["https://cdn.modrinth.com/root.jar"]}]}
    saved = {}

    monkeypatch.setattr(ModrinthPackRegistry, "load", lambda _instance: registry)
    monkeypatch.setattr(ModrinthPackRegistry, "save", lambda _dir, payload: saved.update(payload))
    monkeypatch.setattr(CurseForgePackRegistry, "load", lambda _instance: {})
    monkeypatch.setattr(ModProvenanceRegistry, "synchronize", lambda _instance: {})
    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: versions[version_id])
    monkeypatch.setattr(ModrinthClient, "select_version", lambda project_id, **_kwargs: {"dep-a": dep_a, "dep-b": dep_b}[project_id])
    monkeypatch.setattr(ModrinthClient, "get_project", lambda project_id: projects[project_id])

    result = ModpackDependencyResolver.resolve(instance(tmp_path))

    assert result.added_files == ("Dep-A", "Dep-B")
    by_project = {entry.get("projectId"): entry for entry in saved["managedFiles"]}
    assert by_project["dep-a"]["selectionReason"] == "required_dependency"
    assert by_project["dep-a"]["requiredBy"] == ["root.jar"]
    assert by_project["dep-b"]["requiredBy"] == ["Dep-A"]


def test_modrinth_resolver_keeps_pack_pinned_dependency_version(tmp_path, monkeypatch):
    root = mr_version("root-v", "root", "root.jar", (ModrinthDependency("required", project_id="dep", version_id="new-v"),))
    old = mr_version("old-v", "dep", "dep-old.jar")
    registry = {"managedFiles": [
        {"path": "mods/root.jar", "fileName": "root.jar", "source": "download", "provider": "modrinth", "projectId": "root", "versionId": "root-v", "sha1": "r" * 40, "sha512": "r" * 128, "size": 10, "downloads": []},
        {"path": "mods/dep-old.jar", "fileName": "dep-old.jar", "source": "download", "provider": "modrinth", "projectId": "dep", "versionId": "old-v", "sha1": "d" * 40, "sha512": "d" * 128, "size": 10, "downloads": []},
    ]}
    monkeypatch.setattr(ModrinthPackRegistry, "load", lambda _instance: registry)
    monkeypatch.setattr(ModrinthPackRegistry, "save", lambda *_args: None)
    monkeypatch.setattr(CurseForgePackRegistry, "load", lambda _instance: {})
    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: {"root-v": root, "old-v": old}[version_id])

    result = ModpackDependencyResolver.resolve(instance(tmp_path))

    assert not result.added_files
    assert any("pack-pinned file was kept" in warning for warning in result.warnings)
    assert registry["managedFiles"][1]["requiredBy"] == ["root.jar"]


def test_curseforge_resolver_adds_only_required_dependencies(tmp_path, monkeypatch):
    root = cf_file(10, 100, "root.jar", (CurseForgeDependency(20, 3), CurseForgeDependency(30, 2)))
    required = cf_file(20, 200, "required.jar")
    registry = {"managedFiles": [{"projectId": 10, "fileId": 100, "fileName": "root.jar", "path": "mods/root.jar", "provider": "curseforge", "required": True}]}
    saved = {}

    monkeypatch.setattr(ModrinthPackRegistry, "load", lambda _instance: {})
    monkeypatch.setattr(CurseForgePackRegistry, "load", lambda _instance: registry)
    monkeypatch.setattr(CurseForgePackRegistry, "save", lambda _instance, payload: saved.update(payload))
    monkeypatch.setattr(ModProvenanceRegistry, "synchronize", lambda _instance: {})
    monkeypatch.setattr(CurseForgeClient, "get_files_batch", lambda _file_ids: {100: root})
    monkeypatch.setattr(CurseForgeClient, "get_file", lambda project_id, file_id: root if project_id == 10 else required)
    monkeypatch.setattr(CurseForgeClient, "latest_compatible_file", lambda project_id, *_args, **_kwargs: required if project_id == 20 else pytest.fail("optional dependency must not be resolved"))
    monkeypatch.setattr(CurseForgeClient, "get_project", lambda project_id: SimpleNamespace(name="Required", project_url="https://www.curseforge.com/minecraft/mc-mods/required"))

    result = ModpackDependencyResolver.resolve(instance(tmp_path))

    assert result.added_files == ("Required",)
    added = next(entry for entry in saved["managedFiles"] if entry["projectId"] == 20)
    assert added["selectionReason"] == "required_dependency"
    assert added["requiredBy"] == ["root.jar"]


def test_pack_pinned_system_requirement_mismatch_is_warning(tmp_path):
    mod = ModInfo(
        path=tmp_path / "jei.jar",
        file_name="jei.jar",
        enabled=True,
        mod_id="jei",
        name="Just Enough Items",
        version="19.0.0",
        loader="neoforge",
        dependencies={"minecraft": "[1.21, 1.21.1)"},
        managed_by_modpack=True,
    )

    report = ModCompatibilityManager.scan(instance(tmp_path), mods=[mod])

    assert report.error_count == 0
    assert report.warning_count == 1
    assert report.issues[0].code == "pack-pinned-system-requirement"


def test_required_dependency_errors_cannot_be_bypassed_for_managed_pack(tmp_path, monkeypatch):
    managed_instance = instance(tmp_path)
    monkeypatch.setattr(ModrinthPackRegistry, "load", lambda _instance: {"managedFiles": [{"path": "mods/root.jar"}]})
    monkeypatch.setattr(CurseForgePackRegistry, "load", lambda _instance: {})
    issue = ModIssue("error", "dependency-missing", "FancyMenu requires missing dependency 'konkrete'.", ("fancymenu", "konkrete"))
    monkeypatch.setattr(ModCompatibilityManager, "scan", lambda _instance: ModHealthReport((issue,), 1, 0))

    with pytest.raises(RequiredModDependenciesMissing, match="konkrete"):
        ModpackDependencyResolver.raise_for_required_dependencies(managed_instance)


def test_jar_audit_searches_curseforge_for_kotlinforforge(tmp_path, monkeypatch):
    from pathlib import Path
    import zipfile

    from src.models.curseforge.project import CurseForgeProject

    managed_instance = instance(tmp_path, loader="forge")
    managed_instance.version_id = "1.19.2"
    managed_instance.mod_loader = ("forge", "43.4.0")
    mods = Path(managed_instance.instance_dir) / "mods"
    mods.mkdir(parents=True)
    metadata = (
        'modLoader="javafml"\n'
        'loaderVersion="[43,)"\n'
        'license="MIT"\n\n'
        '[[mods]]\n'
        'modId="sliceanddice"\n'
        'version="2.3.0"\n'
        'displayName="Create Slice & Dice"\n\n'
        '[[dependencies.sliceanddice]]\n'
        'modId="kotlinforforge"\n'
        'mandatory=true\n'
        'versionRange="[3.9.1,)"\n'
        'ordering="NONE"\n'
        'side="BOTH"\n'
    )
    with zipfile.ZipFile(mods / "sliceanddice.jar", "w") as archive:
        archive.writestr("META-INF/mods.toml", metadata)

    root = cf_file(10, 100, "sliceanddice.jar")
    root = CurseForgeFile(
        file_id=root.file_id,
        project_id=root.project_id,
        display_name=root.display_name,
        file_name=root.file_name,
        release_type=root.release_type,
        file_date=root.file_date,
        file_length=(mods / "sliceanddice.jar").stat().st_size,
        download_url=root.download_url,
        sha1="a" * 40,
        game_versions=("1.19.2",),
        dependencies=(),
        loaders=("forge",),
    )
    CurseForgePackRegistry.save(Path(managed_instance.instance_dir), {
        "managedFiles": [{
            "projectId": 10,
            "fileId": 100,
            "fileName": "sliceanddice.jar",
            "path": "mods/sliceanddice.jar",
            "provider": "curseforge",
            "required": True,
            "dependencyMetadataResolved": True,
            "dependencies": [],
            "declaredLoaders": ["forge"],
            "gameVersions": ["1.19.2"],
        }],
    })

    project = CurseForgeProject(
        project_id=351264,
        name="Kotlin for Forge",
        slug="kotlin-for-forge",
        summary="Kotlin language provider",
        download_count=1,
        authors=("thedarkcolour",),
        logo_url="",
        class_id=6,
        date_modified="2026-01-01T00:00:00Z",
        project_url="https://www.curseforge.com/minecraft/mc-mods/kotlin-for-forge",
        game_versions=("1.19.2",),
        loaders=("forge",),
    )
    kff = CurseForgeFile(
        file_id=5000,
        project_id=351264,
        display_name="Kotlin for Forge 3.12.0",
        file_name="kotlinforforge-3.12.0-all.jar",
        release_type="release",
        file_date="2026-01-01T00:00:00Z",
        file_length=100,
        download_url="https://edge.forgecdn.net/files/5000/kotlinforforge-3.12.0-all.jar",
        sha1="b" * 40,
        game_versions=("1.19.2",),
        dependencies=(),
        loaders=("forge",),
    )

    monkeypatch.setattr(ModProvenanceRegistry, "synchronize", lambda _instance: {})
    monkeypatch.setattr(CurseForgeClient, "search_projects", lambda *_args, **_kwargs: SimpleNamespace(projects=(project,)))
    monkeypatch.setattr(CurseForgeClient, "latest_compatible_file", lambda *_args, **_kwargs: kff)
    monkeypatch.setattr(ModrinthClient, "search_projects", lambda *_args, **_kwargs: SimpleNamespace(projects=()))

    result = ModpackDependencyResolver.resolve(managed_instance)
    saved = CurseForgePackRegistry.load(Path(managed_instance.instance_dir))
    added = next(entry for entry in saved["managedFiles"] if entry["projectId"] == 351264)

    assert result.added_files == ("Kotlin for Forge",)
    assert added["selectionReason"] == "jar_audit_dependency"
    assert added["providesModId"] == "kotlinforforge"
    assert added["requestedVersionRanges"] == ["[3.9.1,)"]
    assert added["requiredBy"] == ["Create Slice & Dice"]
