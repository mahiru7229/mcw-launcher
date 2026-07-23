from __future__ import annotations

from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget

from src.core.language.language_manager import tr
from src.gui.config import VERSION_ID


class StartupSplash(QWidget):
    """Small startup window shown while persistent data and the main GUI are prepared."""

    MINIMUM_VISIBLE_MS = 450

    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setObjectName("StartupSplash")
        self.setFixedSize(520, 278)

        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._message_key = "startup.starting"
        self._detail_key = "startup.please_wait"
        self._failed = False

        self._build_ui()
        self._apply_palette()
        self.retranslate()
        self._center_on_primary_screen()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("StartupCard")
        outer_layout.addWidget(self.card)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(34, 30, 34, 28)
        layout.setSpacing(10)

        self.eyebrow_label = QLabel()
        self.eyebrow_label.setObjectName("StartupEyebrow")

        self.title_label = QLabel("MCW LAUNCHER")
        self.title_label.setObjectName("StartupTitle")

        self.version_label = QLabel(VERSION_ID)
        self.version_label.setObjectName("StartupVersion")

        self.status_label = QLabel()
        self.status_label.setObjectName("StartupStatus")
        self.status_label.setWordWrap(True)

        self.detail_label = QLabel()
        self.detail_label.setObjectName("StartupDetail")
        self.detail_label.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("StartupProgress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)

        layout.addWidget(self.eyebrow_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.version_label)
        layout.addSpacing(16)
        layout.addWidget(self.status_label)
        layout.addWidget(self.detail_label)
        layout.addStretch(1)
        layout.addWidget(self.progress_bar)

        self.setStyleSheet(
            """
            QWidget#StartupSplash {
                background: transparent;
            }
            QFrame#StartupCard {
                background: #20231f;
                border: 2px solid #596451;
                border-radius: 12px;
            }
            QLabel#StartupEyebrow {
                color: #9bdc64;
                font-family: "Segoe UI";
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
            }
            QLabel#StartupTitle {
                color: #f2f4ef;
                font-family: "Segoe UI";
                font-size: 30px;
                font-weight: 800;
            }
            QLabel#StartupVersion {
                color: #a8afa4;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QLabel#StartupStatus {
                color: #f2f4ef;
                font-family: "Segoe UI";
                font-size: 15px;
                font-weight: 700;
            }
            QLabel#StartupDetail {
                color: #afb6ac;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QProgressBar#StartupProgress {
                background: #111310;
                border: 1px solid #4d5549;
                border-radius: 5px;
            }
            QProgressBar#StartupProgress::chunk {
                background: #8ed35b;
                border-radius: 4px;
            }
            """
        )

    def _apply_palette(self) -> None:
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#20231f"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#f2f4ef"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#f2f4ef"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#8ed35b"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#111310"))
        self.setPalette(palette)

    def _center_on_primary_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        x = available.left() + max(0, (available.width() - self.width()) // 2)
        y = available.top() + max(0, (available.height() - self.height()) // 2)
        self.move(x, y)

    def update_progress(self, percent: int, message_key: str, detail_key: str = "startup.please_wait") -> None:
        if self._failed:
            return
        self._message_key = str(message_key)
        self._detail_key = str(detail_key)
        self.progress_bar.setValue(max(0, min(100, int(percent))))
        self.retranslate()
        app = QGuiApplication.instance()
        if app is not None:
            app.processEvents()

    def retranslate(self) -> None:
        self.eyebrow_label.setText(tr("startup.eyebrow"))
        self.status_label.setText(tr(self._message_key))
        self.detail_label.setText(tr(self._detail_key))

    def show_error(self) -> None:
        self._failed = True
        self._message_key = "startup.failed"
        self._detail_key = "startup.failed_detail"
        self.progress_bar.setValue(100)
        self.status_label.setText(tr(self._message_key))
        self.detail_label.setText(tr(self._detail_key))
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #111310; border: 1px solid #6d5656; border-radius: 5px; }"
            "QProgressBar::chunk { background: #c47a7a; border-radius: 4px; }"
        )
        app = QGuiApplication.instance()
        if app is not None:
            app.processEvents()

    def finish(self, window: QWidget) -> None:
        remaining = max(0, self.MINIMUM_VISIBLE_MS - self._elapsed.elapsed())
        QTimer.singleShot(remaining, lambda: self._complete_finish(window))

    def _complete_finish(self, window: QWidget) -> None:
        self.close()
        window.raise_()
        window.activateWindow()
