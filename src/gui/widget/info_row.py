from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class InfoRow(QWidget):

    def __init__(self, title: str, value: str = "-") -> None:
        super().__init__()

        self.title_label = QLabel(title)
        self.value_label = QLabel(value)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)