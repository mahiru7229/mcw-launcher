from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr
from mcw_core import get_default_core, is_download_cancelled
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class JavaController(BaseController):
    installations_changed = Signal(list)
    latest_release_changed = Signal(int)
    latest_release_failed = Signal(str)
    installation_finished = Signal(int, object)
    installation_cancelled = Signal(int)
    installation_failed = Signal(int, str)
    progress_received = Signal(object)

    SCAN_TASK_ID = "java.scan"
    LATEST_RELEASE_TASK_ID = "java.latest_release"
    INSTALL_TASK_PREFIX = "java.install."

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._core = get_default_core()
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def scan(self) -> None:
        self._task_runner.run(self.SCAN_TASK_ID, lambda: self._core.java.scan(self.progress_received.emit), tr("Scanning Java installations..."), blocking=False)
        self.refresh_latest_release()

    def refresh_latest_release(self) -> None:
        self._task_runner.run(self.LATEST_RELEASE_TASK_ID, self._core.java.latest_feature_release, tr("launcher_settings.java.latest_checking"), blocking=False)

    def install(self, major: int) -> None:
        managed_major = self._core.java.normalize_feature_major(major)
        task_id = f"{self.INSTALL_TASK_PREFIX}{managed_major}"
        def task() -> Path:
            self._core.operations.begin()
            try:
                return self._core.java.install(managed_major, on_progress=self.progress_received.emit, force=True)
            finally:
                self._core.operations.finish()

        started = self._task_runner.run(task_id, task, tr("java.install.task", major=managed_major), blocking=True)
        if not started:
            self._core.operations.finish()

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == self.LATEST_RELEASE_TASK_ID:
            self.latest_release_changed.emit(self._core.java.normalize_feature_major(result))
            return
        if task_id == self.SCAN_TASK_ID:
            installations = list(result) if isinstance(result, (list, tuple)) else []
            self.installations_changed.emit(installations)
            self.log_created.emit(tr("Java scan completed: {count} installation(s)", count=len(installations)))
            return

        major = self._install_major(task_id)
        if major is None:
            return
        executable = Path(result) if isinstance(result, (str, Path)) else result
        self.installation_finished.emit(major, executable)
        self.log_created.emit(tr("java.install.completed_log", major=major, path=executable))
        self.scan()

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == self.LATEST_RELEASE_TASK_ID:
            message = str(error)
            self.latest_release_failed.emit(message)
            self.log_created.emit(tr("launcher_settings.java.latest_failed_log", error=message))
            return
        if task_id == self.SCAN_TASK_ID:
            self._emit_error(tr("Java scan"), error)
            return

        major = self._install_major(task_id)
        if major is None:
            return
        if is_download_cancelled(error):
            self.installation_cancelled.emit(major)
            self.log_created.emit(tr("java.install.cancelled_log", major=major))
            return
        self.installation_failed.emit(major, str(error))
        self._emit_error(tr("java.install.title", major=major), error)

    @classmethod
    def _install_major(cls, task_id: str) -> int | None:
        if not task_id.startswith(cls.INSTALL_TASK_PREFIX):
            return None
        try:
            return int(task_id.removeprefix(cls.INSTALL_TASK_PREFIX))
        except ValueError:
            return None
