import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QMessageBox

from src.gui.dialogs.message_box_compat import DIALOG_BACKGROUND, DIALOG_TEXT, apply_message_box_compatibility


def test_message_box_is_forced_dark_with_white_text(gui_app):
    box = QMessageBox()
    box.setText("Readable message")

    apply_message_box_compatibility(box)

    assert box.palette().color(QPalette.ColorRole.Window) == QColor(DIALOG_BACKGROUND)
    assert box.palette().color(QPalette.ColorRole.WindowText) == QColor(DIALOG_TEXT)
    assert box.palette().color(QPalette.ColorRole.Text) == QColor(DIALOG_TEXT)
    assert DIALOG_BACKGROUND in box.styleSheet()
    assert DIALOG_TEXT in box.styleSheet()
