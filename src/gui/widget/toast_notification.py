from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QParallelAnimationGroup, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.gui.animation.motion_runtime import MotionRuntime, easing_curve
from src.gui.widget.themed_animated_label import ThemedAnimatedLabel


_TOAST_ASSETS = {
    "info": ("state.ready", "icon.state.ready"),
    "success": ("state.success", "icon.state.success"),
    "warning": ("state.warning", "icon.state.warning"),
    "error": ("state.error", "icon.state.error"),
}


class ToastNotification(QFrame):
    def __init__(self, title: str, message: str, level: str, parent: QWidget) -> None:
        super().__init__(parent)
        normalized_level = str(level or "info").strip().lower()
        if normalized_level not in _TOAST_ASSETS:
            normalized_level = "info"
        self.level = normalized_level
        self.setObjectName("ToastNotification")
        self.setProperty("toastLevel", normalized_level)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(320)
        self.setMaximumWidth(440)

        animation_key, static_asset_key = _TOAST_ASSETS[normalized_level]
        self.icon = ThemedAnimatedLabel(animation_key, static_asset_key, 28, 28, self)
        self.title_label = QLabel(str(title), self)
        self.title_label.setObjectName("ToastTitle")
        self.message_label = QLabel(str(message), self)
        self.message_label.setObjectName("ToastMessage")
        self.message_label.setWordWrap(True)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)
        if str(title).strip():
            text_layout.addWidget(self.title_label)
        else:
            self.title_label.hide()
        text_layout.addWidget(self.message_label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 14, 10)
        layout.setSpacing(10)
        layout.addWidget(self.icon, 0)
        layout.addLayout(text_layout, 1)
        self.adjustSize()


class ToastManager(QObject):
    MARGIN = 18
    SPACING = 10

    def __init__(self, host: QWidget, motion_runtime: MotionRuntime, parent: QObject | None = None) -> None:
        super().__init__(parent or host)
        self.host = host
        self.motion_runtime = motion_runtime
        self._toasts: list[ToastNotification] = []
        self._animations: dict[ToastNotification, QParallelAnimationGroup] = {}
        self.host.installEventFilter(self)

    @property
    def visible_count(self) -> int:
        return len(self._toasts)

    def show(self, message: str, level: str = "info", title: str = "") -> ToastNotification:
        definition = self.motion_runtime.definition.toast
        while len(self._toasts) >= definition.max_visible:
            self.dismiss(self._toasts[0], animated=False)

        toast = ToastNotification(title, message, level, self.host)
        toast.setGraphicsEffect(QGraphicsOpacityEffect(toast))
        self._toasts.append(toast)
        self._layout_toasts()
        self._animate_in(toast)
        QTimer.singleShot(definition.visible_duration_ms, lambda current=toast: self.dismiss(current))
        return toast

    def dismiss(self, toast: ToastNotification, animated: bool = True) -> None:
        if toast not in self._toasts:
            return
        existing = self._animations.pop(toast, None)
        if existing is not None:
            existing.stop()
        definition = self.motion_runtime.definition.toast
        duration = self.motion_runtime.duration(definition.duration_ms) if animated else 0
        if duration <= 0 or definition.transition_type == "none":
            self._remove(toast)
            return

        effect = toast.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(toast)
            toast.setGraphicsEffect(effect)
        group = QParallelAnimationGroup(toast)
        if definition.transition_type in {"fade", "slide_fade"}:
            opacity = QPropertyAnimation(effect, b"opacity", group)
            opacity.setDuration(duration)
            opacity.setStartValue(effect.opacity())
            opacity.setEndValue(0.0)
            opacity.setEasingCurve(easing_curve(definition.easing))
            group.addAnimation(opacity)
        if definition.transition_type in {"slide", "slide_fade"} and definition.distance_px > 0:
            position = QPropertyAnimation(toast, b"pos", group)
            position.setDuration(duration)
            position.setStartValue(toast.pos())
            position.setEndValue(toast.pos() + QPoint(definition.distance_px, 0))
            position.setEasingCurve(easing_curve(definition.easing))
            group.addAnimation(position)
        if group.animationCount() == 0:
            self._remove(toast)
            return
        group.finished.connect(lambda current=toast: self._remove(current))
        self._animations[toast] = group
        group.start()

    def clear(self) -> None:
        for toast in tuple(self._toasts):
            self.dismiss(toast, animated=False)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.host and event.type() in {QEvent.Type.Resize, QEvent.Type.Show}:
            QTimer.singleShot(0, self._layout_toasts)
        return False

    def _animate_in(self, toast: ToastNotification) -> None:
        definition = self.motion_runtime.definition.toast
        duration = self.motion_runtime.duration(definition.duration_ms)
        effect = toast.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(toast)
            toast.setGraphicsEffect(effect)
        target = toast.pos()
        if duration <= 0 or definition.transition_type == "none":
            effect.setOpacity(1.0)
            toast.show()
            toast.raise_()
            return

        group = QParallelAnimationGroup(toast)
        if definition.transition_type in {"fade", "slide_fade"}:
            effect.setOpacity(0.0)
            opacity = QPropertyAnimation(effect, b"opacity", group)
            opacity.setDuration(duration)
            opacity.setStartValue(0.0)
            opacity.setEndValue(1.0)
            opacity.setEasingCurve(easing_curve(definition.easing))
            group.addAnimation(opacity)
        else:
            effect.setOpacity(1.0)
        if definition.transition_type in {"slide", "slide_fade"} and definition.distance_px > 0:
            start = target + QPoint(definition.distance_px, 0)
            toast.move(start)
            position = QPropertyAnimation(toast, b"pos", group)
            position.setDuration(duration)
            position.setStartValue(start)
            position.setEndValue(target)
            position.setEasingCurve(easing_curve(definition.easing))
            group.addAnimation(position)
        toast.show()
        toast.raise_()
        if group.animationCount() == 0:
            effect.setOpacity(1.0)
            toast.move(target)
            return
        group.finished.connect(lambda current=toast: self._animations.pop(current, None))
        self._animations[toast] = group
        group.start()

    def _layout_toasts(self) -> None:
        y = self.host.height() - self.MARGIN
        for toast in reversed(self._toasts):
            toast.adjustSize()
            y -= toast.height()
            toast.move(max(self.MARGIN, self.host.width() - toast.width() - self.MARGIN), max(self.MARGIN, y))
            toast.raise_()
            y -= self.SPACING

    def _remove(self, toast: ToastNotification) -> None:
        animation = self._animations.pop(toast, None)
        if animation is not None:
            animation.stop()
        if toast in self._toasts:
            self._toasts.remove(toast)
        toast.hide()
        toast.deleteLater()
        self._layout_toasts()
