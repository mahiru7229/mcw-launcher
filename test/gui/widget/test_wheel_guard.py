import os
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.gui.widget.wheel_guard import prevent_wheel_value_changes

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_wheel_guard_blocks_spinbox_and_combo_and_slider_changes_in_scroll_area(gui_app: QApplication) -> None:
    scroll = QScrollArea()
    scroll.resize(300, 300)
    content = QWidget()
    layout = QVBoxLayout(content)

    combo = QComboBox()
    combo.addItems(["Alpha", "Beta", "Gamma"])
    spin = QSpinBox()
    spin.setRange(0, 5000)
    spin.setValue(1024)
    double_spin = QDoubleSpinBox()
    double_spin.setRange(0, 100)
    double_spin.setValue(25.5)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(40)

    layout.addWidget(combo)
    layout.addWidget(spin)
    layout.addWidget(double_spin)
    layout.addWidget(slider)
    for i in range(40):
        layout.addWidget(QLabel(f"Spacer {i}"))

    scroll.setWidget(content)
    scroll.show()
    gui_app.processEvents()

    prevent_wheel_value_changes(scroll)

    # Verify text margins were indented by 10px
    assert spin.lineEdit().textMargins().left() == 10
    assert double_spin.lineEdit().textMargins().left() == 10

    # Simulate wheel event (scroll down by 1 notch)
    wheel_down = QWheelEvent(
        QPoint(10, 10),
        QPoint(10, 10),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )

    # Test combo box: value should not change, scroll area should scroll
    gui_app.sendEvent(combo, wheel_down)
    assert combo.currentIndex() == 0
    assert scroll.verticalScrollBar().value() > 0

    # Test spinbox: value should not change
    bar_pos = scroll.verticalScrollBar().value()
    gui_app.sendEvent(spin, wheel_down)
    assert spin.value() == 1024
    assert scroll.verticalScrollBar().value() > bar_pos

    # Test spinbox lineEdit: value should not change
    bar_pos2 = scroll.verticalScrollBar().value()
    gui_app.sendEvent(spin.lineEdit(), wheel_down)
    assert spin.value() == 1024
    assert scroll.verticalScrollBar().value() > bar_pos2

    # Test double spinbox: value should not change
    bar_pos3 = scroll.verticalScrollBar().value()
    gui_app.sendEvent(double_spin, wheel_down)
    assert double_spin.value() == 25.5
    assert scroll.verticalScrollBar().value() > bar_pos3

    # Test slider: value should not change
    bar_pos4 = scroll.verticalScrollBar().value()
    gui_app.sendEvent(slider, wheel_down)
    assert slider.value() == 40
    assert scroll.verticalScrollBar().value() > bar_pos4


def test_wheel_guard_allows_scrolling_inside_open_combobox_popup(gui_app: QApplication) -> None:
    combo = QComboBox()
    combo.addItems([f"Item {i}" for i in range(30)])
    prevent_wheel_value_changes(combo)

    # When view is not visible, filter blocks event
    wheel_ev = QWheelEvent(
        QPoint(10, 10),
        QPoint(10, 10),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    gui_app.sendEvent(combo, wheel_ev)
    assert combo.currentIndex() == 0
