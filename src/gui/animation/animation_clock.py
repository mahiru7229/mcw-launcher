from __future__ import annotations

from PySide6.QtCore import QElapsedTimer, QObject, QTimer, Qt, Signal


class AnimationClock(QObject):
    tick = Signal(int)

    _instance: "AnimationClock | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._clients = 0
        self._elapsed = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._emit_tick)

    @classmethod
    def instance(cls) -> "AnimationClock":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def acquire(self) -> int:
        self._clients += 1
        if not self._elapsed.isValid():
            self._elapsed.start()
        if not self._timer.isActive():
            self._timer.start()
        return self.now_ms()

    def release(self) -> None:
        self._clients = max(0, self._clients - 1)
        if self._clients == 0:
            self._timer.stop()

    def now_ms(self) -> int:
        if not self._elapsed.isValid():
            self._elapsed.start()
        return max(0, int(self._elapsed.elapsed()))

    def _emit_tick(self) -> None:
        self.tick.emit(self.now_ms())
