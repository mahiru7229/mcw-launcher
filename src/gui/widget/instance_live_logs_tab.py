from __future__ import annotations

from pathlib import Path
import threading

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.diagnostics.mclogs_client import McLogsClient
from mcw_core.api.language.language_manager import tr
from src.gui.platform_open import open_local_path
from src.gui.theme.runtime import set_theme_icon
from src.models.instance.instance import Instance


class InstanceLiveLogsTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._instance: Instance | None = None
        self._log_path: Path | None = None
        self._last_read_offset = 0
        self._all_lines: list[str] = []

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1000)
        self._poll_timer.timeout.connect(self._poll_log)

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Control Bar
        control_bar = QHBoxLayout()
        control_bar.setSpacing(8)

        self.level_filter = QComboBox()
        self.level_filter.addItem(tr("live_logs.level.all"), "all")
        self.level_filter.addItem(tr("live_logs.level.warn_error"), "warn")
        self.level_filter.addItem(tr("live_logs.level.error_only"), "error")
        self.level_filter.currentIndexChanged.connect(self._apply_filter)
        control_bar.addWidget(self.level_filter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("live_logs.search_placeholder"))
        self.search_input.textChanged.connect(self._apply_filter)
        control_bar.addWidget(self.search_input, 1)

        self.auto_scroll_checkbox = QCheckBox(tr("live_logs.auto_scroll"))
        self.auto_scroll_checkbox.setChecked(True)
        control_bar.addWidget(self.auto_scroll_checkbox)

        self.copy_all_btn = set_theme_icon(QPushButton(tr("live_logs.action.copy_all")), "icon.action.clone")
        self.copy_all_btn.clicked.connect(self._copy_all)
        control_bar.addWidget(self.copy_all_btn)

        self.share_mclogs_btn = set_theme_icon(QPushButton(tr("live_logs.action.share_mclogs")), "icon.action.upload")
        self.share_mclogs_btn.clicked.connect(self._share_mclogs)
        control_bar.addWidget(self.share_mclogs_btn)

        self.open_logs_btn = set_theme_icon(QPushButton(tr("live_logs.action.open_folder")), "icon.action.folder")
        self.open_logs_btn.clicked.connect(self._open_logs_folder)
        control_bar.addWidget(self.open_logs_btn)

        self.clear_btn = QPushButton(tr("live_logs.action.clear"))
        self.clear_btn.clicked.connect(self._clear_view)
        control_bar.addWidget(self.clear_btn)

        root.addLayout(control_bar)

        # Log Text Display
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        font = QFont("Consolas" if font_exists("Consolas") else "Monospace", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.log_text.setFont(font)
        self.log_text.setStyleSheet(
            "QPlainTextEdit { background: #0b0f19; color: #d1d5db; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 6px; }"
        )
        root.addWidget(self.log_text, 1)

        # Status / Empty Label
        self.empty_label = QLabel(tr("live_logs.empty"))
        self.empty_label.setObjectName("MutedLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setVisible(False)
        root.addWidget(self.empty_label)

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._all_lines.clear()
        self._last_read_offset = 0
        self.log_text.clear()

        if instance is None:
            self._log_path = None
            self._poll_timer.stop()
            self.empty_label.setVisible(True)
            return

        instance_dir = Path(instance.instance_dir)
        # Check standard latest.log location
        self._log_path = instance_dir / "logs" / "latest.log"
        self._poll_log()
        self._poll_timer.start()

    def reload(self) -> None:
        self._last_read_offset = 0
        self._all_lines.clear()
        self.log_text.clear()
        self._poll_log()

    def _poll_log(self) -> None:
        if self._log_path is None or not self._log_path.is_file():
            if not self._all_lines:
                self.empty_label.setVisible(True)
            return

        try:
            file_size = self._log_path.stat().st_size
        except OSError:
            return

        # If file was truncated/recreated
        if file_size < self._last_read_offset:
            self._last_read_offset = 0
            self._all_lines.clear()
            self.log_text.clear()

        if file_size == self._last_read_offset:
            return

        self.empty_label.setVisible(False)
        try:
            with open(self._log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._last_read_offset)
                new_text = f.read()
                self._last_read_offset = f.tell()
        except OSError:
            return

        new_lines = new_text.splitlines()
        self._all_lines.extend(new_lines)
        self._append_filtered_lines(new_lines)

    def _apply_filter(self) -> None:
        self.log_text.clear()
        self._append_filtered_lines(self._all_lines)

    def _append_filtered_lines(self, lines: list[str]) -> None:
        filter_mode = str(self.level_filter.currentData() or "all")
        keyword = self.search_input.text().strip().lower()

        filtered = []
        for line in lines:
            lower = line.lower()
            if keyword and keyword not in lower:
                continue

            if filter_mode == "error":
                if not any(tag in line for tag in ("[ERROR]", "[FATAL]", "Exception:", "Error:")):
                    continue
            elif filter_mode == "warn":
                if not any(tag in line for tag in ("[WARN]", "[ERROR]", "[FATAL]", "Exception:", "Warning:", "Error:")):
                    continue

            filtered.append(line)

        if not filtered:
            return

        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        info_format = QTextCharFormat()
        info_format.setForeground(QColor("#d1d5db"))

        warn_format = QTextCharFormat()
        warn_format.setForeground(QColor("#f59e0b"))

        error_format = QTextCharFormat()
        error_format.setForeground(QColor("#ef4444"))

        for line in filtered:
            if any(tag in line for tag in ("[ERROR]", "[FATAL]", "Exception:", "Error:")):
                cursor.insertText(line + "\n", error_format)
            elif any(tag in line for tag in ("[WARN]", "Warning:")):
                cursor.insertText(line + "\n", warn_format)
            else:
                cursor.insertText(line + "\n", info_format)

        if self.auto_scroll_checkbox.isChecked():
            self.log_text.ensureCursorVisible()

    def _copy_all(self) -> None:
        text = self.log_text.toPlainText()
        if text:
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(text)
                QMessageBox.information(self, tr("live_logs.action.copy_all"), tr("screenshot.copied"))

    def _share_mclogs(self) -> None:
        text = "\n".join(self._all_lines) if self._all_lines else self.log_text.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, tr("live_logs.action.share_mclogs"), tr("live_logs.empty"))
            return

        self.share_mclogs_btn.setEnabled(False)
        self.share_mclogs_btn.setText(tr("live_logs.sharing"))

        def run_upload() -> None:
            try:
                result = McLogsClient.upload(text)
                url = str(result.get("url") or "")
                QTimer.singleShot(0, lambda: self._on_mclogs_success(url))
            except Exception as err:
                msg = str(err)
                QTimer.singleShot(0, lambda: self._on_mclogs_error(msg))

        threading.Thread(target=run_upload, daemon=True).start()

    def _on_mclogs_success(self, url: str) -> None:
        self.share_mclogs_btn.setEnabled(True)
        self.share_mclogs_btn.setText(tr("live_logs.action.share_mclogs"))
        if url:
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(url)
            QMessageBox.information(
                self,
                tr("live_logs.action.share_mclogs"),
                tr("live_logs.share_success", url=url),
            )

    def _on_mclogs_error(self, message: str) -> None:
        self.share_mclogs_btn.setEnabled(True)
        self.share_mclogs_btn.setText(tr("live_logs.action.share_mclogs"))
        QMessageBox.critical(self, tr("live_logs.action.share_mclogs"), message)

    def _clear_view(self) -> None:
        self.log_text.clear()

    def _open_logs_folder(self) -> None:
        if self._instance is not None:
            logs_dir = Path(self._instance.instance_dir) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            open_local_path(logs_dir)

    def retranslate_dynamic(self) -> None:
        self.search_input.setPlaceholderText(tr("live_logs.search_placeholder"))
        self.auto_scroll_checkbox.setText(tr("live_logs.auto_scroll"))
        self.copy_all_btn.setText(tr("live_logs.action.copy_all"))
        self.share_mclogs_btn.setText(tr("live_logs.action.share_mclogs"))
        self.open_logs_btn.setText(tr("live_logs.action.open_folder"))


def font_exists(family: str) -> bool:
    from PySide6.QtGui import QFontDatabase
    return family in QFontDatabase.families()
