from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr

from mcw_core.api.instance.instance_manager import InstanceManager
from mcw_core.api.lan.lan_hosting_manager import LanHostingManager
from mcw_core.api.progress.progress_reporter import ProgressReporter
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class LanHostingController(BaseController):
    TASK_ID = "lan.hosting.prepare"

    prepared = Signal(object)
    progress_received = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def prepare(self, instance_name: str, auth_mode: str, connection_provider: str) -> bool:
        normalized_name = str(instance_name).strip()
        if not normalized_name:
            self._emit_error("LAN hosting", "Select an instance first.")
            return False

        reporter = ProgressReporter(self.progress_received.emit)

        def task() -> object:
            instance = InstanceManager.load(normalized_name)
            return LanHostingManager.prepare(instance, auth_mode, connection_provider, reporter)

        return self._task_runner.run(
            self.TASK_ID,
            task,
            tr("task.lan.prepare", instance=normalized_name),
        )

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id != self.TASK_ID:
            return
        self.status_changed.emit(tr("lan.prepare.completed"))
        self.log_created.emit("Prepared LAN authentication and connection support")
        self.prepared.emit(result)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == self.TASK_ID:
            self._emit_error("LAN hosting", error)
