from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr
from mcw_core.api.storage.legacy_storage_migration_service import CleanupPlan, LegacyStorageMigrationService
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class StorageController(BaseController):
    legacy_probe_ready = Signal(object)
    cleanup_plan_ready = Signal(object)
    cleanup_completed = Signal(object)

    PROBE_TASK = "storage.legacy.probe"
    SCAN_TASK = "storage.legacy.scan"
    CLEAN_TASK = "storage.legacy.clean"

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def probe(self) -> bool:
        return self._task_runner.run(self.PROBE_TASK, LegacyStorageMigrationService.probe, tr("storage.legacy.scan.task"), blocking=False)

    def scan(self) -> bool:
        return self._task_runner.run(self.SCAN_TASK, LegacyStorageMigrationService.scan, tr("storage.legacy.scan.task"), blocking=False)

    def clean(self, plan: CleanupPlan, candidate_ids: tuple[str, ...]) -> bool:
        selected = tuple(str(value) for value in candidate_ids)
        return self._task_runner.run(self.CLEAN_TASK, lambda: LegacyStorageMigrationService.apply(plan, selected), tr("storage.legacy.clean.task"), blocking=True)

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == self.PROBE_TASK:
            self.legacy_probe_ready.emit(result)
        elif task_id == self.SCAN_TASK:
            self.cleanup_plan_ready.emit(result)
        elif task_id == self.CLEAN_TASK:
            self.cleanup_completed.emit(result)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id not in {self.PROBE_TASK, self.SCAN_TASK, self.CLEAN_TASK}:
            return
        self._emit_error(tr("storage.legacy.failed.title"), error)
