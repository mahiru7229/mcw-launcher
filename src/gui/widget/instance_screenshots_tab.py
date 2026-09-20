from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.language.language_manager import tr
from mcw_core.api.minecraft.screenshot_manager import ScreenshotManager
from src.gui.platform_open import open_local_path
from src.gui.theme.runtime import set_theme_icon
from src.models.instance.instance import Instance
from src.models.screenshot.screenshot_info import ScreenshotInfo


class ScreenshotViewerDialog(QDialog):
    """Full-size screenshot preview modal with copy button."""

    def __init__(self, screenshot: ScreenshotInfo, parent=None) -> None:
        super().__init__(parent)
        self.screenshot = screenshot
        self.setWindowTitle(screenshot.file_name)
        self.resize(880, 560)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(str(self.screenshot.path))
        if not pix.isNull():
            self.image_label.setPixmap(pix.scaled(840, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.image_label, 1)

        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        info_text = f"{self.screenshot.file_name} ({max(1, self.screenshot.file_size_bytes // 1024)} KB)"
        self.info_label = QLabel(info_text)
        self.info_label.setObjectName("MutedLabel")
        bottom_bar.addWidget(self.info_label)
        bottom_bar.addStretch(1)

        self.copy_btn = set_theme_icon(QPushButton(tr("screenshot.action.copy")), "icon.action.clone")
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        bottom_bar.addWidget(self.copy_btn)

        self.close_btn = QPushButton(tr("common.cancel"))
        self.close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(self.close_btn)

        layout.addLayout(bottom_bar)

    def _copy_to_clipboard(self) -> None:
        pix = QPixmap(str(self.screenshot.path))
        if not pix.isNull():
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setPixmap(pix)
                QMessageBox.information(self, tr("screenshot.action.copy"), tr("screenshot.copied"))


class ScreenshotCardWidget(QFrame):
    action_completed = Signal()

    def __init__(self, screenshot: ScreenshotInfo, parent=None) -> None:
        super().__init__(parent)
        self.screenshot = screenshot
        self.setObjectName("ScreenshotCard")
        self.setStyleSheet(
            "#ScreenshotCard { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 4px; } "
            "#ScreenshotCard:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); }"
        )
        self.setFixedSize(180, 160)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(166, 95)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("border-radius: 4px; background: rgba(0, 0, 0, 0.3);")
        pix = QPixmap(str(self.screenshot.path))
        if not pix.isNull():
            self.thumb_label.setPixmap(pix.scaled(166, 95, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.thumb_label)

        # File name / date
        name = self.screenshot.file_name
        if len(name) > 22:
            name = name[:19] + "..."
        self.name_label = QLabel(name)
        self.name_label.setObjectName("TinyLabel")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self.view_btn = QPushButton(tr("screenshot.action.copy"))
        self.view_btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
        self.view_btn.clicked.connect(self._copy_image)
        btn_row.addWidget(self.view_btn, 1)

        self.del_btn = set_theme_icon(QPushButton(), "icon.action.remove")
        self.del_btn.setObjectName("DangerButton")
        self.del_btn.setToolTip(tr("screenshot.action.delete"))
        self.del_btn.setFixedSize(22, 22)
        self.del_btn.clicked.connect(self._delete_image)
        btn_row.addWidget(self.del_btn)

        layout.addLayout(btn_row)

    def mouseDoubleClickEvent(self, event) -> None:
        dialog = ScreenshotViewerDialog(self.screenshot, self.window())
        dialog.exec()

    def _copy_image(self) -> None:
        pix = QPixmap(str(self.screenshot.path))
        if not pix.isNull():
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setPixmap(pix)
                QMessageBox.information(self, tr("screenshot.action.copy"), tr("screenshot.copied"))

    def _delete_image(self) -> None:
        confirm = QMessageBox.question(
            self,
            tr("screenshot.confirm_delete.title"),
            tr("screenshot.confirm_delete.text", name=self.screenshot.file_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            ScreenshotManager.delete_screenshot(self.screenshot.path)
            self.action_completed.emit()


class InstanceScreenshotsTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._instance: Instance | None = None
        self._screenshots: list[ScreenshotInfo] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Top toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.open_folder_btn = set_theme_icon(QPushButton(tr("screenshot.action.open_folder")), "icon.action.folder")
        self.open_folder_btn.clicked.connect(self._open_folder)
        toolbar.addWidget(self.open_folder_btn)

        self.refresh_btn = set_theme_icon(QPushButton(tr("common.refresh")), "icon.action.refresh")
        self.refresh_btn.clicked.connect(self.reload)
        toolbar.addWidget(self.refresh_btn)

        toolbar.addStretch(1)
        root.addLayout(toolbar)

        # Grid container inside scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.grid_container)
        root.addWidget(self.scroll_area, 1)

        # Empty label
        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setObjectName("MutedLabel")
        self.empty_label.setText(f"{tr('screenshot.empty')}\n{tr('screenshot.empty_hint')}")
        self.empty_label.setVisible(False)
        root.addWidget(self.empty_label)

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self.reload()

    def reload(self) -> None:
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self._instance is None:
            self.empty_label.setVisible(True)
            self._screenshots = []
            return

        instance_dir = Path(getattr(self._instance, "instance_dir", ""))
        self._screenshots = ScreenshotManager.list_screenshots(instance_dir)

        if not self._screenshots:
            self.empty_label.setVisible(True)
            return

        self.empty_label.setVisible(False)
        cols = 4
        for idx, shot in enumerate(self._screenshots):
            card = ScreenshotCardWidget(shot, self)
            card.action_completed.connect(self.reload)
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)

    def _open_folder(self) -> None:
        if self._instance is not None:
            folder = Path(self._instance.instance_dir) / "screenshots"
            folder.mkdir(parents=True, exist_ok=True)
            open_local_path(folder)

    def retranslate_dynamic(self) -> None:
        self.open_folder_btn.setText(tr("screenshot.action.open_folder"))
        self.refresh_btn.setText(tr("common.refresh"))
        self.empty_label.setText(f"{tr('screenshot.empty')}\n{tr('screenshot.empty_hint')}")
