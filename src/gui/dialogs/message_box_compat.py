from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QAbstractButton, QApplication, QLabel, QMessageBox, QPlainTextEdit, QTextEdit

from src.gui.dark_theme import create_forced_dark_palette
from src.gui.dark_theme_constants import (
    DARK_BORDER,
    DARK_BUTTON,
    DARK_BUTTON_HOVER,
    DARK_BUTTON_PRESSED,
    DARK_INPUT,
    DARK_SURFACE,
    DARK_TEXT,
)


DIALOG_TEXT = DARK_TEXT
# Kept as an alias so older imports and downstream tests do not break.
DIALOG_NEUTRAL_TEXT = DIALOG_TEXT
DIALOG_BACKGROUND = DARK_SURFACE
DIALOG_BUTTON = DARK_BUTTON
DIALOG_BORDER = DARK_BORDER

MESSAGE_BOX_STYLE = f"""
QMessageBox {{
    background-color: {DIALOG_BACKGROUND};
    color: {DIALOG_TEXT};
}}

QMessageBox QLabel {{
    background: transparent;
    color: {DIALOG_TEXT};
    font-family: "Segoe UI";
    font-size: 10.5pt;
}}

QMessageBox QTextEdit,
QMessageBox QPlainTextEdit {{
    background: {DARK_INPUT};
    color: {DIALOG_TEXT};
    border: 2px solid {DIALOG_BORDER};
    font-family: "Segoe UI";
    font-size: 10.5pt;
}}

QMessageBox QPushButton {{
    min-width: 88px;
    background: {DIALOG_BUTTON};
    color: {DIALOG_TEXT};
    border: 2px solid {DIALOG_BORDER};
    padding: 7px 12px;
    font-weight: 700;
}}

QMessageBox QPushButton:hover {{
    background: {DARK_BUTTON_HOVER};
    color: {DIALOG_TEXT};
}}

QMessageBox QPushButton:pressed {{
    background: {DARK_BUTTON_PRESSED};
    color: {DIALOG_TEXT};
}}
"""


def _force_dark_palette(widget: QObject):
    palette = create_forced_dark_palette(getattr(widget, "palette")())

    # QMessageBox uses a slightly lighter surface than the main window.
    # Set the palette role explicitly as well as QSS because some Qt/Windows
    # styles read QPalette.Window directly when creating child controls.
    dialog_background = QColor(DIALOG_BACKGROUND)
    for color_group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        palette.setColor(color_group, QPalette.ColorRole.Window, dialog_background)
    return palette


def apply_message_box_compatibility(message_box: QMessageBox) -> None:
    message_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    message_box_options = getattr(QMessageBox, "Option", None)
    dont_use_native = getattr(message_box_options, "DontUseNativeDialog", None)
    if dont_use_native is not None:
        message_box.setOption(dont_use_native, True)

    message_box.setPalette(_force_dark_palette(message_box))
    message_box.setStyleSheet(MESSAGE_BOX_STYLE)

    # Apply foreground/background directly to children created by QMessageBox.
    # This protects against Windows styles that partially ignore inherited QSS.
    for label in message_box.findChildren(QLabel):
        label.setPalette(_force_dark_palette(label))
        label.setStyleSheet(f"background: transparent; color: {DIALOG_TEXT};")
    for text_edit in [*message_box.findChildren(QTextEdit), *message_box.findChildren(QPlainTextEdit)]:
        text_edit.setPalette(_force_dark_palette(text_edit))
        text_edit.setStyleSheet(
            f"background: {DARK_INPUT}; color: {DIALOG_TEXT}; "
            f"border: 2px solid {DIALOG_BORDER};"
        )
    for button in message_box.findChildren(QAbstractButton):
        button.setPalette(_force_dark_palette(button))
        button.setStyleSheet(
            f"background: {DIALOG_BUTTON}; color: {DIALOG_TEXT}; "
            f"border: 2px solid {DIALOG_BORDER}; padding: 7px 12px; font-weight: 700;"
        )


class MessageBoxCompatibilityFilter(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Show and isinstance(watched, QMessageBox):
            apply_message_box_compatibility(watched)
        return super().eventFilter(watched, event)


def install_message_box_compatibility(application: QApplication) -> MessageBoxCompatibilityFilter:
    compatibility_filter = MessageBoxCompatibilityFilter(application)
    application.installEventFilter(compatibility_filter)
    return compatibility_filter
