from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr

from mcw_core.api.ftb.ftb_client import FTBClient
from mcw_core.api.ftb.ftb_pack_installer import FTBPackInstaller
from mcw_core.api.progress.progress_reporter import ProgressReporter
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class FTBController(BaseController):
    search_results_changed = Signal(object)
    project_details_changed = Signal(int, object)
    versions_changed = Signal(int, object)
    version_details_changed = Signal(int, int, object)
    modpack_installed = Signal(object)
    cache_cleared = Signal(object)
    progress_received = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def search(self, query: str, sort: str, index: int, force_refresh: bool = False) -> bool:
        task_id = "ftb.search"
        task = lambda: FTBClient.search_projects(query=query, index=index, page_size=25, sort=sort, force_refresh=force_refresh)
        return self._run_network_task(
            self._task_runner,
            task_id,
            task,
            tr("task.ftb.search"),
            blocking=False,
        )

    def load_project_details(self, project_id: int) -> bool:
        task_id = f"ftb.details.{int(project_id)}"
        task = lambda: (int(project_id), FTBClient.get_project_details(project_id))
        return self._run_network_task(
            self._task_runner,
            task_id,
            task,
            tr("task.ftb.load_details"),
            blocking=False,
        )

    def load_versions(self, project_id: int, allowed_release_types: tuple[str, ...]) -> bool:
        task_id = f"ftb.versions.{int(project_id)}"
        task = lambda: (int(project_id), FTBClient.list_versions(project_id, allowed_release_types))
        return self._run_network_task(
            self._task_runner,
            task_id,
            task,
            tr("task.ftb.load_versions"),
            blocking=False,
        )

    def load_version_details(self, project_id: int, version_id: int) -> bool:
        task_id = f"ftb.version.{int(project_id)}.{int(version_id)}"
        task = lambda: (int(project_id), int(version_id), FTBClient.get_version(project_id, version_id))
        return self._run_network_task(
            self._task_runner,
            task_id,
            task,
            tr("task.ftb.load_version_metadata"),
            blocking=False,
        )

    def install_modpack(self, project_id: int, version_id: int, instance_name: str, install_optional_files: bool, allowed_release_types: tuple[str, ...], settings_override: dict | None = None) -> bool:
        reporter = ProgressReporter(self.progress_received.emit)
        return self._task_runner.run(
            "ftb.install.modpack",
            lambda: FTBPackInstaller.install(
                project_id,
                version_id,
                instance_name,
                install_optional_files=install_optional_files,
                allowed_release_types=allowed_release_types,
                reporter=reporter,
                settings_override=settings_override,
            ),
            tr("task.ftb.install_modpack", instance=instance_name),
        )

    def clear_api_cache(self) -> bool:
        return self._task_runner.run(
            "ftb.cache.clear",
            lambda: (FTBClient.clear_api_cache(), FTBClient.api_cache_status())[1],
            tr("task.ftb.clear_cache"),
            blocking=False,
        )

    def clear_cache(self) -> bool:
        """Compatibility alias for clearing the provider API metadata cache."""
        return self.clear_api_cache()

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == "ftb.search":
            self.search_results_changed.emit(result)
            return
        if task_id.startswith("ftb.details.") and isinstance(result, tuple) and len(result) == 2:
            self.project_details_changed.emit(int(result[0]), result[1])
            return
        if task_id.startswith("ftb.versions.") and isinstance(result, tuple) and len(result) == 2:
            self.versions_changed.emit(int(result[0]), result[1])
            return
        if task_id.startswith("ftb.version.") and isinstance(result, tuple) and len(result) == 3:
            self.version_details_changed.emit(int(result[0]), int(result[1]), result[2])
            return
        if task_id == "ftb.install.modpack":
            self.status_changed.emit(tr("status.ftb.modpack_installed"))
            self.log_created.emit("Created an instance from an FTB modpack")
            self.modpack_installed.emit(result)
            return
        if task_id == "ftb.cache.clear":
            self.status_changed.emit(tr("status.ftb.cache_cleared"))
            self.cache_cleared.emit(result)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if not task_id.startswith("ftb."):
            return
        title = tr("ftb.modpack.install") if task_id == "ftb.install.modpack" else tr("content.library.provider.ftb")
        if self._offer_network_retry(task_id, title, error):
            return
        self._emit_error(title, error)
