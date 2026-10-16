"""Prevent accidental value changes via mouse wheel scrolling on input widgets."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QScrollArea,
    QSlider,
    QSpinBox,
    QWidget,
)


class WheelBlockFilter(QObject):
    """Filters wheel events on input widgets so page scrolling isn't hijacked."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            # Allow mouse wheel to scroll inside open dropdown list
            if isinstance(watched, QComboBox) and watched.view() is not None and watched.view().isVisible():
                return False
            # Forward the wheel event to the nearest enclosing QScrollArea
            parent = watched.parent()
            while parent is not None:
                if isinstance(parent, QScrollArea):
                    bar = parent.verticalScrollBar()
                    if bar is not None and bar.isVisible():
                        bar.event(event)
                        return True
                    h_bar = parent.horizontalScrollBar()
                    if h_bar is not None and h_bar.isVisible():
                        h_bar.event(event)
                        return True
                parent = parent.parent()
            event.ignore()
            return True
        return super().eventFilter(watched, event)


_WHEEL_BLOCK_FILTER: WheelBlockFilter | None = None


def _get_wheel_block_filter() -> WheelBlockFilter:
    global _WHEEL_BLOCK_FILTER
    if _WHEEL_BLOCK_FILTER is None:
        from PySide6.QtCore import QCoreApplication

        app = QCoreApplication.instance()
        _WHEEL_BLOCK_FILTER = WheelBlockFilter(parent=app)
    return _WHEEL_BLOCK_FILTER


def protect_input_widget(widget: QWidget) -> None:
    """Protect a single input widget from mouse wheel changes and indent spinbox text."""
    if isinstance(widget, (QComboBox, QSpinBox, QDoubleSpinBox, QSlider)):
        filter_instance = _get_wheel_block_filter()
        widget.installEventFilter(filter_instance)
        if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            line_edit = widget.lineEdit()
            if line_edit is not None:
                line_edit.setTextMargins(10, 0, 0, 0)
                line_edit.installEventFilter(filter_instance)


def prevent_wheel_value_changes(root: QWidget) -> None:
    """Install WheelBlockFilter on all inputs inside root and indent spinbox text."""
    protect_input_widget(root)
    for widget in root.findChildren(QWidget):
        protect_input_widget(widget)
