from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from mcw_core.api.content.content_pack_manager import ContentPackManager
from mcw_core.api.curseforge.curseforge_client import CurseForgeClient
from mcw_core.api.instance.instance_manager import InstanceManager
from mcw_core.api.modrinth.modrinth_client import ModrinthClient
from mcw_core.api.progress.progress_reporter import ProgressReporter
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class ContentPackController(BaseController):
    search_results_changed = Signal(str, str, object)
    search_failed = Signal(str, str, str)
    versions_changed = Signal(str, str, str, list)
    files_changed = Signal(str, str, int, list)
    project_details_changed = Signal(str, str, str, object)
    installed = Signal(object)
    entries_changed = Signal(str, str, list)
    progress_received = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def search(self, provider: str, content_type: str, query: str, sort: str, offset: int, game_version: str = "") -> bool:
        source = self._provider(provider)
        kind = ContentPackManager.normalize_type(content_type)
        task_id = f"content.search.{source}.{kind}"
        if source == "modrinth":
            task = lambda: (source, kind, ModrinthClient.search_projects(kind, query=query, game_version=game_version, loader="", index=sort, offset=offset, limit=25, force_refresh=True))
        else:
            task = lambda: (source, kind, CurseForgeClient.search_projects(kind, query=query, game_version=game_version, loader="", sort=sort, index=offset, page_size=25, force_refresh=True))
        return self._task_runner.run(task_id, task, f"Searching {source.title()} {ContentPackManager.display_name(kind)}s...", blocking=False)

    def load_project_details(self, provider: str, content_type: str, project_id: str) -> bool:
        source = self._provider(provider)
        kind = ContentPackManager.normalize_type(content_type)
        task_id = f"content.details.{source}.{kind}.{project_id}"
        if source == "modrinth":
            task = lambda: (source, kind, str(project_id), ModrinthClient.get_project(str(project_id)))
        else:
            task = lambda: (source, kind, str(project_id), CurseForgeClient.get_project_details(int(project_id)))
        return self._task_runner.run(task_id, task, "Loading project details...", blocking=False)

    def load_versions(self, provider: str, content_type: str, project_id: str, game_version: str = "", release_types: tuple[str, ...] = ("release", "beta", "alpha")) -> bool:
        source = self._provider(provider)
        kind = ContentPackManager.normalize_type(content_type)
        task_id = f"content.versions.{source}.{kind}.{project_id}"
        if source == "modrinth":
            task = lambda: (source, kind, str(project_id), ModrinthClient.list_project_versions(str(project_id), loader="", game_version=game_version, version_types=release_types))
        else:
            task = lambda: (source, kind, int(project_id), CurseForgeClient.list_files(int(project_id), game_version=game_version, loader="", release_types=release_types))
        return self._task_runner.run(task_id, task, "Loading compatible content versions...", blocking=False)

    def install_modrinth(self, instance_name: str, content_type: str, version_id: str) -> bool:
        reporter = ProgressReporter(self.progress_received.emit)
        kind = ContentPackManager.normalize_type(content_type)
        return self._task_runner.run("content.install.modrinth", lambda: ContentPackManager.install_modrinth(InstanceManager.load(instance_name), kind, version_id, reporter), f"Installing {ContentPackManager.display_name(kind)}...")

    def install_curseforge(self, instance_name: str, content_type: str, project_name: str, project_url: str, file: object) -> bool:
        reporter = ProgressReporter(self.progress_received.emit)
        kind = ContentPackManager.normalize_type(content_type)
        return self._task_runner.run("content.install.curseforge", lambda: ContentPackManager.install_curseforge(InstanceManager.load(instance_name), kind, file, project_name, project_url, reporter), f"Installing {ContentPackManager.display_name(kind)}...")

    def import_local(self, instance_name: str, content_type: str, source: Path) -> bool:
        kind = ContentPackManager.normalize_type(content_type)
        return self._task_runner.run("content.install.local", lambda: ContentPackManager.import_local(InstanceManager.load(instance_name), kind, Path(source)), f"Importing {ContentPackManager.display_name(kind)}...")

    def refresh_entries(self, instance_name: str, content_type: str) -> bool:
        kind = ContentPackManager.normalize_type(content_type)
        return self._task_runner.run(f"content.entries.{kind}", lambda: (instance_name, kind, ContentPackManager.list_entries(InstanceManager.load(instance_name), kind)), "Loading installed content...", blocking=False)

    def set_enabled(self, instance_name: str, content_type: str, entry_id: str, enabled: bool) -> bool:
        kind = ContentPackManager.normalize_type(content_type)
        return self._task_runner.run("content.toggle", lambda: (instance_name, kind, ContentPackManager.set_enabled(InstanceManager.load(instance_name), entry_id, enabled)), "Updating content pack state...")

    def remove(self, instance_name: str, content_type: str, entry_id: str) -> bool:
        kind = ContentPackManager.normalize_type(content_type)
        return self._task_runner.run("content.remove", lambda: (instance_name, kind, ContentPackManager.remove(InstanceManager.load(instance_name), entry_id)), "Removing content pack...")

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id.startswith("content.search."):
            provider, kind, payload = result
            self.search_results_changed.emit(str(provider), str(kind), payload)
            return
        if task_id.startswith("content.details."):
            provider, kind, project_id, project = result
            self.project_details_changed.emit(str(provider), str(kind), str(project_id), project)
            return
        if task_id.startswith("content.versions."):
            provider, kind, project_id, versions = result
            if str(provider) == "modrinth":
                self.versions_changed.emit(str(provider), str(kind), str(project_id), list(versions))
            else:
                self.files_changed.emit(str(provider), str(kind), int(project_id), list(versions))
            return
        if task_id.startswith("content.install."):
            self.installed.emit(result)
            self.status_changed.emit("Content pack installed")
            self.log_created.emit(f"Installed {getattr(result, 'content_type', 'content pack')}: {getattr(result, 'file_name', '')}")
            return
        if task_id.startswith("content.entries."):
            instance_name, kind, entries = result
            self.entries_changed.emit(str(instance_name), str(kind), list(entries))
            return
        if task_id in {"content.toggle", "content.remove"}:
            instance_name, kind, _entry = result
            entries = ContentPackManager.list_entries(InstanceManager.load(str(instance_name)), str(kind))
            self.entries_changed.emit(str(instance_name), str(kind), entries)
            return

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if not task_id.startswith("content."):
            return
        if task_id.startswith("content.search."):
            parts = task_id.split(".")
            provider = parts[2] if len(parts) > 2 else "modrinth"
            kind = parts[3] if len(parts) > 3 else "resourcepack"
            self.search_failed.emit(provider, kind, str(error) or "Content search failed.")
            return
        if task_id.startswith("content.details."):
            self.log_created.emit(f"Could not load content project details: {error}")
            return
        self._emit_error("Content packs", error)

    @staticmethod
    def _provider(value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized not in {"modrinth", "curseforge"}:
            raise ValueError(f"Unsupported content provider: {value or 'unknown'}")
        return normalized
