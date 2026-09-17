from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from mcw_core.api.language.language_manager import tr
from src.gui.theme.runtime import set_theme_icon
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.auth.microsoft.device_code_response import DeviceCodeResponse


class MicrosoftDeviceCodeDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("account.microsoft.device_code.title", "Microsoft Sign-in"))
        self.setModal(True)
        self._url: str = "https://www.microsoft.com/link"
        self._user_code: str = ""
        self._reset_copy_timer = QTimer(self)
        self._reset_copy_timer.setSingleShot(True)
        self._reset_copy_timer.timeout.connect(self._on_copy_timeout)
        self._build_ui()

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 480, 360, 420, 320)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        self.title_label = QLabel(tr("account.microsoft.device_code.title", "Microsoft Sign-in"))
        self.title_label.setObjectName("SectionTitle")
        root.addWidget(self.title_label)

        self.instruction_label = QLabel(
            tr(
                "account.microsoft.device_code.instructions",
                "To sign in, open the link below in your web browser and enter this code:",
            )
        )
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setObjectName("MutedLabel")
        root.addWidget(self.instruction_label)

        # Code display box
        self.code_edit = QLineEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.code_edit.font()
        font.setPointSize(22)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        self.code_edit.setFont(font)
        self.code_edit.setFixedHeight(56)
        self.code_edit.setStyleSheet("QLineEdit { letter-spacing: 4px; font-weight: bold; padding: 6px; }")
        root.addWidget(self.code_edit)

        # Action buttons row: Copy Code & Open Link
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.copy_button = set_theme_icon(
            QPushButton(tr("account.microsoft.device_code.copy", "Copy Code")),
            "icon.action.copy",
        )
        self.copy_button.setObjectName("PrimaryButton")
        self.copy_button.setFixedHeight(36)
        self.copy_button.clicked.connect(self._copy_code)
        actions_layout.addWidget(self.copy_button)

        self.open_link_button = set_theme_icon(
            QPushButton(tr("account.microsoft.device_code.open_link", "Open Link")),
            "icon.action.open",
        )
        self.open_link_button.setFixedHeight(36)
        self.open_link_button.clicked.connect(self._open_link)
        actions_layout.addWidget(self.open_link_button)

        root.addLayout(actions_layout)

        # Link URL text
        self.url_label = QLabel(f'<a href="{self._url}">{self._url}</a>')
        self.url_label.setOpenExternalLinks(True)
        self.url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.url_label)

        # Status indicator
        self.status_label = QLabel(
            tr("account.microsoft.device_code.waiting", "Waiting for you to complete sign-in in your browser...")
        )
        self.status_label.setObjectName("StatusBadge")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        root.addStretch()

        # Bottom cancel button
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.cancel_button = QPushButton(tr("account.microsoft.cancel", "Cancel"))
        self.cancel_button.setObjectName("DangerButton")
        self.cancel_button.clicked.connect(self._on_cancel)
        bottom_layout.addWidget(self.cancel_button)
        root.addLayout(bottom_layout)

    def set_data(self, response: DeviceCodeResponse) -> None:
        self._url = response.verification_uri or "https://www.microsoft.com/link"
        self._user_code = response.user_code
        self.code_edit.setText(response.user_code)
        self.url_label.setText(f'<a href="{self._url}">{self._url}</a>')

        # Auto-copy code to clipboard for convenience
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._user_code)

        # Auto-open browser
        try:
            QDesktopServices.openUrl(QUrl(self._url))
        except Exception:
            pass

    def _copy_code(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._user_code)
        self.copy_button.setText(tr("account.microsoft.device_code.copied", "Copied!"))
        self._reset_copy_timer.start(2000)

    def _on_copy_timeout(self) -> None:
        self.copy_button.setText(tr("account.microsoft.device_code.copy", "Copy Code"))

    def _open_link(self) -> None:
        try:
            QDesktopServices.openUrl(QUrl(self._url))
        except Exception:
            pass

    def _on_cancel(self) -> None:
        self.cancel_requested.emit()
        self.reject()

    def closeEvent(self, event) -> None:
        self.cancel_requested.emit()
        super().closeEvent(event)
