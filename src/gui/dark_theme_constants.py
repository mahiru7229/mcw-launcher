from __future__ import annotations


DARK_WINDOW = "#171817"
DARK_SURFACE = "#20221f"
DARK_SURFACE_ALT = "#252823"
DARK_INPUT = "#141613"
DARK_BUTTON = "#343730"
DARK_BUTTON_HOVER = "#454940"
DARK_BUTTON_PRESSED = "#292b27"
DARK_BORDER = "#596451"
DARK_SELECTION = "#4f6d3c"
DARK_TEXT = "#ffffff"


# This block is intentionally appended after the normal launcher stylesheet.
# It is the final compatibility layer: Windows appearance settings, native Qt
# palettes, and custom theme assets must not be able to turn launcher/dialog
# text dark or restore a light native surface.
FORCED_DARK_APPLICATION_STYLE = f"""
QWidget {{
    color: {DARK_TEXT};
}}

QMainWindow,
QDialog,
QMessageBox,
QMenu,
QToolTip {{
    background-color: {DARK_SURFACE};
    color: {DARK_TEXT};
}}

QLabel,
QCheckBox,
QRadioButton,
QGroupBox,
QAbstractButton,
QPushButton,
QToolButton,
QCommandLinkButton {{
    color: {DARK_TEXT};
}}

QLabel:disabled,
QCheckBox:disabled,
QRadioButton:disabled,
QGroupBox:disabled,
QAbstractButton:disabled,
QPushButton:disabled,
QToolButton:disabled,
QCommandLinkButton:disabled {{
    color: {DARK_TEXT};
}}

QLineEdit,
QTextEdit,
QPlainTextEdit,
QSpinBox,
QDoubleSpinBox,
QComboBox,
QAbstractItemView,
QListView,
QTreeView,
QTableView,
QTableWidget {{
    background-color: {DARK_INPUT};
    color: {DARK_TEXT};
    selection-background-color: {DARK_SELECTION};
    selection-color: {DARK_TEXT};
}}

QLineEdit:disabled,
QTextEdit:disabled,
QPlainTextEdit:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled,
QComboBox:disabled,
QAbstractItemView:disabled {{
    background-color: {DARK_INPUT};
    color: {DARK_TEXT};
}}

QComboBox QAbstractItemView,
QMenu {{
    background-color: {DARK_SURFACE_ALT};
    color: {DARK_TEXT};
    selection-background-color: {DARK_SELECTION};
    selection-color: {DARK_TEXT};
}}

QMenu::item {{
    background-color: transparent;
    color: {DARK_TEXT};
    padding: 6px 18px;
}}

QMenu::item:selected {{
    background-color: {DARK_SELECTION};
    color: {DARK_TEXT};
}}

QPushButton,
QToolButton,
QDialogButtonBox QPushButton,
QMessageBox QPushButton {{
    background-color: {DARK_BUTTON};
    color: {DARK_TEXT};
    border-color: {DARK_BORDER};
}}

QPushButton:hover,
QToolButton:hover,
QDialogButtonBox QPushButton:hover,
QMessageBox QPushButton:hover {{
    background-color: {DARK_BUTTON_HOVER};
    color: {DARK_TEXT};
}}

QPushButton:pressed,
QToolButton:pressed,
QDialogButtonBox QPushButton:pressed,
QMessageBox QPushButton:pressed {{
    background-color: {DARK_BUTTON_PRESSED};
    color: {DARK_TEXT};
}}

QMessageBox QLabel,
QMessageBox QTextEdit,
QMessageBox QPlainTextEdit {{
    background-color: transparent;
    color: {DARK_TEXT};
}}

QToolTip {{
    background-color: {DARK_SURFACE_ALT};
    color: {DARK_TEXT};
    border: 2px solid {DARK_BORDER};
}}
"""
