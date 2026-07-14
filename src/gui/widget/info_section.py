from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.gui.widget.seperator import Separator


class InfoSection(QWidget):

    def __init__(self, title: str, separator_color: str = "#555555", separator_thickness: int = 1) -> None:
        super().__init__()

        self.title = title
        self.separator_color = separator_color
        self.separator_thickness = separator_thickness

        self.title_label = QLabel(self.title)
        self.main_layout = QVBoxLayout(self)

        self._build_ui()

    def _build_ui(self) -> None:
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)

        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
            }
        """)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(Separator(self.separator_color, thickness=self.separator_thickness))

    def add_row(self, row: QWidget) -> None:
        self.main_layout.addWidget(row)