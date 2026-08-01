from __future__ import annotations

from PySide6.QtCore import QElapsedTimer, QEvent, QObject, QTimer, Qt, Signal
from PySide6.QtWidgets import QApplication


class _ApplicationVisibilityFilter(QObject):
    def __init__(self, clock: "AnimationClock") -> None:
        super().__init__(clock)
        self.clock = clock

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in {
            QEvent.Type.Show,
            QEvent.Type.Hide,
            QEvent.Type.Close,
            QEvent.Type.WindowStateChange,
            QEvent.Type.ApplicationStateChange,
        }:
            QTimer.singleShot(0, self.clock.refresh_visibility)
        return False


class AnimationClock(QObject):
    tick = Signal(int)
    mode_changed = Signal(str)

    _instance: "AnimationClock | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._clients = 0
        self._mode = "full"
        self._enabled = True
        self._pause_when_hidden = True
        self._visibility_suspended = False
        self._timeline_suspended = False
        self._paused_at_real_ms: int | None = None
        self._paused_accumulated_ms = 0
        self._elapsed = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._emit_tick)
        self._application: QApplication | None = None
        self._visibility_filter = _ApplicationVisibilityFilter(self)
        self._install_application_filter()

    @classmethod
    def instance(cls) -> "AnimationClock":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def interval_ms(self) -> int:
        return self._timer.interval()

    @property
    def is_suspended(self) -> bool:
        return not self._enabled or self._visibility_suspended

    def configure(self, mode: object, full_fps: int = 60, reduced_fps: int = 30, pause_when_hidden: bool = True) -> None:
        normalized = str(mode or "full").strip().lower()
        if normalized not in {"full", "reduced", "off"}:
            normalized = "full"
        previous_mode = self._mode
        self._mode = normalized
        fps = reduced_fps if normalized == "reduced" else full_fps
        fps = max(1, int(fps))
        self._timer.setInterval(max(1, round(1000 / fps)))
        self._enabled = normalized != "off"
        self._pause_when_hidden = bool(pause_when_hidden)
        self._install_application_filter()
        self.refresh_visibility()
        self._update_timeline_suspension()
        if normalized != previous_mode:
            self.mode_changed.emit(normalized)

    def acquire(self) -> int:
        self._clients += 1
        self._ensure_elapsed()
        self.refresh_visibility()
        self._sync_timer()
        return self.now_ms()

    def release(self) -> None:
        self._clients = max(0, self._clients - 1)
        self._sync_timer()

    def now_ms(self) -> int:
        self._ensure_elapsed()
        real_now = max(0, int(self._elapsed.elapsed()))
        current_pause = 0 if self._paused_at_real_ms is None else max(0, real_now - self._paused_at_real_ms)
        return max(0, real_now - self._paused_accumulated_ms - current_pause)

    def refresh_visibility(self) -> None:
        self._install_application_filter()
        suspended = False
        if self._pause_when_hidden and self._application is not None:
            top_levels = tuple(self._application.topLevelWidgets())
            if top_levels:
                suspended = not any(widget.isVisible() and not widget.isMinimized() for widget in top_levels)
        self._set_visibility_suspended(suspended)

    def _ensure_elapsed(self) -> None:
        if not self._elapsed.isValid():
            self._elapsed.start()

    def _install_application_filter(self) -> None:
        application = QApplication.instance()
        if application is None or application is self._application:
            return
        if self._application is not None:
            self._application.removeEventFilter(self._visibility_filter)
        application.installEventFilter(self._visibility_filter)
        self._application = application

    def _set_visibility_suspended(self, suspended: bool) -> None:
        suspended = bool(suspended)
        if suspended == self._visibility_suspended:
            self._update_timeline_suspension()
            return
        self._visibility_suspended = suspended
        self._update_timeline_suspension()

    def _update_timeline_suspension(self) -> None:
        should_suspend = not self._enabled or self._visibility_suspended
        if should_suspend != self._timeline_suspended:
            self._ensure_elapsed()
            real_now = max(0, int(self._elapsed.elapsed()))
            if should_suspend:
                self._paused_at_real_ms = real_now
            elif self._paused_at_real_ms is not None:
                self._paused_accumulated_ms += max(0, real_now - self._paused_at_real_ms)
                self._paused_at_real_ms = None
            self._timeline_suspended = should_suspend
        self._sync_timer()

    def _sync_timer(self) -> None:
        should_run = self._clients > 0 and not self._timeline_suspended
        if should_run and not self._timer.isActive():
            self._timer.start()
        elif not should_run and self._timer.isActive():
            self._timer.stop()

    def _emit_tick(self) -> None:
        self.tick.emit(self.now_ms())
