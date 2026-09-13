from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.language.language_manager import tr
from mcw_core.api.minecraft.world_manager import WorldManager
from src.gui.formatters.time_formatter import format_last_played
from src.gui.platform_open import open_local_path
from src.gui.theme.runtime import set_theme_icon, set_theme_pixmap
from src.models.instance.instance import Instance
from src.models.world.world_info import WorldInfo


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{max(1, size_bytes // 1024)} KB"
    mb = size_bytes / (1024 * 1024)
    if mb < 1024:
        return f"{mb:.1f} MB"
    gb = mb / 1024
    return f"{gb:.2f} GB"


class WorldCardWidget(QFrame):
    quick_play_clicked = Signal(str)
    action_completed = Signal()

    def __init__(self, instance_dir: Path, world: WorldInfo, parent=None) -> None:
        super().__init__(parent)
        self.instance_dir = instance_dir
        self.world = world
        self.setObjectName("WorldCard")
        self.setStyleSheet(
            "#WorldCard { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 6px; } "
            "#WorldCard:hover { background: rgba(255, 255, 255, 0.07); border-color: rgba(255, 255, 255, 0.15); }"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        # World Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(54, 54)
        self.icon_label.setStyleSheet("border-radius: 6px; background: rgba(0, 0, 0, 0.2);")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(self.world.icon_path) if self.world.icon_path and Path(self.world.icon_path).is_file() else QPixmap()
        if not pixmap.isNull():
            self.icon_label.setPixmap(pixmap.scaled(54, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            set_theme_pixmap(self.icon_label, "icon.action.worlds", 48, 48)
        layout.addWidget(self.icon_label)

        # World Info (Name, Mode, Last Played, Size)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.title_label = QLabel(self.world.display_name)
        self.title_label.setObjectName("SectionTitle")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_row.addWidget(self.title_label)

        # Mode Badge
        mode_key = f"world.mode.{self.world.game_mode}"
        mode_text = tr(mode_key)
        self.mode_badge = QLabel(mode_text)
        self.mode_badge.setStyleSheet(
            "background: rgba(80, 160, 255, 0.18); color: #8ab4f8; border-radius: 4px; padding: 2px 6px; font-size: 11px;"
            if not self.world.is_hardcore
            else "background: rgba(240, 80, 80, 0.22); color: #ff8a8a; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;"
        )
        title_row.addWidget(self.mode_badge)
        title_row.addStretch(1)
        info_layout.addLayout(title_row)

        details_row = QHBoxLayout()
        details_row.setSpacing(14)
        iso_time = ""
        if self.world.last_played > 0:
            try:
                iso_time = datetime.fromtimestamp(self.world.last_played / 1000, tz=timezone.utc).isoformat()
            except (ValueError, OSError):
                iso_time = ""
        time_text = format_last_played(iso_time)
        self.time_label = QLabel(tr("world.last_played", time=time_text))
        self.time_label.setObjectName("MutedLabel")
        details_row.addWidget(self.time_label)

        size_text = _format_size(self.world.folder_size_bytes)
        self.size_label = QLabel(tr("world.size", size=size_text))
        self.size_label.setObjectName("MutedLabel")
        details_row.addWidget(self.size_label)

        if self.world.version_name:
            self.ver_label = QLabel(f"MC: {self.world.version_name}")
            self.ver_label.setObjectName("MutedLabel")
            details_row.addWidget(self.ver_label)

        details_row.addStretch(1)
        info_layout.addLayout(details_row)
        layout.addLayout(info_layout, 1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.play_button = set_theme_icon(QPushButton(tr("world.action.play")), "icon.action.launch")
        self.play_button.setObjectName("PrimaryButton")
        self.play_button.clicked.connect(lambda: self.quick_play_clicked.emit(self.world.folder_name))
        btn_layout.addWidget(self.play_button)

        self.backup_button = set_theme_icon(QPushButton(tr("world.action.backup")), "icon.action.save")
        self.backup_button.clicked.connect(self._backup)
        btn_layout.addWidget(self.backup_button)

        self.duplicate_button = set_theme_icon(QPushButton(tr("world.action.duplicate")), "icon.action.clone")
        self.duplicate_button.clicked.connect(self._duplicate)
        btn_layout.addWidget(self.duplicate_button)

        self.folder_button = set_theme_icon(QPushButton(), "icon.action.folder")
        self.folder_button.setToolTip(tr("world.action.open_folder"))
        self.folder_button.clicked.connect(lambda: open_local_path(self.instance_dir / "saves" / self.world.folder_name))
        btn_layout.addWidget(self.folder_button)

        self.delete_button = set_theme_icon(QPushButton(), "icon.action.remove")
        self.delete_button.setObjectName("DangerButton")
        self.delete_button.setToolTip(tr("world.action.delete"))
        self.delete_button.clicked.connect(self._delete)
        btn_layout.addWidget(self.delete_button)

        layout.addLayout(btn_layout)

    def _backup(self) -> None:
        try:
            archive = WorldManager.backup_world(self.instance_dir, self.world.folder_name)
            QMessageBox.information(
                self,
                tr("world.action.backup"),
                tr("world.backup_success", name=self.world.display_name),
            )
            self.action_completed.emit()
        except Exception as error:
            QMessageBox.critical(self, tr("world.action.backup"), str(error))

    def _duplicate(self) -> None:
        try:
            WorldManager.duplicate_world(self.instance_dir, self.world.folder_name)
            self.action_completed.emit()
        except Exception as error:
            QMessageBox.critical(self, tr("world.action.duplicate"), str(error))

    def _delete(self) -> None:
        confirm = QMessageBox.question(
            self,
            tr("world.confirm_delete.title"),
            tr("world.confirm_delete.text", name=self.world.display_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                WorldManager.delete_world(self.instance_dir, self.world.folder_name)
                self.action_completed.emit()
            except Exception as error:
                QMessageBox.critical(self, tr("world.confirm_delete.title"), str(error))


class InstanceWorldsTab(QWidget):
    quick_play_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._instance: Instance | None = None
        self._worlds: list[WorldInfo] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Header action bar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.import_button = set_theme_icon(QPushButton(tr("world.action.import")), "icon.action.import")
        self.import_button.clicked.connect(self._import_world)
        toolbar.addWidget(self.import_button)

        self.open_saves_button = set_theme_icon(QPushButton(tr("world.action.open_folder")), "icon.action.folder")
        self.open_saves_button.clicked.connect(self._open_saves_folder)
        toolbar.addWidget(self.open_saves_button)

        self.refresh_button = set_theme_icon(QPushButton(tr("common.refresh")), "icon.action.refresh")
        self.refresh_button.clicked.connect(self.reload)
        toolbar.addWidget(self.refresh_button)

        toolbar.addStretch(1)
        root.addLayout(toolbar)

        # Scroll area for worlds list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch(1)

        self.scroll_area.setWidget(self.cards_container)
        root.addWidget(self.scroll_area, 1)

        # Empty label
        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setObjectName("MutedLabel")
        self.empty_label.setText(f"{tr('world.empty')}\n{tr('world.empty_hint')}")
        self.empty_label.setVisible(False)
        root.addWidget(self.empty_label)

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self.reload()

    def reload(self) -> None:
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self._instance is None:
            self.empty_label.setVisible(True)
            self._worlds = []
            return

        instance_dir = Path(getattr(self._instance, "instance_dir", ""))
        self._worlds = WorldManager.list_worlds(instance_dir)

        if not self._worlds:
            self.empty_label.setVisible(True)
            return

        self.empty_label.setVisible(False)
        for world in self._worlds:
            card = WorldCardWidget(instance_dir, world, self)
            card.quick_play_clicked.connect(self.quick_play_requested.emit)
            card.action_completed.connect(self.reload)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    @property
    def latest_world(self) -> WorldInfo | None:
        return self._worlds[0] if self._worlds else None

    def _open_saves_folder(self) -> None:
        if self._instance is not None:
            open_local_path(Path(self._instance.instance_dir) / "saves")

    def _import_world(self) -> None:
        if self._instance is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("world.action.import"),
            "",
            "World Archives (*.zip);;All Files (*.*)",
        )
        if not path:
            return
        try:
            WorldManager.import_world(self._instance.instance_dir, path)
            self.reload()
        except Exception as error:
            QMessageBox.critical(self, tr("world.action.import"), str(error))

    def retranslate_dynamic(self) -> None:
        self.import_button.setText(tr("world.action.import"))
        self.open_saves_button.setText(tr("world.action.open_folder"))
        self.refresh_button.setText(tr("common.refresh"))
        self.empty_label.setText(tr("world.empty"))
