from __future__ import annotations

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from src.gui.dark_theme_constants import (
    DARK_BORDER,
    DARK_BUTTON,
    DARK_INPUT,
    DARK_SELECTION,
    DARK_SURFACE,
    DARK_SURFACE_ALT,
    DARK_TEXT,
    DARK_WINDOW,
    FORCED_DARK_APPLICATION_STYLE,
)


def configure_forced_dark_attributes() -> None:
    """Disable native dialogs before QApplication exists so Qt styling always wins."""
    for attribute_name in ("AA_DontUseNativeDialogs", "AA_UseStyleSheetPropagationInWidgetStyles"):
        attribute = getattr(Qt.ApplicationAttribute, attribute_name, None)
        if attribute is not None:
            QCoreApplication.setAttribute(attribute, True)


def create_forced_dark_palette(base_palette: QPalette | None = None) -> QPalette:
    palette = QPalette(base_palette) if base_palette is not None else QPalette()

    colors = {
        QPalette.ColorRole.Window: QColor(DARK_WINDOW),
        QPalette.ColorRole.WindowText: QColor(DARK_TEXT),
        QPalette.ColorRole.Base: QColor(DARK_INPUT),
        QPalette.ColorRole.AlternateBase: QColor(DARK_SURFACE_ALT),
        QPalette.ColorRole.ToolTipBase: QColor(DARK_SURFACE_ALT),
        QPalette.ColorRole.ToolTipText: QColor(DARK_TEXT),
        QPalette.ColorRole.Text: QColor(DARK_TEXT),
        QPalette.ColorRole.Button: QColor(DARK_BUTTON),
        QPalette.ColorRole.ButtonText: QColor(DARK_TEXT),
        QPalette.ColorRole.BrightText: QColor(DARK_TEXT),
        QPalette.ColorRole.Highlight: QColor(DARK_SELECTION),
        QPalette.ColorRole.HighlightedText: QColor(DARK_TEXT),
        QPalette.ColorRole.Link: QColor(DARK_TEXT),
        QPalette.ColorRole.LinkVisited: QColor(DARK_TEXT),
        QPalette.ColorRole.PlaceholderText: QColor(DARK_TEXT),
        QPalette.ColorRole.Light: QColor(DARK_BORDER),
        QPalette.ColorRole.Midlight: QColor(DARK_SURFACE_ALT),
        QPalette.ColorRole.Mid: QColor(DARK_SURFACE),
        QPalette.ColorRole.Dark: QColor(DARK_INPUT),
        QPalette.ColorRole.Shadow: QColor("#000000"),
    }

    for role, color in colors.items():
        palette.setColor(QPalette.ColorGroup.Active, role, color)
        palette.setColor(QPalette.ColorGroup.Inactive, role, color)
        palette.setColor(QPalette.ColorGroup.Disabled, role, color)
    return palette


def apply_forced_dark_theme(application: QApplication) -> None:
    application.setStyle("Fusion")
    application.setPalette(create_forced_dark_palette(application.palette()))
    application.setStyleSheet(FORCED_DARK_APPLICATION_STYLE)
