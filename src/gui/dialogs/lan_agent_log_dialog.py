from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from mcw_core.api.language.language_manager import tr
from src.gui.theme.runtime import set_theme_icon
from src.gui.window_sizing import resize_dialog_to_screen


class LanAgentLogDialog(QDialog):
    def __init__(self, log_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.log_path = Path(log_path)
        self.setObjectName("LanAgentLogDialog")
        self.setWindowTitle(tr("lan.agent.log.title"))
        self.setModal(True)
        resize_dialog_to_screen(self, 760, 540, 560, 400)

        layout = QVBoxLayout(self)
        description = QLabel(tr("lan.agent.log.description"))
        description.setWordWrap(True)
        layout.addWidget(description)

        self.path_label = QLabel(tr("lan.agent.log.path", path=str(self.log_path)))
        self.path_label.setObjectName("CardSubtitle")
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(self.path_label.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.path_label)

        self.output = QPlainTextEdit()
        self.output.setObjectName("DetailsOutput")
        self.output.setReadOnly(True)
        layout.addWidget(self.output, 1)

        buttons = QDialogButtonBox()
        self.refresh_button = set_theme_icon(QPushButton(tr("common.refresh")), "icon.action.refresh")
        self.copy_button = set_theme_icon(QPushButton(tr("logs.copy_all")), "icon.action.copy")
        self.open_file_button = set_theme_icon(QPushButton(tr("lan.agent.log.open_file")), "icon.action.folder")
        self.open_folder_button = set_theme_icon(QPushButton(tr("lan.agent.log.open_folder")), "icon.action.folder")
        close_button = buttons.addButton(QDialogButtonBox.StandardButton.Close)
        buttons.addButton(self.refresh_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.copy_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.open_file_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.open_folder_button, QDialogButtonBox.ButtonRole.ActionRole)
        layout.addWidget(buttons)

        self.refresh_button.clicked.connect(self.refresh)
        self.copy_button.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.output.toPlainText()))
        self.open_file_button.clicked.connect(self._open_file)
        self.open_folder_button.clicked.connect(self._open_folder)
        close_button.clicked.connect(self.accept)
        self.refresh()

    def refresh(self) -> None:
        exists = self.log_path.is_file()
        self.open_file_button.setEnabled(exists)
        try:
            text = self.log_path.read_text(encoding="utf-8", errors="replace") if exists else ""
        except OSError as error:
            text = tr("lan.agent.log.read_error", error=str(error))
        if not text:
            text = tr("lan.agent.log.not_found")
        self.output.setPlainText(text)
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)

    def _open_file(self) -> None:
        if not self.log_path.is_file():
            QMessageBox.information(self, tr("lan.agent.log.title"), tr("lan.agent.log.not_found"))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.log_path.resolve())))

    def _open_folder(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.log_path.parent.resolve())))
