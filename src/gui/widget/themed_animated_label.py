from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from src.core.theme.theme_manager import ThemeManager, theme_manager
from src.gui.animation.theme_animation_player import ThemeAnimationPlayer


class ThemedAnimatedLabel(QLabel):
    def __init__(
        self,
        animation_key: str,
        static_asset_key: str = "",
        width: int = 24,
        height: int = 24,
        parent: QWidget | None = None,
        manager: ThemeManager | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme_manager = manager or theme_manager
        self._animation_key = str(animation_key)
        self._static_asset_key = str(static_asset_key)
        self._target_width = max(1, int(width))
        self._target_height = max(1, int(height))
        self._animation_enabled = True
        self._player = ThemeAnimationPlayer(self)
        self._player.frame_changed.connect(self._render_current_frame)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(self._target_width, self._target_height)
        self.apply_theme()

    @property
    def animation_key(self) -> str:
        return self._animation_key

    def set_theme_state(self, animation_key: str, static_asset_key: str = "") -> None:
        self._animation_key = str(animation_key)
        self._static_asset_key = str(static_asset_key)
        self.apply_theme()

    def set_animation_enabled(self, enabled: bool) -> None:
        self._animation_enabled = bool(enabled)
        if self._animation_enabled and self.isVisible() and self._player.animation is not None:
            self._player.start()
        else:
            self._player.stop()
        self._render_current_frame()

    def apply_theme(self) -> None:
        animation = self._theme_manager.resolve_animation(self._animation_key, fallback_to_default=True) if self._animation_key else None
        self._player.set_animation(animation)
        if animation is None:
            self._render_static_asset()
        else:
            self._render_current_frame()
            if self._animation_enabled and self.isVisible():
                self._player.start()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._animation_enabled and self._player.animation is not None:
            self._player.start()

    def hideEvent(self, event) -> None:
        self._player.stop()
        super().hideEvent(event)

    def _render_current_frame(self, _index: int = 0) -> None:
        frame = self._player.current_frame
        if frame.isNull():
            self._render_static_asset()
            return
        definition = self._player.animation.definition if self._player.animation is not None else None
        transformation = Qt.TransformationMode.SmoothTransformation if definition is not None and definition.filtering == "smooth" else Qt.TransformationMode.FastTransformation
        scaled = frame.scaled(
            self._target_width,
            self._target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            transformation,
        )
        self.setText("")
        self.setPixmap(scaled)

    def _render_static_asset(self) -> None:
        self._player.stop()
        path = self._theme_manager.resolve_asset(self._static_asset_key, fallback_to_default=True) if self._static_asset_key else None
        pixmap = QPixmap(str(path)) if path is not None else QPixmap()
        if pixmap.isNull():
            self.setPixmap(QPixmap())
            return
        self.setPixmap(
            pixmap.scaled(
                self._target_width,
                self._target_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
