from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.language.language_manager import tr


class IssueReportDialog(QDialog):
    information_submitted = Signal(object)

    def __init__(self, context: str = "", parent=None) -> None:
        super().__init__(parent)
        self._context = str(context or "").strip()
        self._issue_url = ""
        self._bundle_path: Path | None = None
        self.setWindowTitle(tr("issue_report.title"))
        self.setMinimumSize(620, 500)
        self.setSizeGripEnabled(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        self._build_information_page()
        self._build_guidance_page()
        self._apply_initial_size()


    def _available_geometry(self):
        screen = self.screen() or QGuiApplication.primaryScreen()
        return screen.availableGeometry() if screen is not None else None

    def _apply_initial_size(self) -> None:
        available = self._available_geometry()
        width, height = 760, 600
        if available is not None:
            width = min(width, max(620, available.width() - 96))
            height = min(height, max(500, available.height() - 96))
        self.resize(width, height)

    def _editor_min_height(self, *, primary: bool = False) -> int:
        available = self._available_geometry()
        compact = available is not None and available.height() <= 800
        if primary:
            return 72 if compact else 88
        return 56 if compact else 72

    def _build_information_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        heading = QLabel(tr("issue_report.details.heading"))
        heading.setWordWrap(True)
        layout.addWidget(heading)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(tr("issue_report.details.title_placeholder"))
        self.what_happened_edit = QTextEdit()
        self.what_happened_edit.setPlaceholderText(tr("issue_report.details.what_happened_placeholder"))
        self.what_happened_edit.setMinimumHeight(self._editor_min_height(primary=True))
        self.steps_edit = QTextEdit()
        self.steps_edit.setPlaceholderText(tr("issue_report.details.steps_placeholder"))
        self.steps_edit.setMinimumHeight(self._editor_min_height())
        self.expected_edit = QTextEdit()
        self.expected_edit.setMinimumHeight(self._editor_min_height())
        self.actual_edit = QTextEdit()
        self.actual_edit.setMinimumHeight(self._editor_min_height())
        form.addRow(tr("issue_report.details.title"), self.title_edit)
        form.addRow(tr("issue_report.details.what_happened"), self.what_happened_edit)
        form.addRow(tr("issue_report.details.steps"), self.steps_edit)
        form.addRow(tr("issue_report.details.expected"), self.expected_edit)
        form.addRow(tr("issue_report.details.actual"), self.actual_edit)
        layout.addLayout(form)

        self.context_label = QLabel(tr("issue_report.details.context", context=self._context or tr("issue_report.details.context_none")))
        self.context_label.setWordWrap(True)
        layout.addWidget(self.context_label)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton(tr("common.cancel"))
        self.continue_button = QPushButton(tr("issue_report.details.continue"))
        cancel.clicked.connect(self.reject)
        self.continue_button.clicked.connect(self._submit_information)
        buttons.addWidget(cancel)
        buttons.addWidget(self.continue_button)
        layout.addLayout(buttons)
        self.stack.addWidget(page)

    def _build_guidance_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        heading = QLabel(tr("issue_report.guide.heading"))
        heading.setWordWrap(True)
        layout.addWidget(heading)

        self.bundle_label = QLabel("")
        self.bundle_label.setWordWrap(True)
        self.bundle_label.setTextInteractionFlags(self.bundle_label.textInteractionFlags())
        layout.addWidget(self.bundle_label)

        instructions = QLabel(tr("issue_report.guide.instructions"))
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview, 1)

        buttons = QHBoxLayout()
        copy_button = QPushButton(tr("issue_report.guide.copy"))
        open_folder_button = QPushButton(tr("issue_report.guide.open_folder"))
        open_github_button = QPushButton(tr("issue_report.guide.open_github"))
        close_button = QPushButton(tr("common.close"))
        copy_button.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.preview.toPlainText()))
        open_folder_button.clicked.connect(self._open_bundle_folder)
        open_github_button.clicked.connect(self._open_github)
        close_button.clicked.connect(self.accept)
        buttons.addWidget(copy_button)
        buttons.addWidget(open_folder_button)
        buttons.addStretch()
        buttons.addWidget(open_github_button)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        self.stack.addWidget(page)

    def _submit_information(self) -> None:
        title = self.title_edit.text().strip()
        what_happened = self.what_happened_edit.toPlainText().strip()
        if not title or not what_happened:
            QMessageBox.information(self, tr("issue_report.title"), tr("issue_report.details.required"))
            return
        self.continue_button.setEnabled(False)
        self.status_label.setText(tr("issue_report.details.collecting"))
        self.information_submitted.emit(self.details())


    def prefill(self, *, title: str = "", what_happened: str = "") -> None:
        if title:
            self.title_edit.setText(str(title))
        if what_happened:
            self.what_happened_edit.setPlainText(str(what_happened))

    def details(self) -> dict[str, str]:
        return {
            "title": self.title_edit.text().strip(),
            "what_happened": self.what_happened_edit.toPlainText().strip(),
            "steps": self.steps_edit.toPlainText().strip(),
            "expected": self.expected_edit.toPlainText().strip(),
            "actual": self.actual_edit.toPlainText().strip(),
            "context": self._context,
        }

    def set_collection_failed(self, message: str) -> None:
        self.continue_button.setEnabled(True)
        self.status_label.setText(tr("issue_report.details.collect_failed", error=message))

    def show_guidance(self, bundle_path: Path, issue_body: str, issue_url: str) -> None:
        self._bundle_path = Path(bundle_path)
        self._issue_url = str(issue_url)
        self.bundle_label.setText(tr("issue_report.guide.bundle", path=self._bundle_path))
        self.preview.setPlainText(issue_body)
        self.stack.setCurrentIndex(1)

    def _open_bundle_folder(self) -> None:
        if self._bundle_path is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._bundle_path.parent.resolve())))

    def _open_github(self) -> None:
        if self._issue_url:
            QDesktopServices.openUrl(QUrl(self._issue_url))
