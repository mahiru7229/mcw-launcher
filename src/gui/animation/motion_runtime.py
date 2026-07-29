from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPoint, QParallelAnimationGroup, QPropertyAnimation
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QDialog, QGraphicsColorizeEffect, QGraphicsOpacityEffect, QPushButton, QStackedWidget, QWidget

from src.core.theme.theme_manager import ThemeManager, theme_manager
from src.core.theme.theme_motion import MotionTransitionDefinition, ThemeMotionDefinition


class MotionMode:
    FULL = "full"
    REDUCED = "reduced"
    OFF = "off"
    VALUES = frozenset({FULL, REDUCED, OFF})

    @classmethod
    def normalize(cls, value: object) -> str:
        normalized = str(value or cls.FULL).strip().lower()
        return normalized if normalized in cls.VALUES else cls.FULL


_EASING_BY_NAME = {
    "linear": QEasingCurve.Type.Linear,
    "in_quad": QEasingCurve.Type.InQuad,
    "out_quad": QEasingCurve.Type.OutQuad,
    "in_out_quad": QEasingCurve.Type.InOutQuad,
    "in_cubic": QEasingCurve.Type.InCubic,
    "out_cubic": QEasingCurve.Type.OutCubic,
    "in_out_cubic": QEasingCurve.Type.InOutCubic,
    "out_back": QEasingCurve.Type.OutBack,
}


def easing_curve(name: str) -> QEasingCurve:
    return QEasingCurve(_EASING_BY_NAME.get(str(name).strip().lower(), QEasingCurve.Type.OutCubic))


class _MotionEventFilter(QObject):
    def __init__(self, runtime: "MotionRuntime") -> None:
        super().__init__(runtime)
        self.runtime = runtime

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QPushButton):
            self.runtime._handle_button_event(watched, event)
        if isinstance(watched, QDialog):
            return self.runtime._handle_dialog_event(watched, event)
        return False


