from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QComboBox, QWidget

from src.gui.widget.adaptive_combo_box import AdaptiveComboBoxManager


def _application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_combo_resizes_to_selected_text() -> None:
    app = _application()
    parent = QWidget()
    parent.resize(800, 300)
    combo = QComboBox(parent)
    combo.addItems(["1.21", "Minecraft 1.14.2 Pre-Release 4"])
    manager = AdaptiveComboBoxManager(app)

    combo.setCurrentIndex(0)
    manager.refresh(combo)
    short_width = combo.width()
    combo.setCurrentIndex(1)
    manager.refresh(combo)

    assert combo.width() > short_width
    assert combo.view().minimumWidth() >= combo.width()


def test_combo_caps_long_text_and_sets_tooltip() -> None:
    app = _application()
    combo = QComboBox()
    combo.setProperty("mcwAdaptiveMaxWidth", 160)
    combo.addItem("A very long version label " * 20)
    manager = AdaptiveComboBoxManager(app)

    manager.refresh(combo)

    assert combo.width() == 160
    assert combo.toolTip() == combo.currentText()


def test_combo_resizes_selected_item_with_icon() -> None:
    app = _application()
    combo = QComboBox()
    icon_pixmap = QPixmap(16, 16)
    icon_pixmap.fill()
    combo.addItem(QIcon(icon_pixmap), "Minecraft 1.21")
    manager = AdaptiveComboBoxManager(app)

    manager.refresh(combo)

    expected_minimum = (
        combo.fontMetrics().horizontalAdvance(combo.currentText())
        + combo.iconSize().width()
        + 8
        + manager.TEXT_CHROME_WIDTH
    )
    assert combo.width() >= expected_minimum
