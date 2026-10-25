from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Signal, Slot

from mcw_core import get_default_core
from mcw_core.api.config.launcher_settings_manager import LauncherSettingsManager
from mcw_core.api.language.language_manager import tr
from mcw_core.api.progress.progress_reporter import ProgressReporter
from mcw_core.api.update.update_manager import UpdateManager
from src.gui.config import GITHUB_REPOSITORY, UPDATE_CHANNEL, VERSION_ID, get_active_hotfix_version
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskConflictPolicy, TaskRunner
from mcw_core.api.models.update.update_info import UpdateInfo


class UpdateController(BaseController):
    update_available = Signal(object, bool)
    no_update_available = Signal(bool)
    update_prepared = Signal(object)
    update_check_failed = Signal(object, bool)
    progress_received = Signal(object)

    AUTO_CHECK_TASK_ID = "update.check.auto"
    MANUAL_CHECK_TASK_ID = "update.check.manual"
    PREPARE_TASK_ID = "update.prepare"

    @staticmethod
    def _is_valid_update_info(result: object) -> bool:
        if isinstance(result, UpdateInfo):
            return True
        cls_obj = type(result)
        return (
            cls_obj.__name__ == "UpdateInfo"
            and getattr(cls_obj, "__module__", "") in {
                "src.models.update.update_info",
                "mcw_core.api.models.update.update_info",
            }
            and hasattr(result, "version")
            and hasattr(result, "tag_name")
            and hasattr(result, "asset")
        )

    @classmethod
    def _effective_version(cls) -> str:
        return get_active_hotfix_version() or VERSION_ID

    def __init__(self, task_runner: TaskRunner, channel: str = UPDATE_CHANNEL, source: str = "cloudflare") -> None:
        super().__init__()
        self._task_runner = task_runner
        self._channel = self._normalize_channel(channel)
        self._source = self._normalize_source(source)
        self._manager = UpdateManager(
            repository=GITHUB_REPOSITORY,
            current_version=self._effective_version(),
            channel=self._channel,
            source=self._source,
        )
        self._settings = LauncherSettingsManager()
        self._core = get_default_core()
        self._pending_update_info: UpdateInfo | None = None
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)
        self._task_runner.task_cancelled.connect(self._on_task_cancelled)
        self._task_runner.task_settled.connect(self._on_task_settled)

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def source(self) -> str:
        return self._source

    def set_channel(self, channel: str) -> None:
        normalized = self._normalize_channel(channel)
        if normalized == self._channel:
            return
        self._channel = normalized
        self._manager = UpdateManager(
            repository=GITHUB_REPOSITORY,
            current_version=self._effective_version(),
            channel=self._channel,
            source=self._source,
        )

    def set_source(self, source: str) -> None:
        normalized = self._normalize_source(source)
        if normalized == self._source:
            return
        self._source = normalized
        self._manager = UpdateManager(
            repository=GITHUB_REPOSITORY,
            current_version=self._effective_version(),
            channel=self._channel,
            source=self._source,
        )

    @staticmethod
    def _normalize_channel(channel: str) -> str:
        value = str(channel or "stable").strip().lower()
        return value if value in {"stable", "beta"} else "stable"

    @staticmethod
    def _normalize_source(source: str | None) -> str:
        value = str(source or "cloudflare").strip().lower()
        return value if value in {"cloudflare", "github", "auto"} else "cloudflare"

    def check(self, manual: bool = False) -> None:
        effective_ver = self._effective_version()
        if self._manager.current_version != effective_ver:
            self._manager = UpdateManager(
                repository=GITHUB_REPOSITORY,
                current_version=effective_ver,
                channel=self._channel,
                source=self._source,
            )
        task_id = self.MANUAL_CHECK_TASK_ID if manual else self.AUTO_CHECK_TASK_ID
        self._task_runner.run(task_id, lambda: self._manager.check_for_update(force_refresh=manual), tr("update.status.checking"), blocking=False)

    def prepare(self, info: UpdateInfo) -> bool:
        if self._pending_update_info is not None or self._task_runner.is_task_active(self.PREPARE_TASK_ID):
            return False
        self._pending_update_info = info
        cancelled = self._task_runner.begin_priority_mode("update.")
        core_cancelled = bool(self._core.operations.cancel())
        cancelled_count = len(cancelled)
        if cancelled_count or core_cancelled:
            self.status_changed.emit(tr("update.status.priority", count=cancelled_count))
            self.log_created.emit(tr("update.log.priority", count=cancelled_count))
        return self._start_pending_prepare()

    def _start_pending_prepare(self) -> bool:
        info = self._pending_update_info
        if info is None:
            return False
        active_tasks = [task_id for task_id in self._task_runner.active_task_ids if not task_id.startswith("update.")]
        if active_tasks:
            self.status_changed.emit(tr("update.status.priority_waiting", count=len(active_tasks)))
            return True

        self._pending_update_info = None
        reporter = ProgressReporter(self.progress_received.emit)
        started = self._task_runner.run(
            self.PREPARE_TASK_ID,
            lambda: self._manager.prepare_update(info, reporter),
            tr("update.status.downloading"),
            blocking=True,
            conflict_policy=TaskConflictPolicy.PARALLEL,
        )
        if not started:
            self.release_priority()
        return started

    def release_priority(self) -> None:
        self._pending_update_info = None
        self._task_runner.end_priority_mode("update.")

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id not in {self.AUTO_CHECK_TASK_ID, self.MANUAL_CHECK_TASK_ID, self.PREPARE_TASK_ID}:
            return

        if task_id == self.PREPARE_TASK_ID:
            self.status_changed.emit(tr("update.status.ready"))
            self.log_created.emit(tr("update.log.prepared"))
            self.update_prepared.emit(result)
            return

        manual = task_id == self.MANUAL_CHECK_TASK_ID
        self._settings.update_section("updates", {"last_checked_at": datetime.now(timezone.utc).isoformat()})
        if result is None:
            self.status_changed.emit(tr("update.status.latest"))
            self.no_update_available.emit(manual)
            return
        if not self._is_valid_update_info(result):
            self.update_check_failed.emit(RuntimeError("Update check returned an invalid result."), manual)
            return

        self.status_changed.emit(tr("update.status.available", version=result.version))
        self.log_created.emit(tr("update.log.available", version=result.version))
        self.update_available.emit(result, manual)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == self.PREPARE_TASK_ID:
            self.release_priority()
            self._emit_error(tr("update.error.title"), error)
            return
        if task_id not in {self.AUTO_CHECK_TASK_ID, self.MANUAL_CHECK_TASK_ID}:
            return

        manual = task_id == self.MANUAL_CHECK_TASK_ID
        self.log_created.emit(tr("update.log.check_failed", error=error))
        self.update_check_failed.emit(error, manual)

    @Slot(str)
    def _on_task_cancelled(self, task_id: str) -> None:
        if task_id == self.PREPARE_TASK_ID:
            self.release_priority()

    @Slot(str, bool, object)
    def _on_task_settled(self, task_id: str, _succeeded: bool, _payload: object) -> None:
        if self._pending_update_info is None or task_id.startswith("update."):
            return
        self._start_pending_prepare()

try:
    from PySide6.QtWidgets import QApplication

    _app = QApplication.instance()
    if _app is not None:
        for _widget in _app.topLevelWidgets():
            _ctrl = getattr(_widget, "update_controller", None)
            if _ctrl is not None and type(_ctrl).__name__ == "UpdateController" and type(_ctrl) is not UpdateController:
                _ctrl.__class__ = UpdateController
except Exception:
    pass
