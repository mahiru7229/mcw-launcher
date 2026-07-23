from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QAbstractButton, QApplication, QLabel, QMessageBox, QTextEdit


# #767676 keeps readable contrast against both pure white and pure black.
# This is intentional: a few Windows/driver combinations may ignore either
# the QMessageBox background or foreground palette, but not always both.
DIALOG_NEUTRAL_TEXT = "#767676"
DIALOG_BACKGROUND = "#f1f1f1"
DIALOG_BUTTON = "#dddddd"
DIALOG_BORDER = "#767676"

MESSAGE_BOX_STYLE = f"""
QMessageBox {{
    background-color: {DIALOG_BACKGROUND};
    color: {DIALOG_NEUTRAL_TEXT};
}}

QMessageBox QLabel,
QMessageBox QTextEdit {{
    background: transparent;
    color: {DIALOG_NEUTRAL_TEXT};
    font-family: "Segoe UI";
    font-size: 10.5pt;
}}

QMessageBox QPushButton {{
    min-width: 88px;
    background: {DIALOG_BUTTON};
    color: {DIALOG_NEUTRAL_TEXT};
    border: 2px solid {DIALOG_BORDER};
    padding: 7px 12px;
    font-weight: 700;
}}

QMessageBox QPushButton:hover {{
    background: #cfcfcf;
    color: #666666;
}}

QMessageBox QPushButton:pressed {{
    background: #c2c2c2;
}}
"""


def _neutral_palette(widget: QObject) -> QPalette:
    palette = QPalette(getattr(widget, "palette")())
    background = QColor(DIALOG_BACKGROUND)
    foreground = QColor(DIALOG_NEUTRAL_TEXT)
    button = QColor(DIALOG_BUTTON)
    palette.setColor(QPalette.ColorRole.Window, background)
    palette.setColor(QPalette.ColorRole.Base, background)
    palette.setColor(QPalette.ColorRole.AlternateBase, background)
    palette.setColor(QPalette.ColorRole.WindowText, foreground)
    palette.setColor(QPalette.ColorRole.Text, foreground)
    palette.setColor(QPalette.ColorRole.PlaceholderText, foreground)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, foreground)
    palette.setColor(QPalette.ColorRole.ToolTipText, foreground)
    return palette


def apply_message_box_compatibility(message_box: QMessageBox) -> None:
    message_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    message_box.setPalette(_neutral_palette(message_box))
    message_box.setStyleSheet(MESSAGE_BOX_STYLE)

    # Apply the neutral foreground directly to native-created children too.
    # Some Windows themes ignore an inherited QMessageBox palette while still
    # respecting a child palette or child stylesheet.
    for label in message_box.findChildren(QLabel):
        label.setPalette(_neutral_palette(label))
        label.setStyleSheet(f"background: transparent; color: {DIALOG_NEUTRAL_TEXT};")
    for text_edit in message_box.findChildren(QTextEdit):
        text_edit.setPalette(_neutral_palette(text_edit))
        text_edit.setStyleSheet(f"background: {DIALOG_BACKGROUND}; color: {DIALOG_NEUTRAL_TEXT};")
    for button in message_box.findChildren(QAbstractButton):
        button.setPalette(_neutral_palette(button))
        button.setStyleSheet(
            f"background: {DIALOG_BUTTON}; color: {DIALOG_NEUTRAL_TEXT}; "
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
