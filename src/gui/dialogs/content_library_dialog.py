from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from mcw_core.api.language.language_manager import tr
from src.gui.media.safe_rich_text import safe_external_url
from src.gui.theme.runtime import set_theme_icon
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.content.installed_content import InstalledContentItem, InstalledContentLibrary
from src.models.instance.instance import Instance


class ContentLibraryDialog(QDialog):
    refresh_requested = Signal()
    enabled_requested = Signal(list, bool)
    remove_requested = Signal(list)
    pin_requested = Signal(list, bool)
    ignore_update_requested = Signal(list, bool)
    import_requested = Signal(str, list)
    open_folder_requested = Signal(str)
    open_manager_requested = Signal(str)

    ITEM_ROLE = Qt.ItemDataRole.UserRole

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ContentLibraryDialog")
        self.setModal(False)
        self.setAcceptDrops(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        fitted_width, fitted_height = resize_dialog_to_screen(self, 1180, 640, 860, 500)
        self.setMinimumSize(min(860, fitted_width), min(500, fitted_height))
        self._instance: Instance | None = None
        self._library: InstalledContentLibrary | None = None
        self._busy = False
        self._build_ui()
        self.retranslate_dynamic()

    @property
    def instance(self) -> Instance | None:
        return self._instance

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._library = None
        self.table.setRowCount(0)
        self.details.clear()
        self.retranslate_dynamic()
        self._update_actions()

    def set_library(self, library: InstalledContentLibrary | None) -> None:
        if library is not None and self._instance is not None and library.instance_name != self._instance.name:
            return
        self._library = library
        self._render_table()
        self._render_summary()

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self.refresh_button.setEnabled(not self._busy and self._instance is not None)
        self.search_input.setEnabled(not self._busy)
        self.type_filter.setEnabled(not self._busy)
        self.provider_filter.setEnabled(not self._busy)
        self.status_filter.setEnabled(not self._busy)
        self.ownership_filter.setEnabled(not self._busy)
        self.pinned_only.setEnabled(not self._busy)
        self._update_actions()

    def selected_items(self) -> list[InstalledContentItem]:
        output: list[InstalledContentItem] = []
        seen: set[str] = set()
        for index in self.table.selectionModel().selectedRows():
            item = self.table.item(index.row(), 0)
            value = item.data(self.ITEM_ROLE) if item is not None else None
            if isinstance(value, InstalledContentItem) and value.item_id not in seen:
                seen.add(value.item_id)
                output.append(value)
        return output

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        self.title_label = QLabel()
        self.title_label.setObjectName("SectionTitle")
        self.context_label = QLabel()
        self.context_label.setObjectName("MutedLabel")
        root.addWidget(self.title_label)
        root.addWidget(self.context_label)

        filter_frame = QFrame()
        filter_frame.setObjectName("ToolbarFrame")
        filter_row = QHBoxLayout(filter_frame)
        filter_row.setContentsMargins(10, 8, 10, 8)
        filter_row.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self._apply_filter)
        self.type_filter = QComboBox()
        self.provider_filter = QComboBox()
        self.status_filter = QComboBox()
        self.ownership_filter = QComboBox()
        self.pinned_only = QCheckBox()
        self.type_filter.currentIndexChanged.connect(self._apply_filter)
        self.provider_filter.currentIndexChanged.connect(self._apply_filter)
        self.status_filter.currentIndexChanged.connect(self._apply_filter)
        self.ownership_filter.currentIndexChanged.connect(self._apply_filter)
        self.pinned_only.toggled.connect(self._apply_filter)
        filter_row.addWidget(self.search_input, 1)
        filter_row.addWidget(self.type_filter)
        filter_row.addWidget(self.provider_filter)
        filter_row.addWidget(self.status_filter)
        filter_row.addWidget(self.ownership_filter)
        filter_row.addWidget(self.pinned_only)
        root.addWidget(filter_frame)

        summary_row = QHBoxLayout()
        self.summary_label = QLabel()
        self.summary_label.setObjectName("TinyLabel")
        self.visible_summary_label = QLabel()
        self.visible_summary_label.setObjectName("TinyLabel")
        summary_row.addWidget(self.summary_label)
        summary_row.addStretch(1)
        summary_row.addWidget(self.visible_summary_label)
        root.addLayout(summary_row)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("ContentLibraryTable")
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.itemDoubleClicked.connect(lambda _item: self._open_manager())
        root.addWidget(self.table, 1)

        self.details = QPlainTextEdit()
        self.details.setObjectName("DetailsOutput")
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(150)
        root.addWidget(self.details)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.refresh_button = set_theme_icon(QPushButton(), "icon.action.refresh")
        self.add_local_button = set_theme_icon(QPushButton(), "icon.action.import")
        self.manage_button = set_theme_icon(QPushButton(), "icon.action.edit")
        self.open_folder_button = set_theme_icon(QPushButton(), "icon.action.folder")
        self.open_web_button = set_theme_icon(QPushButton(), "icon.action.web")
        self.enable_button = set_theme_icon(QPushButton(), "icon.action.enable")
        self.disable_button = set_theme_icon(QPushButton(), "icon.action.disable")
        self.pin_button = QPushButton()
        self.ignore_button = QPushButton()
        self.remove_button = set_theme_icon(QPushButton(), "icon.action.remove")
        self.remove_button.setObjectName("DangerButton")

        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.add_local_button.clicked.connect(self._choose_local_files)
        self.manage_button.clicked.connect(self._open_manager)
        self.open_folder_button.clicked.connect(self._open_folder)
        self.open_web_button.clicked.connect(self._open_web)
        self.enable_button.clicked.connect(lambda: self._emit_enabled(True))
        self.disable_button.clicked.connect(lambda: self._emit_enabled(False))
        self.pin_button.clicked.connect(self._toggle_pin)
        self.ignore_button.clicked.connect(self._toggle_ignore)
        self.remove_button.clicked.connect(self._remove_selected)

        action_row.addWidget(self.refresh_button)
        action_row.addWidget(self.add_local_button)
        action_row.addWidget(self.manage_button)
        action_row.addWidget(self.open_folder_button)
        action_row.addWidget(self.open_web_button)
        action_row.addStretch(1)
        action_row.addWidget(self.enable_button)
        action_row.addWidget(self.disable_button)
        action_row.addWidget(self.pin_button)
        action_row.addWidget(self.ignore_button)
        action_row.addWidget(self.remove_button)
        root.addLayout(action_row)

    def _render_table(self) -> None:
        selected_ids = {item.item_id for item in self.selected_items()}
        items = list(self._library.items) if self._library is not None else []
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(items))
        for row, content in enumerate(items):
            source = self._provider_label(content)
            flags: list[str] = []
            if content.pinned:
                flags.append(tr("content.library.flag.pinned"))
            if content.ignored_update:
                flags.append(tr("content.library.flag.ignored"))
            status = tr(f"content.library.status.{content.status}", default=content.status.title())
            if flags:
                status = f"{status} • {' / '.join(flags)}"
            values = (
                tr(f"content.library.type.{content.content_type}", default=content.content_type.title()),
                content.name,
                content.version or tr("common.unknown"),
                source,
                status,
                self._format_size(content.size),
                content.file_name or content.target_path,
            )
            tooltip = self._details_text(content)
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setData(self.ITEM_ROLE, content)
                cell.setToolTip(tooltip)
                self.table.setItem(row, column, cell)
        self.table.setSortingEnabled(True)
        self._apply_filter()
        if selected_ids:
            for row in range(self.table.rowCount()):
                cell = self.table.item(row, 0)
                content = cell.data(self.ITEM_ROLE) if cell is not None else None
                if isinstance(content, InstalledContentItem) and content.item_id in selected_ids:
                    self.table.selectRow(row)
        elif items:
            self.table.selectRow(0)
        self._selection_changed()

    def _render_summary(self) -> None:
        library = self._library
        if library is None:
            self.summary_label.setText(tr("content.library.summary.empty"))
            return
        self.summary_label.setText(tr(
            "content.library.summary",
            total=library.total_count,
            enabled=library.enabled_count,
            managed=library.managed_count,
            pending=library.pending_count,
            missing=library.missing_count,
            size=self._format_size(library.total_size),
        ))

    def _apply_filter(self) -> None:
        query = self.search_input.text().strip().casefold()
        kind = str(self.type_filter.currentData() or "")
        provider = str(self.provider_filter.currentData() or "")
        status = str(self.status_filter.currentData() or "")
        ownership = str(self.ownership_filter.currentData() or "")
        pinned_only = self.pinned_only.isChecked()
        visible_count = 0
        for row in range(self.table.rowCount()):
            cell = self.table.item(row, 0)
            content = cell.data(self.ITEM_ROLE) if cell is not None else None
            visible = isinstance(content, InstalledContentItem)
            if visible and kind:
                visible = content.content_type == kind
            if visible and provider:
                visible = content.provider == provider
            if visible and status:
                visible = content.status == status
            if visible and ownership == "managed":
                visible = content.managed_by_modpack
            elif visible and ownership == "user":
                visible = not content.managed_by_modpack and content.content_type != "modpack"
            if visible and pinned_only:
                visible = content.pinned
            if visible and query:
                haystack = " ".join((content.name, content.version, content.provider, content.project_id, content.file_name, content.target_path)).casefold()
                visible = query in haystack
            self.table.setRowHidden(row, not visible)
            visible_count += int(visible)
        self.visible_summary_label.setText(tr("content.library.visible_summary", visible=visible_count, total=self.table.rowCount()))
        self._update_actions()

    def _selection_changed(self) -> None:
        selected = self.selected_items()
        self.details.setPlainText("\n\n".join(self._details_text(item) for item in selected[:5]))
        self._update_actions()

    def _update_actions(self) -> None:
        selected = self.selected_items()
        available = not self._busy and bool(selected)
        toggleable = [item for item in selected if item.toggleable]
        removable = [item for item in selected if item.removable]
        action_kind = self._action_kind(selected)
        self.add_local_button.setEnabled(not self._busy and self._instance is not None and self._import_kind() != "modpack")
        self.manage_button.setEnabled(not self._busy and self._instance is not None and action_kind in {"mod", "resourcepack", "shader"})
        self.open_folder_button.setEnabled(not self._busy and self._instance is not None and action_kind in {"mod", "resourcepack", "shader", "modpack"})
        self.open_web_button.setEnabled(available and len(selected) == 1 and bool(safe_external_url(selected[0].project_url)))
        self.enable_button.setEnabled(available and bool(toggleable) and any(not item.enabled for item in toggleable))
        self.disable_button.setEnabled(available and bool(toggleable) and any(item.enabled for item in toggleable))
        self.pin_button.setEnabled(available)
        self.ignore_button.setEnabled(available)
        self.remove_button.setEnabled(available and bool(removable))
        self.pin_button.setText(tr("content.library.unpin") if selected and all(item.pinned for item in selected) else tr("content.library.pin"))
        self.ignore_button.setText(tr("content.library.unignore") if selected and all(item.ignored_update for item in selected) else tr("content.library.ignore"))

    def _emit_enabled(self, enabled: bool) -> None:
        item_ids = [item.item_id for item in self.selected_items() if item.toggleable and item.enabled != enabled]
        if item_ids:
            self.enabled_requested.emit(item_ids, enabled)

    def _toggle_pin(self) -> None:
        selected = self.selected_items()
        if selected:
            self.pin_requested.emit([item.item_id for item in selected], not all(item.pinned for item in selected))

    def _toggle_ignore(self) -> None:
        selected = self.selected_items()
        if selected:
            self.ignore_update_requested.emit([item.item_id for item in selected], not all(item.ignored_update for item in selected))

    def _remove_selected(self) -> None:
        removable = [item for item in self.selected_items() if item.removable]
        if not removable:
            return
        answer = QMessageBox.question(self, tr("content.library.remove_title"), tr("content.library.remove_confirm", count=len(removable)), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.remove_requested.emit([item.item_id for item in removable])

    def _open_folder(self) -> None:
        kind = self._action_kind(self.selected_items())
        if kind:
            self.open_folder_requested.emit(kind)

    def _open_manager(self) -> None:
        kind = self._action_kind(self.selected_items())
        if kind:
            self.open_manager_requested.emit(kind)

    def _choose_local_files(self) -> None:
        if self._instance is None:
            return
        kind = self._import_kind()
        if kind == "modpack":
            return
        filters = {
            "mod": tr("content.library.file_filter.mods"),
            "resourcepack": tr("content.library.file_filter.packs"),
            "shader": tr("content.library.file_filter.packs"),
            "auto": tr("content.library.file_filter.all"),
        }
        paths, _selected = QFileDialog.getOpenFileNames(self, tr("content.library.import_title"), "", filters[kind])
        if paths:
            self.import_requested.emit(kind, [Path(path) for path in paths])

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        supported = any(url.isLocalFile() and self._accepts_local_path(Path(url.toLocalFile())) for url in urls)
        if not self._busy and self._instance is not None and self._import_kind() != "modpack" and supported:
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if self._busy or self._instance is None or self._import_kind() == "modpack":
            event.ignore()
            return
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile() and self._accepts_local_path(Path(url.toLocalFile()))]
        if not paths:
            event.ignore()
            return
        event.acceptProposedAction()
        self.import_requested.emit(self._import_kind(), paths)

    def _import_kind(self) -> str:
        kind = str(self.type_filter.currentData() or "").strip().casefold()
        return kind if kind else "auto"

    def _accepts_local_path(self, path: Path) -> bool:
        suffix = Path(path).suffix.casefold()
        kind = self._import_kind()
        if kind == "mod":
            return suffix == ".jar"
        if kind in {"resourcepack", "shader"}:
            return suffix == ".zip"
        return kind == "auto" and suffix in {".jar", ".zip"}

    def _action_kind(self, selected: list[InstalledContentItem]) -> str:
        kinds = {item.content_type for item in selected}
        if len(kinds) == 1:
            return next(iter(kinds))
        filtered = str(self.type_filter.currentData() or "").strip().casefold()
        return filtered if filtered in {"mod", "resourcepack", "shader", "modpack"} else ""

    def _open_web(self) -> None:
        selected = self.selected_items()
        url = safe_external_url(selected[0].project_url if len(selected) == 1 else "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    @staticmethod
    def _provider_label(item: InstalledContentItem) -> str:
        provider = tr(f"content.library.provider.{item.provider}", default=item.provider.title())
        if item.managed_by_modpack:
            owner = tr(f"content.library.provider.{item.source_pack_provider}", default=item.source_pack_provider.title())
            return tr("content.library.provider.managed", provider=provider, pack=owner)
        return provider

    @staticmethod
    def _details_text(item: InstalledContentItem) -> str:
        lines = [
            item.name,
            tr("content.library.detail.type", value=tr(f"content.library.type.{item.content_type}", default=item.content_type.title())),
            tr("content.library.detail.provider", value=ContentLibraryDialog._provider_label(item)),
            tr("content.library.detail.status", value=tr(f"content.library.status.{item.status}", default=item.status.title())),
            tr("content.library.detail.version", value=item.version or tr("common.unknown")),
            tr("content.library.detail.path", value=item.target_path or "—"),
        ]
        if item.project_id:
            lines.append(tr("content.library.detail.project_id", value=item.project_id))
        if item.version_id:
            lines.append(tr("content.library.detail.version_id", value=item.version_id))
        if item.file_id:
            lines.append(tr("content.library.detail.file_id", value=item.file_id))
        if item.sha512 or item.sha1:
            lines.append(tr("content.library.detail.hash", value=item.sha512 or item.sha1))
        return "\n".join(lines)

    @staticmethod
    def _format_size(size: int) -> str:
        value = max(0, int(size))
        units = ("B", "KiB", "MiB", "GiB")
        amount = float(value)
        unit = units[0]
        for candidate in units:
            unit = candidate
            if amount < 1024.0 or candidate == units[-1]:
                break
            amount /= 1024.0
        return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("content.library.title"))
        self.title_label.setText(tr("content.library.title"))
        self.context_label.setText(tr("content.library.context", instance=self._instance.name if self._instance is not None else tr("common.none")))
        self.search_input.setPlaceholderText(tr("content.library.search"))
        self._reset_combo(self.type_filter, (
            (tr("content.library.filter.all_types"), ""),
            (tr("content.library.type.modpack"), "modpack"),
            (tr("content.library.type.mod"), "mod"),
            (tr("content.library.type.resourcepack"), "resourcepack"),
            (tr("content.library.type.shader"), "shader"),
        ))
        self._reset_combo(self.provider_filter, (
            (tr("content.library.filter.all_providers"), ""),
            (tr("content.library.provider.modrinth"), "modrinth"),
            (tr("content.library.provider.curseforge"), "curseforge"),
            (tr("content.library.provider.ftb"), "ftb"),
            (tr("content.library.provider.atlauncher"), "atlauncher"),
            (tr("content.library.provider.local"), "local"),
            (tr("content.library.provider.manual"), "manual"),
            (tr("content.library.provider.unknown"), "unknown"),
        ))
        self._reset_combo(self.status_filter, (
            (tr("content.library.filter.all_statuses"), ""),
            (tr("content.library.status.ready"), "ready"),
            (tr("content.library.status.disabled"), "disabled"),
            (tr("content.library.status.pending"), "pending"),
            (tr("content.library.status.missing"), "missing"),
            (tr("content.library.status.broken"), "broken"),
        ))
        self._reset_combo(self.ownership_filter, (
            (tr("content.library.filter.all_ownership"), ""),
            (tr("content.library.filter.user_added"), "user"),
            (tr("content.library.filter.managed"), "managed"),
        ))
        self.pinned_only.setText(tr("content.library.filter.pinned_only"))
        self.table.setHorizontalHeaderLabels((
            tr("content.library.column.type"),
            tr("content.library.column.name"),
            tr("content.library.column.version"),
            tr("content.library.column.source"),
            tr("content.library.column.status"),
            tr("content.library.column.size"),
            tr("content.library.column.file"),
        ))
        self.refresh_button.setText(tr("content.library.refresh"))
        self.add_local_button.setText(tr("content.library.add_local"))
        self.manage_button.setText(tr("content.library.manage"))
        self.open_folder_button.setText(tr("content.library.open_folder"))
        self.open_web_button.setText(tr("content.library.open_web"))
        self.enable_button.setText(tr("content.library.enable"))
        self.disable_button.setText(tr("content.library.disable"))
        self.remove_button.setText(tr("content.library.remove"))
        self._render_summary()
        self._apply_filter()

    @staticmethod
    def _reset_combo(combo: QComboBox, entries: tuple[tuple[str, str], ...]) -> None:
        current = str(combo.currentData() or "")
        combo.blockSignals(True)
        combo.clear()
        for label, value in entries:
            combo.addItem(label, value)
        index = combo.findData(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)
