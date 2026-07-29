from __future__ import annotations

from PySide6.QtCore import QObject, QRect, Signal
from PySide6.QtGui import QPixmap

from src.core.theme.theme_animation import ResolvedThemeAnimation
from src.gui.animation.animation_clock import AnimationClock


class ThemeAnimationPlayer(QObject):
    frame_changed = Signal(int)
    finished = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._clock = AnimationClock.instance()
        self._clock.tick.connect(self._on_tick)
        self._clock.mode_changed.connect(self._on_mode_changed)
        self._animation: ResolvedThemeAnimation | None = None
        self._frames: tuple[QPixmap, ...] = ()
        self._frame_index = 0
        self._started_at_ms = 0
        self._running = False

    @property
    def animation(self) -> ResolvedThemeAnimation | None:
        return self._animation

    @property
    def frame_index(self) -> int:
        return self._frame_index

    @property
    def current_frame(self) -> QPixmap:
        if not self._frames:
            return QPixmap()
        return self._frames[self._frame_index]

    @property
    def is_running(self) -> bool:
        return self._running

    def set_animation(self, animation: ResolvedThemeAnimation | None) -> bool:
        was_running = self._running
        self.stop()
        self._animation = animation
        self._frames = self._load_frames(animation)
        self._frame_index = 0
        self.frame_changed.emit(0)
        if was_running and self._frames:
            self.start()
        return bool(self._frames)

    def start(self) -> None:
        if self._running or not self._frames:
            return
        self._running = True
        self._started_at_ms = self._clock.acquire()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._clock.release()

    def reset(self) -> None:
        self._frame_index = 0
        self._started_at_ms = self._clock.now_ms()
        self.frame_changed.emit(0)

    def _on_tick(self, now_ms: int) -> None:
        animation = self._animation
        if not self._running or animation is None or not self._frames:
            return
        elapsed = max(0, int(now_ms) - self._started_at_ms)
        raw_index = elapsed // animation.definition.frame_duration_ms
        if animation.definition.loop:
            next_index = raw_index % len(self._frames)
        elif raw_index >= len(self._frames):
            next_index = len(self._frames) - 1
            self.stop()
            self.finished.emit()
        else:
            next_index = raw_index
        if next_index != self._frame_index:
            self._frame_index = int(next_index)
            self.frame_changed.emit(self._frame_index)


    def _on_mode_changed(self, mode: str) -> None:
        if str(mode) == "off" and self._frames:
            self.reset()

    @staticmethod
    def _load_frames(animation: ResolvedThemeAnimation | None) -> tuple[QPixmap, ...]:
        if animation is None:
            return ()
        sheet = QPixmap(str(animation.path))
        if sheet.isNull():
            return ()
        definition = animation.definition
        frames: list[QPixmap] = []
        for index in range(definition.frame_count):
            column = index % definition.columns
            row = index // definition.columns
            rect = QRect(
                column * definition.frame_width,
                row * definition.frame_height,
                definition.frame_width,
                definition.frame_height,
            )
            frame = sheet.copy(rect)
            if frame.isNull():
                return ()
            frames.append(frame)
        return tuple(frames)
