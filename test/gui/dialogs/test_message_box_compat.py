import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QMessageBox

from src.gui.dialogs.message_box_compat import DIALOG_NEUTRAL_TEXT, apply_message_box_compatibility


def test_message_box_uses_neutral_text_visible_on_light_or_dark_background(gui_app):
    box = QMessageBox()
    box.setText("Readable message")

    apply_message_box_compatibility(box)

    assert box.palette().color(QPalette.ColorRole.WindowText) == QColor(DIALOG_NEUTRAL_TEXT)
    assert DIALOG_NEUTRAL_TEXT in box.styleSheet()
