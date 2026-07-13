from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget


class LaunchControlWidget(QWidget):
    launch_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self.setObjectName("LaunchControlWidget")

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 14, 20, 14)
        self.main_layout.setSpacing(16)

        self.progress_widget = QWidget()
        self.progress_layout = QVBoxLayout(self.progress_widget)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(6)

        self.status_label = QLabel("Ready")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.launch_button = QPushButton("Launch")
        self.launch_button.setFixedSize(200, 70)

        self.progress_layout.addWidget(self.status_label)
        self.progress_layout.addWidget(self.progress_bar)

        self.main_layout.addWidget(self.progress_widget, 1)
        self.main_layout.addWidget(self.launch_button)

    def _connect_signals(self) -> None:
        self.launch_button.clicked.connect(self.launch_clicked.emit)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def set_progress(self, value: int) -> None:
        value = max(0, min(value, 100))

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(value)

    def set_indeterminate(self, enabled: bool) -> None:
        if enabled:
            self.progress_bar.setRange(0, 0)
            return

        self.progress_bar.setRange(0, 100)

    def set_busy(self, busy: bool) -> None:
        self.launch_button.setEnabled(not busy)

    def reset(self) -> None:
        self.set_status("Ready")
        self.set_indeterminate(False)
        self.set_progress(0)
        self.set_busy(False)