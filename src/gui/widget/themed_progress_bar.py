from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QProgressBar, QStyle, QStyleOptionProgressBar, QWidget

from src.core.theme.theme_manager import ThemeManager, theme_manager
from src.gui.animation.theme_animation_player import ThemeAnimationPlayer
from src.gui.theme.accent_runtime import theme_accent_runtime


class ThemedProgressBar(QProgressBar):
    DETERMINATE_ANIMATION_KEY = "progress.chunk"
    INDETERMINATE_ANIMATION_KEY = "progress.indeterminate"

    def __init__(self, parent: QWidget | None = None, manager: ThemeManager | None = None) -> None:
        super().__init__(parent)
        self._theme_manager = manager or theme_manager
        self._animation_player = ThemeAnimationPlayer(self)
        self._animation_player.frame_changed.connect(lambda _index: self.update())
        self._active_animation_key = ""
        self._fallback_pixmap = QPixmap()
        self.apply_theme()

    def apply_theme(self) -> None:
        self._refresh_animation(force=True)
        self.update()

    def setRange(self, minimum: int, maximum: int) -> None:
        super().setRange(minimum, maximum)
        if hasattr(self, "_animation_player"):
            self._refresh_animation()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._animation_player.animation is not None:
            self._animation_player.start()

    def hideEvent(self, event) -> None:
        self._animation_player.stop()
        super().hideEvent(event)

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if self.isVisible() and self._animation_player.animation is not None:
            self._animation_player.start()

    def paintEvent(self, event) -> None:
        frame = self._animation_player.current_frame
        if frame.isNull() and self._fallback_pixmap.isNull():
            super().paintEvent(event)
            return

        option = QStyleOptionProgressBar()
        self.initStyleOption(option)
        painter = QPainter(self)
        painter.setClipRect(event.rect())

        track_option = QStyleOptionProgressBar(option)
        track_option.minimum = 0
        track_option.maximum = 100
        track_option.progress = 0
        track_option.textVisible = False
        self.style().drawControl(QStyle.ControlElement.CE_ProgressBar, track_option, painter, self)

        contents = self.style().subElementRect(QStyle.SubElement.SE_ProgressBarContents, option, self)
        fill_rect = self._fill_rect(contents)
        if fill_rect.isValid() and not fill_rect.isEmpty():
            source = frame if not frame.isNull() else self._fallback_pixmap
            self._draw_asset(painter, fill_rect, source)

        if option.textVisible and option.text:
            self.style().drawControl(QStyle.ControlElement.CE_ProgressBarLabel, option, painter, self)

    def _refresh_animation(self, force: bool = False) -> None:
        key = self.INDETERMINATE_ANIMATION_KEY if self.minimum() == 0 and self.maximum() == 0 else self.DETERMINATE_ANIMATION_KEY
        if not force and key == self._active_animation_key:
            return
        self._active_animation_key = key
        animation = self._theme_manager.resolve_animation(key, fallback_to_default=True)
        self._animation_player.set_animation(animation)
        fallback = self._theme_manager.resolve_animation_fallback(key, fallback_to_default=True)
        fallback_pixmap = QPixmap(str(fallback)) if fallback is not None else QPixmap()
        self._fallback_pixmap = theme_accent_runtime.tint_pixmap(fallback_pixmap, key)
        if self.isVisible() and animation is not None:
            self._animation_player.start()

    def _fill_rect(self, contents: QRect) -> QRect:
        if self.minimum() == 0 and self.maximum() == 0:
            return QRect(contents)
        span = self.maximum() - self.minimum()
        if span <= 0:
            return QRect()
        ratio = max(0.0, min(1.0, (self.value() - self.minimum()) / span))
        width = round(contents.width() * ratio)
        if self.invertedAppearance():
            return QRect(contents.right() - width + 1, contents.top(), width, contents.height())
        return QRect(contents.left(), contents.top(), width, contents.height())

    def _draw_asset(self, painter: QPainter, target: QRect, pixmap: QPixmap) -> None:
        animation = self._animation_player.animation
        definition = animation.definition if animation is not None else None
        render_mode = definition.render_mode if definition is not None else "stretch"
        filtering = definition.filtering if definition is not None else "nearest"
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, filtering == "smooth")

        if render_mode == "tile_x":
            painter.save()
            painter.setClipRect(target)
            y = target.top() + max(0, (target.height() - pixmap.height()) // 2)
            x = target.left()
            while x <= target.right():
                painter.drawPixmap(x, y, pixmap)
                x += max(1, pixmap.width())
            painter.restore()
            return

        transformation = Qt.TransformationMode.SmoothTransformation if filtering == "smooth" else Qt.TransformationMode.FastTransformation
        if render_mode == "contain":
            scaled = pixmap.scaled(target.size(), Qt.AspectRatioMode.KeepAspectRatio, transformation)
            x = target.left() + (target.width() - scaled.width()) // 2
            y = target.top() + (target.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            return

        painter.drawPixmap(target, pixmap)
