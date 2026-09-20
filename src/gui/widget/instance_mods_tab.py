from __future__ import annotations

from pathlib import Path
import shutil

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.language.language_manager import tr
from src.gui.platform_open import open_local_path
from src.gui.theme.runtime import set_theme_icon
from src.models.instance.instance import Instance


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{max(1, size_bytes // 1024)} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


class InstanceModsTab(QWidget):
    open_advanced_mod_manager_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._instance: Instance | None = None
        self._mod_files: list[Path] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Action bar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("instance_workspace.search_placeholder"))
        self.search_input.textChanged.connect(self._filter_table)
        toolbar.addWidget(self.search_input, 1)

        self.add_mod_btn = set_theme_icon(QPushButton(tr("instance_mods.action.add")), "icon.action.add")
        self.add_mod_btn.setObjectName("PrimaryButton")
        self.add_mod_btn.clicked.connect(self._add_mod)
        toolbar.addWidget(self.add_mod_btn)

        self.open_mods_btn = set_theme_icon(QPushButton(tr("instance_mods.action.open_folder")), "icon.action.folder")
        self.open_mods_btn.clicked.connect(self._open_mods_folder)
        toolbar.addWidget(self.open_mods_btn)

        self.advanced_btn = set_theme_icon(QPushButton(tr("instance.manage_mods")), "icon.action.mods")
        self.advanced_btn.clicked.connect(self.open_advanced_mod_manager_requested.emit)
        toolbar.addWidget(self.advanced_btn)

        self.refresh_btn = set_theme_icon(QPushButton(tr("common.refresh")), "icon.action.refresh")
        self.refresh_btn.clicked.connect(self.reload)
        toolbar.addWidget(self.refresh_btn)

        root.addLayout(toolbar)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            tr("instance_mods.status"),
            tr("instance_mods.name"),
            tr("instance_mods.size"),
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        # Bottom row
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        self.count_label = QLabel()
        self.count_label.setObjectName("MutedLabel")
        bottom_bar.addWidget(self.count_label)
        bottom_bar.addStretch(1)

        self.remove_btn = set_theme_icon(QPushButton(tr("instance_mods.action.remove")), "icon.action.remove")
        self.remove_btn.setObjectName("DangerButton")
        self.remove_btn.clicked.connect(self._remove_selected)
        bottom_bar.addWidget(self.remove_btn)

        root.addLayout(bottom_bar)

        # Empty Label
        self.empty_label = QLabel(f"{tr('instance_mods.empty')}\n{tr('instance_mods.empty_hint')}")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setObjectName("MutedLabel")
        self.empty_label.setVisible(False)
        root.addWidget(self.empty_label)

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self.reload()

    def reload(self) -> None:
        self.table.setRowCount(0)
        self._mod_files.clear()

        if self._instance is None:
            self.empty_label.setVisible(True)
            self.table.setVisible(False)
            self.count_label.setText("")
            return

        mods_dir = Path(self._instance.instance_dir) / "mods"
        if not mods_dir.is_dir():
            self.empty_label.setVisible(True)
            self.table.setVisible(False)
            self.count_label.setText("")
            return

        for p in mods_dir.iterdir():
            if not p.is_file():
                continue
            name_lower = p.name.lower()
            if name_lower.endswith(".jar") or name_lower.endswith(".jar.disabled"):
                self._mod_files.append(p)

        self._mod_files.sort(key=lambda p: p.name.lower())
        if not self._mod_files:
            self.empty_label.setVisible(True)
            self.table.setVisible(False)
            self.count_label.setText("")
            return

        self.empty_label.setVisible(False)
        self.table.setVisible(True)
        self._populate_table()

    def _populate_table(self) -> None:
        self.table.setRowCount(len(self._mod_files))
        enabled_count = 0

        for row, path in enumerate(self._mod_files):
            is_enabled = not path.name.lower().endswith(".disabled")
            if is_enabled:
                enabled_count += 1

            # Checkbox for status
            checkbox = QCheckBox()
            checkbox.setChecked(is_enabled)
            checkbox.toggled.connect(lambda checked, p=path: self._toggle_mod(p, checked))
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.setContentsMargins(8, 0, 8, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(checkbox)
            self.table.setCellWidget(row, 0, cell_widget)

            # Mod Name
            clean_name = path.name[:-9] if path.name.lower().endswith(".disabled") else path.name
            name_item = QTableWidgetItem(clean_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setData(Qt.ItemDataRole.UserRole, str(path))
            if not is_enabled:
                name_item.setForeground(Qt.GlobalColor.darkGray)
            self.table.setItem(row, 1, name_item)

            # Size
            size = 0
            try:
                size = path.stat().st_size
            except OSError:
                pass
            size_item = QTableWidgetItem(_format_size(size))
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, size_item)

        self.count_label.setText(f"{enabled_count}/{len(self._mod_files)} {tr('instance_mods.status.enabled').lower()}")

    def _filter_table(self, query: str) -> None:
        query = query.strip().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            visible = True
            if item is not None and query:
                visible = query in item.text().lower()
            self.table.setRowHidden(row, not visible)

    def _toggle_mod(self, path: Path, enabled: bool) -> None:
        if not path.exists():
            return
        if enabled and path.name.lower().endswith(".disabled"):
            new_path = path.with_name(path.name[:-9])
            try:
                path.rename(new_path)
            except OSError:
                pass
        elif not enabled and not path.name.lower().endswith(".disabled"):
            new_path = path.with_name(path.name + ".disabled")
            try:
                path.rename(new_path)
            except OSError:
                pass
        self.reload()

    def _add_mod(self) -> None:
        if self._instance is None:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("instance_mods.action.add"),
            "",
            "Minecraft Mods (*.jar);;All Files (*.*)",
        )
        if not paths:
            return

        mods_dir = Path(self._instance.instance_dir) / "mods"
        mods_dir.mkdir(parents=True, exist_ok=True)

        for src in paths:
            try:
                shutil.copy2(src, mods_dir / Path(src).name)
            except Exception as err:
                QMessageBox.critical(self, tr("instance_mods.action.add"), str(err))

        self.reload()

    def _remove_selected(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        item = self.table.item(row, 1)
        if item is None:
            return

        file_path = Path(str(item.data(Qt.ItemDataRole.UserRole)))
        confirm = QMessageBox.question(
            self,
            tr("instance_mods.confirm_remove.title"),
            tr("instance_mods.confirm_remove.text", name=item.text()),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                if file_path.exists():
                    file_path.unlink()
                self.reload()
            except Exception as err:
                QMessageBox.critical(self, tr("instance_mods.confirm_remove.title"), str(err))

    def _open_mods_folder(self) -> None:
        if self._instance is not None:
            mods_dir = Path(self._instance.instance_dir) / "mods"
            mods_dir.mkdir(parents=True, exist_ok=True)
            open_local_path(mods_dir)

    def retranslate_dynamic(self) -> None:
        self.search_input.setPlaceholderText(tr("instance_mods.search_placeholder"))
        self.add_mod_btn.setText(tr("instance_mods.action.add"))
        self.open_mods_btn.setText(tr("instance_mods.action.open_folder"))
        self.advanced_btn.setText(tr("instance.manage_mods"))
        self.refresh_btn.setText(tr("common.refresh"))
        self.remove_btn.setText(tr("instance_mods.action.remove"))
        self.empty_label.setText(tr("instance_mods.empty"))
        self.table.setHorizontalHeaderLabels([
            tr("instance_mods.column.status"),
            tr("instance_mods.column.name"),
            tr("instance_mods.column.size"),
            tr("instance_mods.column.modified"),
        ])
