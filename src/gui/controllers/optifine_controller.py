from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from mcw_core import get_default_core
from mcw_core.api.language.language_manager import tr
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class OptiFineController(BaseController):
    versions_ready = Signal(str, object, bool)
    state_ready = Signal(str, object)
    install_finished = Signal(object)
    repair_finished = Signal(object)
    uninstall_finished = Signal(str)
    progress = Signal(object)

    VERSION_TASK_ID = "optifine.versions"
    INSTALL_TASK_ID = "optifine.install"
    REPAIR_TASK_ID = "optifine.repair"
    UNINSTALL_TASK_ID = "optifine.uninstall"

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._core = get_default_core()
        self._version_request: tuple[str, bool] = ("", False)
        task_runner.task_succeeded.connect(self._on_succeeded)
        task_runner.task_failed.connect(self._on_failed)

    def load_versions(self, minecraft_version: str, include_preview: bool = False, force_refresh: bool = False) -> bool:
        game = str(minecraft_version or "").strip()
        self._version_request = (game, bool(include_preview))
        return self._run_network_task(
            self._task_runner,
            self.VERSION_TASK_ID,
            lambda: self._core.optifine.list_versions(game, include_preview, force_refresh),
            tr("task.optifine.load_versions", version=game or tr("common.all")),
            blocking=False,
        )

    def load_state(self, instance_name: str) -> None:
        name = str(instance_name or "").strip()
        if not name:
            return
        try:
            self.state_ready.emit(name, self._core.optifine.state(name))
        except Exception as error:
            self._emit_error(tr("optifine.title"), error)

    def install(self, instance_name: str, version: object, source_path: Path, mode: str = "auto") -> bool:
        name = str(instance_name or "").strip()
        source = Path(source_path)
        if not name:
            return False
        def task():
            return self._core.optifine.install(name, version, source, mode, self.progress.emit)
        return self._task_runner.run(self.INSTALL_TASK_ID, task, tr("task.optifine.install", name=name))

    def repair(self, instance_name: str) -> bool:
        name = str(instance_name or "").strip()
        if not name:
            return False
        return self._task_runner.run(
            self.REPAIR_TASK_ID,
            lambda: self._core.optifine.repair(name, self.progress.emit),
            tr("task.optifine.repair", name=name),
        )

    def uninstall(self, instance_name: str) -> bool:
        name = str(instance_name or "").strip()
        if not name:
            return False
        return self._task_runner.run(
            self.UNINSTALL_TASK_ID,
            lambda: {"name": name, "removed": self._core.optifine.uninstall(name)},
            tr("task.optifine.uninstall", name=name),
        )

    @Slot(str, object)
    def _on_succeeded(self, task_id: str, result: object) -> None:
        if task_id == self.VERSION_TASK_ID:
            game, previews = self._version_request
            self.versions_ready.emit(game, result, previews)
            self.status_changed.emit(tr("status.optifine.versions_loaded", count=len(result)))
        elif task_id == self.INSTALL_TASK_ID:
            self.install_finished.emit(result)
            self.status_changed.emit(tr("status.optifine.installed", name=result.instance_name))
            self.load_state(result.instance_name)
        elif task_id == self.REPAIR_TASK_ID:
            self.repair_finished.emit(result)
            self.status_changed.emit(tr("status.optifine.repaired", name=result.instance_name))
            self.load_state(result.instance_name)
        elif task_id == self.UNINSTALL_TASK_ID:
            self.uninstall_finished.emit(str(result.get("name") or ""))
            self.status_changed.emit(tr("status.optifine.uninstalled", name=result.get("name", "")))
            self.load_state(str(result.get("name") or ""))

    @Slot(str, object)
    def _on_failed(self, task_id: str, error: Exception) -> None:
        if task_id == self.VERSION_TASK_ID and self._offer_network_retry(task_id, tr("optifine.title"), error):
            return
        if task_id.startswith("optifine."):
            self._emit_error(tr("optifine.title"), error)
