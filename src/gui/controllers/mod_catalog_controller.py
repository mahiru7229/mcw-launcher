from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.modrinth.modrinth_client import ModrinthClient
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class ModCatalogController(BaseController):
    search_results_changed = Signal(str, object)
    search_failed = Signal(str, str)
    versions_changed = Signal(str, str, list)
    versions_failed = Signal(str, str, str)

    SEARCH_PREFIX = "mod_catalog.search."
    VERSIONS_PREFIX = "mod_catalog.versions."

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def search(self, query: str, index: str, offset: int, loader: str = ModLoaderManager.FABRIC) -> None:
        normalized_loader = self._normalize_loader(loader)
        task_id = f"{self.SEARCH_PREFIX}{normalized_loader}"
        self._task_runner.run(
            task_id,
            lambda: (
                normalized_loader,
                ModrinthClient.search_projects(
                    project_type="mod",
                    query=query,
                    loader=normalized_loader,
                    index=index,
                    offset=offset,
                    limit=25,
                    force_refresh=True,
                ),
            ),
            f"Searching Modrinth mods for {normalized_loader.title()}...",
            blocking=False,
        )

    def load_versions(self, project_id: str, loader: str = ModLoaderManager.FABRIC) -> None:
        normalized_loader = self._normalize_loader(loader)
        task_id = f"{self.VERSIONS_PREFIX}{normalized_loader}.{project_id}"
        self._task_runner.run(
            task_id,
            lambda: (
                project_id,
                normalized_loader,
                ModrinthClient.list_project_versions(
                    project_id,
                    loader=normalized_loader,
                    version_types=("release", "beta", "alpha"),
                ),
            ),
            f"Loading {normalized_loader.title()} mod versions...",
            blocking=False,
        )

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id.startswith(self.SEARCH_PREFIX):
            if not isinstance(result, tuple) or len(result) != 2:
                self._emit_error("Modrinth mod catalog", "Modrinth search returned an invalid result.")
                return
            loader, search_result = result
            self.search_results_changed.emit(str(loader), search_result)
            return

        if task_id.startswith(self.VERSIONS_PREFIX):
            if not isinstance(result, tuple) or len(result) != 3:
                self._emit_error("Modrinth mod catalog", "Modrinth versions returned an invalid result.")
                return
            project_id, loader, versions = result
            self.versions_changed.emit(str(project_id), str(loader), list(versions))

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        message = str(error) or "Modrinth request failed."
        if task_id.startswith(self.SEARCH_PREFIX):
            loader = task_id.removeprefix(self.SEARCH_PREFIX).split(".", 1)[0]
            self.search_failed.emit(loader, message)
            return

        if task_id.startswith(self.VERSIONS_PREFIX):
            remainder = task_id.removeprefix(self.VERSIONS_PREFIX)
            loader, _, project_id = remainder.partition(".")
            self.versions_failed.emit(project_id, loader, message)

    @staticmethod
    def _normalize_loader(loader: str) -> str:
        normalized = str(loader or "").strip().lower()
        if normalized not in {ModLoaderManager.FABRIC, ModLoaderManager.FORGE}:
            raise RuntimeError(f"Unsupported Modrinth loader filter: {normalized or 'unknown'}")
        return normalized
