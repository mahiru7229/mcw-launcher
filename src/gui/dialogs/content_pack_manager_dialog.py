from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from mcw_core.api.content.content_pack_manager import ContentPackManager
from mcw_core.api.language.language_manager import tr
from src.gui.media.safe_rich_text import safe_external_url
from src.gui.theme.runtime import set_theme_icon
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.content.content_pack import ContentPackEntry
from src.models.instance.instance import Instance


class ContentPackManagerDialog(QDialog):
    browse_requested = Signal(str)
    import_requested = Signal(str, object)
    refresh_requested = Signal(str)
    toggle_requested = Signal(str, str, bool)
    remove_requested = Signal(str, str)
    open_folder_requested = Signal(str)

    ENTRY_ROLE = Qt.ItemDataRole.UserRole

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._instance: Instance | None = None
        self._entries: dict[str, list[ContentPackEntry]] = {ContentPackManager.RESOURCE_PACK: [], ContentPackManager.SHADER_PACK: []}
        self._busy = False
        self.setAcceptDrops(True)
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 980, 620, 760, 500)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)
        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        self.context_label = QLabel()
        self.context_label.setObjectName("MutedLabel")
        self.context_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.context_label)

        self.tabs = QTabWidget()
        self._tables: dict[str, QTableWidget] = {}
        for kind in (ContentPackManager.RESOURCE_PACK, ContentPackManager.SHADER_PACK):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 10, 0, 0)
            layout.setSpacing(8)
            table = QTableWidget(0, 5)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setAlternatingRowColors(True)
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            table.itemSelectionChanged.connect(self._selection_changed)
            layout.addWidget(table, 1)
            self._tables[kind] = table
            self.tabs.addTab(page, "")
        self.tabs.currentChanged.connect(self._tab_changed)
        root.addWidget(self.tabs, 1)

        actions = QHBoxLayout()
        self.browse_button = set_theme_icon(QPushButton(), "icon.action.search")
        self.browse_button.setObjectName("PrimaryButton")
        self.import_button = set_theme_icon(QPushButton(), "icon.action.import")
        self.enable_button = QPushButton()
        self.remove_button = set_theme_icon(QPushButton(), "icon.action.remove")
        self.remove_button.setObjectName("DangerButton")
        self.open_web_button = set_theme_icon(QPushButton(), "icon.action.web")
        self.open_folder_button = set_theme_icon(QPushButton(), "icon.action.folder")
        self.refresh_button = set_theme_icon(QPushButton(), "icon.action.refresh")
        self.browse_button.clicked.connect(lambda: self.browse_requested.emit(self.current_kind()))
        self.import_button.clicked.connect(self._choose_import)
        self.enable_button.clicked.connect(self._toggle_selected)
        self.remove_button.clicked.connect(self._remove_selected)
        self.open_web_button.clicked.connect(self._open_selected_web)
        self.open_folder_button.clicked.connect(lambda: self.open_folder_requested.emit(self.current_kind()))
        self.refresh_button.clicked.connect(lambda: self.refresh_requested.emit(self.current_kind()))
        actions.addWidget(self.browse_button)
        actions.addWidget(self.import_button)
        actions.addWidget(self.enable_button)
        actions.addWidget(self.remove_button)
        actions.addStretch()
        actions.addWidget(self.open_web_button)
        actions.addWidget(self.open_folder_button)
        actions.addWidget(self.refresh_button)
        root.addLayout(actions)
        self._selection_changed()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if not self._busy and self._instance is not None and any(url.isLocalFile() and url.toLocalFile().casefold().endswith(".zip") for url in urls):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if self._busy or self._instance is None:
            event.ignore()
            return
        path = next((Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile() and url.toLocalFile().casefold().endswith(".zip")), None)
        if path is None:
            event.ignore()
            return
        event.acceptProposedAction()
        self.import_requested.emit(self.current_kind(), path)

    @property
    def instance(self) -> Instance | None:
        return self._instance

    def set_instance(self, instance: Instance) -> None:
        self._instance = instance
        self._entries = {ContentPackManager.RESOURCE_PACK: [], ContentPackManager.SHADER_PACK: []}
        for kind in self._entries:
            self._render(kind)
        self.retranslate_dynamic()

    def set_entries(self, instance_name: str, content_type: str, entries: list[ContentPackEntry]) -> None:
        if self._instance is None or self._instance.name != str(instance_name):
            return
        kind = ContentPackManager.normalize_type(content_type)
        self._entries[kind] = list(entries)
        self._render(kind)
        self._selection_changed()

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self.tabs.setEnabled(not self._busy)
        self.browse_button.setEnabled(not self._busy and self._instance is not None)
        self.import_button.setEnabled(not self._busy and self._instance is not None)
        self.open_folder_button.setEnabled(not self._busy and self._instance is not None)
        self.refresh_button.setEnabled(not self._busy and self._instance is not None)
        self._selection_changed()

    def current_kind(self) -> str:
        return ContentPackManager.RESOURCE_PACK if self.tabs.currentIndex() == 0 else ContentPackManager.SHADER_PACK

    def set_current_kind(self, content_type: str) -> None:
        kind = ContentPackManager.normalize_type(content_type)
        self.tabs.setCurrentIndex(0 if kind == ContentPackManager.RESOURCE_PACK else 1)

    def selected_entry(self) -> ContentPackEntry | None:
        table = self._tables[self.current_kind()]
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        value = item.data(self.ENTRY_ROLE) if item is not None else None
        return value if isinstance(value, ContentPackEntry) else None

    def _choose_import(self) -> None:
        if self._instance is None:
            return
        kind = self.current_kind()
        label = tr("content.kind.resourcepack") if kind == ContentPackManager.RESOURCE_PACK else tr("content.kind.shader")
        path, _ = QFileDialog.getOpenFileName(self, tr("content.manager.import_title", kind=label), "", tr("content.manager.zip_filter"))
        if path:
            self.import_requested.emit(kind, Path(path))

    def _toggle_selected(self) -> None:
        entry = self.selected_entry()
        if entry is not None:
            self.toggle_requested.emit(entry.content_type, entry.entry_id, not entry.enabled)

    def _open_selected_web(self) -> None:
        entry = self.selected_entry()
        url = safe_external_url(entry.project_url if entry is not None else "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _remove_selected(self) -> None:
        entry = self.selected_entry()
        if entry is None:
            return
        answer = QMessageBox.question(self, tr("content.manager.remove_title"), tr("content.manager.remove_confirm", name=entry.project_name), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.remove_requested.emit(entry.content_type, entry.entry_id)

    def _tab_changed(self, _index: int) -> None:
        self._selection_changed()
        if self._instance is not None:
            self.refresh_requested.emit(self.current_kind())

    def _selection_changed(self) -> None:
        entry = self.selected_entry()
        available = not self._busy and entry is not None
        self.enable_button.setEnabled(available)
        self.remove_button.setEnabled(available)
        self.open_web_button.setEnabled(available and bool(safe_external_url(entry.project_url if entry is not None else "")))
        self.enable_button.setText(tr("content.manager.disable") if entry is not None and entry.enabled else tr("content.manager.enable"))

    def _render(self, kind: str) -> None:
        table = self._tables[kind]
        entries = self._entries[kind]
        table.clearSelection()
        table.clearContents()
        table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            version = entry.version_number or tr("common.unknown")
            if entry.pack_format is not None:
                version = tr("content.manager.version_with_pack_format", version=version, pack_format=entry.pack_format)
            values = (entry.project_name, entry.provider.title(), version, tr("content.manager.enabled") if entry.enabled else tr("content.manager.disabled"), entry.file_name)
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(self.ENTRY_ROLE, entry)
                if entry.pack_description:
                    item.setToolTip(entry.pack_description)
                table.setItem(row, column, item)
        if entries:
            table.selectRow(0)

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("content.manager.title"))
        self.title_label.setText(tr("content.manager.title"))
        self.context_label.setText(tr("content.manager.context", instance=self._instance.name if self._instance is not None else tr("common.none")))
        self.tabs.setTabText(0, tr("content.kind.resourcepacks"))
        self.tabs.setTabText(1, tr("content.kind.shaders"))
        headers = (tr("content.column.project"), tr("content.column.provider"), tr("content.column.version"), tr("content.column.status"), tr("content.column.file"))
        for table in self._tables.values():
            table.setHorizontalHeaderLabels(headers)
        self.browse_button.setText(tr("content.manager.browse"))
        self.import_button.setText(tr("content.manager.import"))
        self.remove_button.setText(tr("content.manager.remove"))
        self.open_web_button.setText(tr("content.manager.open_web"))
        self.open_folder_button.setText(tr("content.manager.open_folder"))
        self.refresh_button.setText(tr("content.manager.refresh"))
        self._selection_changed()
