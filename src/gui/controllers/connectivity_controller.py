from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr
from mcw_core.api.network.connectivity_monitor import ConnectivitySnapshot, connectivity_monitor
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskConflictPolicy, TaskRunner


class ConnectivityController(BaseController):
    connectivity_changed = Signal(bool, str)

    TASK_ID = "network.connectivity.probe"

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def probe(self, *, force: bool = False) -> bool:
        return self._task_runner.run(
            self.TASK_ID,
            lambda: connectivity_monitor.probe(force=force),
            tr("network.connectivity.checking"),
            blocking=False,
            conflict_policy=TaskConflictPolicy.REPLACE,
        )

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id != self.TASK_ID or not isinstance(result, ConnectivitySnapshot):
            return
        if result.online:
            self.log_created.emit(tr("network.connectivity.online_log", latency=f"{result.latency_ms:.0f}"))
        else:
            self.status_changed.emit(tr("network.offline.status"))
            self.log_created.emit(tr("network.offline.log"))
        self.connectivity_changed.emit(result.online, result.detail)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id != self.TASK_ID:
            return
        self.status_changed.emit(tr("network.offline.status"))
        self.log_created.emit(tr("network.offline.probe_failed_log", error=type(error).__name__))
        self.connectivity_changed.emit(False, type(error).__name__)
