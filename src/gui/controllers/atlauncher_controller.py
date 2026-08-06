from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from mcw_core.api.atlauncher.atlauncher_client import ATLauncherClient
from mcw_core.api.atlauncher.atlauncher_pack_installer import ATLauncherPackInstaller
from mcw_core.api.language.language_manager import tr
from mcw_core.api.progress.progress_reporter import ProgressReporter
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class ATLauncherController(BaseController):
    search_results_changed = Signal(object)
    project_details_changed = Signal(str, object)
    versions_changed = Signal(str, object)
    version_details_changed = Signal(str, str, object)
    modpack_installed = Signal(object)
    cache_cleared = Signal(object)
    progress_received = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def search(self, query: str, sort: str, index: int, force_refresh: bool = False) -> bool:
        return self._run_network_task(
            self._task_runner,
            "atlauncher.search",
            lambda: ATLauncherClient.search_projects(query=query, index=index, page_size=25, sort=sort, force_refresh=force_refresh),
            tr("task.atlauncher.search"),
            blocking=False,
        )

    def load_project_details(self, safe_name: str) -> bool:
        token = str(safe_name).strip()
        return self._run_network_task(
            self._task_runner,
            f"atlauncher.details.{token}",
            lambda: (token, ATLauncherClient.get_project_details(token)),
            tr("task.atlauncher.load_details"),
            blocking=False,
        )

    def load_versions(self, safe_name: str, allowed_release_types: tuple[str, ...]) -> bool:
        token = str(safe_name).strip()
        return self._run_network_task(
            self._task_runner,
            f"atlauncher.versions.{token}",
            lambda: (token, ATLauncherClient.list_versions(token, allowed_release_types)),
            tr("task.atlauncher.load_versions"),
            blocking=False,
        )

    def load_version_details(self, safe_name: str, version_name: str) -> bool:
        token = str(safe_name).strip()
        version = str(version_name).strip()
        return self._run_network_task(
            self._task_runner,
            f"atlauncher.version.{token}.{version}",
            lambda: (token, version, ATLauncherClient.get_version(token, version)),
            tr("task.atlauncher.load_version_metadata"),
            blocking=False,
        )

    def install_modpack(self, safe_name: str, version_name: str, instance_name: str, install_optional_files: bool, allowed_release_types: tuple[str, ...], settings_override: dict | None = None) -> bool:
        reporter = ProgressReporter(self.progress_received.emit)
        return self._task_runner.run(
            "atlauncher.install.modpack",
            lambda: ATLauncherPackInstaller.install(
                safe_name,
                version_name,
                instance_name,
                install_optional_files=install_optional_files,
                allowed_release_types=allowed_release_types,
                reporter=reporter,
                settings_override=settings_override,
            ),
            tr("task.atlauncher.install_modpack", instance=instance_name),
        )

    def clear_cache(self) -> bool:
        return self._task_runner.run(
            "atlauncher.cache.clear",
            lambda: (ATLauncherClient.clear_cache(), ATLauncherClient.cache_status())[1],
            tr("task.atlauncher.clear_cache"),
            blocking=False,
        )

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == "atlauncher.search":
            self.search_results_changed.emit(result)
            return
        if task_id.startswith("atlauncher.details.") and isinstance(result, tuple) and len(result) == 2:
            self.project_details_changed.emit(str(result[0]), result[1])
            return
        if task_id.startswith("atlauncher.versions.") and isinstance(result, tuple) and len(result) == 2:
            self.versions_changed.emit(str(result[0]), result[1])
            return
        if task_id.startswith("atlauncher.version.") and isinstance(result, tuple) and len(result) == 3:
            self.version_details_changed.emit(str(result[0]), str(result[1]), result[2])
            return
        if task_id == "atlauncher.install.modpack":
            self.status_changed.emit(tr("status.atlauncher.modpack_installed"))
            self.log_created.emit("Created an instance from an ATLauncher pack")
            self.modpack_installed.emit(result)
            return
        if task_id == "atlauncher.cache.clear":
            self.status_changed.emit(tr("status.atlauncher.cache_cleared"))
            self.cache_cleared.emit(result)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if not task_id.startswith("atlauncher."):
            return
        title = tr("atlauncher.modpack.install") if task_id == "atlauncher.install.modpack" else tr("content.library.provider.atlauncher")
        if self._offer_network_retry(task_id, title, error):
            return
        self._emit_error(title, error)