class MotionRuntime(QObject):
    def __init__(self, manager: ThemeManager | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.manager = manager or theme_manager
        self.mode = MotionMode.FULL
        self.definition = ThemeMotionDefinition()
        self._page_animation: QParallelAnimationGroup | None = None
        self._page_cleanup = None
        self._sidebar_animation: QPropertyAnimation | None = None
        self._event_filter = _MotionEventFilter(self)
        self._installed_application: QApplication | None = None
        self._install_event_filter()

    def apply(self, mode: object = MotionMode.FULL) -> None:
        self.mode = MotionMode.normalize(mode)
        self.definition = self.manager.current.motion
        self._install_event_filter()
        if self.mode == MotionMode.OFF:
            self._stop_page_animation()
            self._reset_button_effects()

    def duration(self, duration_ms: int) -> int:
        base = max(0, int(duration_ms))
        if self.mode == MotionMode.OFF or base == 0:
            return 0
        if self.mode == MotionMode.REDUCED:
            return max(1, round(base * 0.45))
        return base

    def switch_page(self, stack: QStackedWidget, target: QWidget) -> None:
        current = stack.currentWidget()
        if current is target:
            return
        current_index = stack.indexOf(current) if current is not None else -1
        target_index = stack.indexOf(target)
        transition = self.definition.page
        duration = self.duration(transition.duration_ms)
        stack.setCurrentWidget(target)
        if duration <= 0 or transition.transition_type == "none":
            return

        self._stop_page_animation()
        group = QParallelAnimationGroup(stack)
        effect: QGraphicsOpacityEffect | None = None
        end_position = target.pos()

        if transition.transition_type in {"fade", "fade_slide"}:
            effect = QGraphicsOpacityEffect(target)
            effect.setOpacity(0.0)
            target.setGraphicsEffect(effect)
            opacity = QPropertyAnimation(effect, b"opacity", group)
            opacity.setDuration(duration)
            opacity.setStartValue(0.0)
            opacity.setEndValue(1.0)
            opacity.setEasingCurve(easing_curve(transition.easing))
            group.addAnimation(opacity)

        if transition.transition_type in {"slide_left", "slide_right", "fade_slide"} and transition.distance_px > 0:
            if transition.transition_type == "slide_left":
                direction = 1
            elif transition.transition_type == "slide_right":
                direction = -1
            else:
                direction = 1 if target_index >= current_index else -1
            start_position = QPoint(end_position.x() + transition.distance_px * direction, end_position.y())
            target.move(start_position)
            position = QPropertyAnimation(target, b"pos", group)
            position.setDuration(duration)
            position.setStartValue(start_position)
            position.setEndValue(end_position)
            position.setEasingCurve(easing_curve(transition.easing))
            group.addAnimation(position)

        cleaned = False

        def finish() -> None:
            nonlocal cleaned
            if cleaned:
                return
            cleaned = True
            target.move(end_position)
            if effect is not None and target.graphicsEffect() is effect:
                target.setGraphicsEffect(None)
            if self._page_animation is group:
                self._page_animation = None
            if self._page_cleanup is finish:
                self._page_cleanup = None

        group.finished.connect(finish)
        self._page_animation = group
        self._page_cleanup = finish
        group.start()

    def set_sidebar_collapsed(self, sidebar: QWidget, collapsed: bool, expanded_width: int) -> None:
        collapsed = bool(collapsed)
        definition = self.definition.sidebar
        target_width = definition.collapsed_width if collapsed else max(definition.collapsed_width, int(expanded_width))
        duration = self.duration(definition.duration_ms)
        if self._sidebar_animation is not None:
            self._sidebar_animation.stop()
            self._sidebar_animation = None

        set_visual = getattr(sidebar, "set_collapsed_visual", None)
        if collapsed and callable(set_visual):
            set_visual(True)
        if duration <= 0 or not hasattr(sidebar, "animatedWidth"):
            setattr(sidebar, "animatedWidth", target_width)
            if callable(set_visual):
                set_visual(collapsed)
            return

        animation = QPropertyAnimation(sidebar, b"animatedWidth", sidebar)
        animation.setDuration(duration)
        animation.setStartValue(sidebar.width())
        animation.setEndValue(target_width)
        animation.setEasingCurve(easing_curve(definition.easing))

        def finish() -> None:
            setattr(sidebar, "animatedWidth", target_width)
            if callable(set_visual):
                set_visual(collapsed)
            if self._sidebar_animation is animation:
                self._sidebar_animation = None

        animation.finished.connect(finish)
        self._sidebar_animation = animation
        animation.start()

    def animate_visibility(self, widget: QWidget, visible: bool, transition: MotionTransitionDefinition | None = None) -> None:
        visible = bool(visible)
        if bool(widget.property("motionVisibleTarget")) == visible and widget.isVisible() == visible:
            return
        widget.setProperty("motionVisibleTarget", visible)
        definition = transition or self.definition.launch_control
        duration = self.duration(definition.duration_ms)
        old_animation = getattr(widget, "_mcw_visibility_animation", None)
        if isinstance(old_animation, QPropertyAnimation):
            old_animation.stop()
        old_effect = widget.graphicsEffect()
        if isinstance(old_effect, QGraphicsOpacityEffect):
            effect = old_effect
        else:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

        if duration <= 0 or definition.transition_type == "none":
            effect.setOpacity(1.0)
            widget.setVisible(visible)
            return
        if visible:
            widget.show()
        start_opacity = effect.opacity() if widget.isVisible() else (0.0 if visible else 1.0)
        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(1.0 if visible else 0.0)
        animation.setEasingCurve(easing_curve(definition.easing))

        def finish() -> None:
            if not visible:
                widget.hide()
            effect.setOpacity(1.0)
            widget._mcw_visibility_animation = None

        animation.finished.connect(finish)
        widget._mcw_visibility_animation = animation
        animation.start()

    def pulse(self, widget: QWidget, duration_ms: int | None = None) -> None:
        duration = self.duration(duration_ms if duration_ms is not None else self.definition.launch_control.duration_ms)
        if duration <= 0:
            return
        old = getattr(widget, "_mcw_pulse_animation", None)
        if isinstance(old, QPropertyAnimation):
            old.stop()
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(duration)
        animation.setKeyValueAt(0.0, 1.0)
        animation.setKeyValueAt(0.45, 0.55 if self.mode == MotionMode.FULL else 0.75)
        animation.setKeyValueAt(1.0, 1.0)
        animation.setEasingCurve(easing_curve(self.definition.launch_control.easing))
        animation.finished.connect(lambda: effect.setOpacity(1.0))
        widget._mcw_pulse_animation = animation
        animation.start()

    def _install_event_filter(self) -> None:
        application = QApplication.instance()
        if application is None or application is self._installed_application:
            return
        if self._installed_application is not None:
            self._installed_application.removeEventFilter(self._event_filter)
        application.installEventFilter(self._event_filter)
        self._installed_application = application

    def _handle_button_event(self, button: QPushButton, event: QEvent) -> None:
        if bool(button.property("motionVisibilityOnly")):
            return
        event_type = event.type()
        if event_type not in {QEvent.Type.Enter, QEvent.Type.Leave, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.EnabledChange}:
            return
        if self.mode == MotionMode.OFF or not button.isEnabled():
            self._animate_button_strength(button, 0.0, 0)
            return
        definition = self.definition.button
        if event_type == QEvent.Type.MouseButtonPress:
            target = definition.press_strength
            duration = definition.press_duration_ms
        elif event_type == QEvent.Type.MouseButtonRelease:
            target = definition.hover_strength if button.underMouse() else 0.0
            duration = definition.press_duration_ms
        elif event_type == QEvent.Type.Enter:
            target = definition.hover_strength
            duration = definition.hover_duration_ms
        else:
            target = 0.0
            duration = definition.hover_duration_ms
        if self.mode == MotionMode.REDUCED:
            target *= 0.5
        self._animate_button_strength(button, target, self.duration(duration))

    def _animate_button_strength(self, button: QPushButton, target: float, duration: int) -> None:
        effect = getattr(button, "_mcw_button_effect", None)
        if not isinstance(effect, QGraphicsColorizeEffect):
            if button.graphicsEffect() is not None:
                return
            effect = QGraphicsColorizeEffect(button)
            effect.setColor(QColor(255, 255, 255))
            effect.setStrength(0.0)
            button.setGraphicsEffect(effect)
            button._mcw_button_effect = effect
        animation = getattr(button, "_mcw_button_animation", None)
        if isinstance(animation, QPropertyAnimation):
            animation.stop()
        if duration <= 0:
            effect.setStrength(float(target))
            return
        animation = QPropertyAnimation(effect, b"strength", button)
        animation.setDuration(duration)
        animation.setStartValue(effect.strength())
        animation.setEndValue(float(target))
        animation.setEasingCurve(easing_curve(self.definition.button.easing))
        button._mcw_button_animation = animation
        animation.start()

    def _handle_dialog_event(self, dialog: QDialog, event: QEvent) -> bool:
        definition = self.definition.dialog
        duration = self.duration(definition.duration_ms)
        if event.type() == QEvent.Type.Show:
            if duration <= 0 or definition.transition_type == "none":
                dialog.setWindowOpacity(1.0)
                return False
            animation = getattr(dialog, "_mcw_dialog_animation", None)
            if isinstance(animation, QPropertyAnimation):
                animation.stop()
            dialog.setWindowOpacity(0.0)
            animation = QPropertyAnimation(dialog, b"windowOpacity", dialog)
            animation.setDuration(duration)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(easing_curve(definition.easing))
            animation.finished.connect(lambda: dialog.setWindowOpacity(1.0))
            dialog._mcw_dialog_animation = animation
            animation.start()
        elif event.type() == QEvent.Type.Close and bool(dialog.property("motionAnimatedClose")) and duration > 0 and definition.transition_type != "none":
            if bool(dialog.property("motionCloseBypass")) or dialog.windowOpacity() <= 0.01:
                return False
            event.ignore()
            animation = getattr(dialog, "_mcw_dialog_animation", None)
            if isinstance(animation, QPropertyAnimation):
                animation.stop()
            animation = QPropertyAnimation(dialog, b"windowOpacity", dialog)
            animation.setDuration(duration)
            animation.setStartValue(dialog.windowOpacity())
            animation.setEndValue(0.0)
            animation.setEasingCurve(easing_curve(definition.easing))

            def finish_close() -> None:
                dialog.setProperty("motionCloseBypass", True)
                dialog.setWindowOpacity(1.0)
                dialog.close()
                dialog.setProperty("motionCloseBypass", False)

            animation.finished.connect(finish_close)
            dialog._mcw_dialog_animation = animation
            animation.start()
            return True
        return False

    def _reset_button_effects(self) -> None:
        application = QApplication.instance()
        if application is None:
            return
        for widget in application.allWidgets():
            if not isinstance(widget, QPushButton):
                continue
            animation = getattr(widget, "_mcw_button_animation", None)
            if isinstance(animation, QPropertyAnimation):
                animation.stop()
            effect = getattr(widget, "_mcw_button_effect", None)
            if isinstance(effect, QGraphicsColorizeEffect):
                effect.setStrength(0.0)

    def _stop_page_animation(self) -> None:
        animation = self._page_animation
        cleanup = self._page_cleanup
        self._page_animation = None
        self._page_cleanup = None
        if animation is not None:
            animation.stop()
        if callable(cleanup):
            cleanup()
