import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QColor, QPalette

from src.gui.dark_theme import create_forced_dark_palette
from src.gui.dark_theme_constants import DARK_INPUT, DARK_TEXT, DARK_WINDOW


def test_forced_dark_palette_uses_dark_surfaces_and_white_text() -> None:
    palette = create_forced_dark_palette()

    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled):
        assert palette.color(group, QPalette.ColorRole.Window) == QColor(DARK_WINDOW)
        assert palette.color(group, QPalette.ColorRole.Base) == QColor(DARK_INPUT)
        assert palette.color(group, QPalette.ColorRole.WindowText) == QColor(DARK_TEXT)
        assert palette.color(group, QPalette.ColorRole.Text) == QColor(DARK_TEXT)
        assert palette.color(group, QPalette.ColorRole.ButtonText) == QColor(DARK_TEXT)
        assert palette.color(group, QPalette.ColorRole.PlaceholderText) == QColor(DARK_TEXT)
