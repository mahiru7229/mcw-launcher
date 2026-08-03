from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from mcw_core.api.instance.instance_manager import InstanceManager
from mcw_core.api.modloader.mod_loader_manager import ModLoaderManager
from mcw_core.api.modrinth.modrinth_client import ModrinthClient
from mcw_core.api.modrinth.modrinth_errors import ModrinthModpackManualDownloadRequired
from mcw_core.api.modrinth.modrinth_manual_installer import ModrinthManualInstaller
from mcw_core.api.modrinth.modrinth_mod_installer import ModrinthModInstaller
from mcw_core.api.modrinth.modrinth_pack_installer import ModrinthPackInstaller
from mcw_core.api.progress.progress_reporter import ProgressReporter
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class ModrinthController(BaseController):
    search_results_changed = Signal(str, str, object)
    search_failed = Signal(str, str, str)
    versions_changed = Signal(str, str, str, list)
    project_details_changed = Signal(str, str, str, object)
    mod_installed = Signal(object)
    manual_files_installed = Signal(str, object)
    modpack_installed = Signal(object)
    modpack_manual_download_required = Signal(object)
    progress_received = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def search(self, project_type: str, query: str, index: str, offset: int, game_version: str = "", loader: str = ModLoaderManager.FABRIC) -> None:
        normalized_loader = self._normalize_loader(loader)
        task_id = f"modrinth.search.{project_type}.{normalized_loader}"
        self._task_runner.run(task_id, lambda: (project_type, normalized_loader, ModrinthClient.search_projects(project_type=project_type, query=query, game_version=game_version, loader=normalized_loader, index=index, offset=offset, limit=25, force_refresh=True)), f"Searching Modrinth {project_type}s for {normalized_loader.title()}...", blocking=False)

    def load_versions(self, project_type: str, project_id: str, game_version: str = "", loader: str = ModLoaderManager.FABRIC) -> None:
        normalized_loader = self._normalize_loader(loader)
        task_id = f"modrinth.versions.{project_type}.{normalized_loader}.{project_id}"
        self._task_runner.run(task_id, lambda: (project_type, project_id, normalized_loader, ModrinthClient.list_project_versions(project_id, loader=normalized_loader, game_version=game_version, version_types=("release", "beta", "alpha"))), f"Loading compatible Modrinth {normalized_loader.title()} versions...", blocking=False)

    def load_project_details(self, project_type: str, project_id: str, loader: str = ModLoaderManager.FABRIC) -> None:
        normalized_loader = self._normalize_loader(loader)
        task_id = f"modrinth.details.{project_type}.{normalized_loader}.{project_id}"
        self._task_runner.run(task_id, lambda: (project_type, project_id, normalized_loader, ModrinthClient.get_project(project_id)), "Loading Modrinth project details...", blocking=False)

    def install_mod(self, instance_name: str, version_id: str, allowed_version_types: tuple[str, ...] = ("release",)) -> bool:
        reporter = ProgressReporter(self.progress_received.emit)

        def task() -> object:
            instance = InstanceManager.load(instance_name)
            return ModrinthModInstaller.install(instance, version_id, install_dependencies=True, allowed_version_types=allowed_version_types, reporter=reporter)

        return self._task_runner.run("modrinth.install.mod", task, f"Installing Modrinth mod into '{instance_name}'...")

    def install_modpack(self, project_id: str, version_id: str, instance_name: str, install_optional_files: bool, allowed_version_types: tuple[str, ...] = ("release",), loader: str = ModLoaderManager.FABRIC, settings_override: dict | None = None) -> None:
        reporter = ProgressReporter(self.progress_received.emit)
        normalized_loader = self._normalize_loader(loader)
        self._task_runner.run("modrinth.install.modpack", lambda: ModrinthPackInstaller.install(project_id, version_id, instance_name, install_optional_files, allowed_version_types, reporter, expected_loader=normalized_loader, settings_override=settings_override), f"Installing Modrinth {normalized_loader.title()} modpack '{instance_name}'...")

    def install_manual_files(self, instance_name: str, requirements: tuple[object, ...] | list[object], sources: tuple[Path, ...] | list[Path]) -> bool:
        normalized_sources = [Path(source) for source in sources]
        if not normalized_sources:
            return False
        return self._task_runner.run(
            "modrinth.install.manual.batch",
            lambda: (instance_name, ModrinthManualInstaller.install_many(InstanceManager.load(instance_name), requirements, normalized_sources)),
            f"Adding {len(normalized_sources)} downloaded Modrinth file(s) to '{instance_name}'...",
        )

    def install_manual_modpack(self, request: ModrinthModpackManualDownloadRequired, source: Path) -> bool:
        reporter = ProgressReporter(self.progress_received.emit)
        return self._task_runner.run(
            "modrinth.install.modpack.manual",
            lambda: ModrinthPackInstaller.install_manual_archive(request, Path(source), reporter=reporter),
            f"Installing downloaded Modrinth modpack '{request.instance_name}'...",
        )

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id.startswith("modrinth.search."):
            if not isinstance(result, tuple) or len(result) != 3:
                self._emit_error("Modrinth", "Modrinth search returned an invalid result.")
                return
            project_type, loader, search_result = result
            self.search_results_changed.emit(str(project_type), str(loader), search_result)
            return
        if task_id.startswith("modrinth.versions."):
            if not isinstance(result, tuple) or len(result) != 4:
                self._emit_error("Modrinth", "Modrinth versions returned an invalid result.")
                return
            project_type, project_id, loader, versions = result
            self.versions_changed.emit(str(project_type), str(project_id), str(loader), list(versions))
            return
        if task_id.startswith("modrinth.details."):
            if not isinstance(result, tuple) or len(result) != 4:
                self._emit_error("Modrinth", "Modrinth project details returned an invalid result.")
                return
            project_type, project_id, loader, project = result
            self.project_details_changed.emit(str(project_type), str(project_id), str(loader), project)
            return
        if task_id == "modrinth.install.mod":
            self.status_changed.emit("Modrinth mod installed")
            self.log_created.emit("Installed Modrinth mod and required dependencies")
            self.mod_installed.emit(result)
            return
        if task_id == "modrinth.install.modpack":
            self.status_changed.emit("Modrinth modpack installed")
            self.log_created.emit("Created instance from Modrinth modpack")
            self.modpack_installed.emit(result)
            return
        if task_id == "modrinth.install.manual.batch":
            instance_name, import_result = result
            self.manual_files_installed.emit(str(instance_name), import_result)
            return
        if task_id == "modrinth.install.modpack.manual":
            self.status_changed.emit("Modrinth modpack installed")
            self.modpack_installed.emit(result)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if not task_id.startswith("modrinth."):
            return
        if task_id.startswith("modrinth.details."):
            self.log_created.emit(f"Could not load Modrinth project details: {error}")
            return
        if task_id.startswith("modrinth.search."):
            parts = task_id.split(".")
            project_type = parts[2] if len(parts) > 2 else "modpack"
            loader = parts[3] if len(parts) > 3 else ModLoaderManager.FABRIC
            message = str(error) or "Modrinth search failed."
            self.search_failed.emit(project_type, loader, message)
        if isinstance(error, ModrinthModpackManualDownloadRequired):
            self.modpack_manual_download_required.emit(error)
            return
        if task_id == "modrinth.install.mod":
            title = "Install Modrinth mod"
        elif task_id == "modrinth.install.modpack":
            title = "Install Modrinth modpack"
        else:
            title = "Modrinth"
        self._emit_error(title, error)

    @staticmethod
    def _normalize_loader(loader: str) -> str:
        normalized = str(loader or "").strip().lower()
        if normalized not in ModLoaderManager.MODDED_LOADERS:
            raise RuntimeError(f"Unsupported Modrinth loader filter: {normalized or 'unknown'}")
        return normalized
