from __future__ import annotations

import re
from dataclasses import replace

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from mcw_core.api.instance.instance_manager import InstanceManager
from mcw_core.api.language.language_manager import tr
from mcw_core.api.modloader.mod_loader_manager import ModLoaderManager
from src.models.instance.instance import Instance
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthVersion
from src.gui.media.remote_image_cache import RemoteImageCache
from src.gui.media.safe_rich_text import safe_external_url
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.content_project_detail import ContentProjectDetailPanel
from src.gui.window_sizing import resize_dialog_to_screen


class ModrinthBrowserDialog(QDialog):
    search_requested = Signal(str, str, str, int, str)
    versions_requested = Signal(str, str, str, str)
    project_details_requested = Signal(str, str, str)
    install_mod_requested = Signal(str, str)
    install_modpack_requested = Signal(str, str, str, bool, object, str)
    channel_preferences_changed = Signal(bool, bool)

    PAGE_SIZE = 25

    def __init__(self, project_type: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ModrinthDialog")
        self.project_type = project_type
        self._instance: Instance | None = None
        self._result: ModrinthSearchResult | None = None
        self._projects: list[ModrinthProject] = []
        self._all_versions: list[ModrinthVersion] = []
        self._versions: list[ModrinthVersion] = []
        self._selected_project: ModrinthProject | None = None
        self._offset = 0
        self._suggested_instance_name = ""
        self._instance_name_customized = False
        self._pending_channel_preferences = (False, False)
        self._image_cache = RemoteImageCache(self)
        self._channel_change_timer = QTimer(self)
        self._channel_change_timer.setSingleShot(True)
        self._channel_change_timer.setInterval(25)
        self._channel_change_timer.timeout.connect(self._apply_queued_channel_change)
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 1120, 720, 900, 560)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        self.context_label = QLabel()
        self.context_label.setObjectName("MutedLabel")
        self.context_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.context_label)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self._request_search)
        self.loader_label = QLabel()
        self.loader_label.setObjectName("MutedLabel")
        self.loader_combo = QComboBox()
        self.loader_combo.addItem("Fabric", ModLoaderManager.FABRIC)
        self.loader_combo.addItem("Quilt", ModLoaderManager.QUILT)
        self.loader_combo.addItem("Forge", ModLoaderManager.FORGE)
        self.loader_combo.addItem("NeoForge", ModLoaderManager.NEOFORGE)
        self.loader_combo.currentIndexChanged.connect(self._loader_changed)
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Relevance", "relevance")
        self.sort_combo.addItem("Downloads", "downloads")
        self.sort_combo.addItem("Recently updated", "updated")
        self.sort_combo.addItem("Newest", "newest")
        self.search_button = set_theme_icon(QPushButton(), "icon.action.search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self._request_search)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.loader_label)
        search_row.addWidget(self.loader_combo)
        search_row.addWidget(self.sort_combo)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        channel_row = QHBoxLayout()
        self.release_channel_label = QLabel("Release channel: Release is always enabled")
        self.release_channel_label.setObjectName("MutedLabel")
        self.include_beta_checkbox = QCheckBox("Beta")
        self.include_alpha_checkbox = QCheckBox("Alpha")
        self.include_beta_checkbox.toggled.connect(self._channels_changed)
        self.include_alpha_checkbox.toggled.connect(self._channels_changed)
        channel_row.addWidget(self.release_channel_label)
        channel_row.addStretch()
        channel_row.addWidget(self.include_beta_checkbox)
        channel_row.addWidget(self.include_alpha_checkbox)
        root.addLayout(channel_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(8)

        self.results_table = QTableWidget(0, 5)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setIconSize(QSize(40, 40))
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.verticalHeader().setDefaultSectionSize(52)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.results_table.itemSelectionChanged.connect(self._project_selected)
        results_layout.addWidget(self.results_table, 1)

        page_row = QHBoxLayout()
        self.result_count_label = QLabel()
        self.result_count_label.setObjectName("MutedLabel")
        self.previous_button = set_theme_icon(QPushButton(), "icon.action.previous")
        self.next_button = set_theme_icon(QPushButton(), "icon.action.next")
        self.previous_button.clicked.connect(self._previous_page)
        self.next_button.clicked.connect(self._next_page)
        page_row.addWidget(self.result_count_label)
        page_row.addStretch()
        page_row.addWidget(self.previous_button)
        page_row.addWidget(self.next_button)
        results_layout.addLayout(page_row)

        self.detail_panel = ContentProjectDetailPanel(self._image_cache)
        self.open_browser_button = self.detail_panel.open_web_button
        self.details_label = self.detail_panel.status_label

        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self._version_selected)
        self.instance_name_input = QLineEdit()
        self.instance_name_input.textEdited.connect(self._instance_name_edited)
        self.optional_checkbox = QCheckBox()
        self.optional_checkbox.setChecked(True)
        self.install_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._request_install)
        self.detail_panel.add_action_widget(self.version_combo, 2)
        if self.project_type == "modpack":
            self.detail_panel.add_action_widget(self.instance_name_input, 2)
            self.detail_panel.add_action_widget(self.optional_checkbox)
        self.detail_panel.add_action_widget(self.install_button)

        splitter.addWidget(results_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([650, 430])
        root.addWidget(splitter, 1)

    @property
    def game_version(self) -> str:
        return self._instance.version_id if self._instance is not None else ""

    @property
    def selected_loader(self) -> str:
        loader = str(self.loader_combo.currentData() or ModLoaderManager.FABRIC).strip().lower()
        return loader if loader in ModLoaderManager.MODDED_LOADERS else ModLoaderManager.FABRIC

    @property
    def allowed_version_types(self) -> tuple[str, ...]:
        values = ["release"]
        if self.include_beta_checkbox.isChecked():
            values.append("beta")
        if self.include_alpha_checkbox.isChecked():
            values.append("alpha")
        return tuple(values)

    def set_channel_preferences(self, include_beta: bool, include_alpha: bool) -> None:
        self.include_beta_checkbox.blockSignals(True)
        self.include_alpha_checkbox.blockSignals(True)
        self.include_beta_checkbox.setChecked(bool(include_beta))
        self.include_alpha_checkbox.setChecked(bool(include_alpha))
        self.include_beta_checkbox.blockSignals(False)
        self.include_alpha_checkbox.blockSignals(False)
        self._apply_version_filter()

    def set_searching(self, loader: str = "") -> None:
        if loader and str(loader).strip().lower() != self.selected_loader:
            return
        self._result = None
        self._projects = []
        self.results_table.clearSelection()
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.result_count_label.setText(tr("modrinth.results.searching"))
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self._clear_project_selection(tr("modrinth.results.contacting"))

    def set_search_error(self, loader: str, message: str) -> None:
        if loader and str(loader).strip().lower() != self.selected_loader:
            return
        self._result = None
        self._projects = []
        self.results_table.clearSelection()
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.result_count_label.setText(tr("modrinth.results.failed"))
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self._clear_project_selection(tr("modrinth.results.error", error=str(message)))

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._offset = 0
        self._result = None
        self._projects = []
        self._all_versions = []
        self._versions = []
        self._selected_project = None
        self._suggested_instance_name = ""
        self._instance_name_customized = False
        if self.project_type == "modpack":
            self.instance_name_input.clear()
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader) if instance is not None else (ModLoaderManager.FABRIC, "")
        selected_loader = loader_name if loader_name in ModLoaderManager.MODDED_LOADERS else ModLoaderManager.FABRIC
        loader_index = self.loader_combo.findData(selected_loader)
        self.loader_combo.blockSignals(True)
        self.loader_combo.setCurrentIndex(max(0, loader_index))
        self.loader_combo.blockSignals(False)
        self.results_table.setRowCount(0)
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self._clear_project_selection(tr("modrinth.results.ready"))
        self.retranslate_dynamic()

    def set_search_result(self, result: ModrinthSearchResult, loader: str = "") -> None:
        if loader and str(loader).strip().lower() != self.selected_loader:
            return
        self._result = result
        self._projects = list(result.projects)
        self._offset = result.offset

        # QTableWidget may preserve row 0 as the current selection while its
        # contents are replaced. In that case selectRow(0) does not emit
        # itemSelectionChanged, leaving versions and the suggested pack name
        # stale until the user clicks the row again. Rebuild the table with
        # signals blocked, then activate the first result explicitly once.
        signals_were_blocked = self.results_table.blockSignals(True)
        try:
            self.results_table.clearSelection()
            self.results_table.clearContents()
            self.results_table.setRowCount(len(self._projects))
            headers = [tr("modrinth.column.name"), tr("modrinth.column.author"), tr("modrinth.column.downloads"), tr("modrinth.column.updated"), tr("modrinth.column.description")]
            self.results_table.setHorizontalHeaderLabels(headers)
            for row, project in enumerate(self._projects):
                values = [project.title, project.author or tr("common.unknown"), f"{project.downloads:,}", project.date_modified[:10], project.description]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.ItemDataRole.UserRole, project)
                    self.results_table.setItem(row, column, item)
                self._request_row_icon(row, project)
            if self._projects:
                self.results_table.selectRow(0)
        finally:
            self.results_table.blockSignals(signals_were_blocked)

        start = result.offset + 1 if result.projects else 0
        end = result.offset + len(result.projects)
        self.result_count_label.setText(tr("modrinth.results.range", start=start, end=end, total=result.total_hits))
        self.previous_button.setEnabled(result.offset > 0)
        self.next_button.setEnabled(result.offset + result.limit < result.total_hits)
        if self._projects:
            self._select_project(self._projects[0])
        else:
            self._clear_project_selection(tr("modrinth.results.empty"))

    def set_versions(self, project_id: str, versions: list[ModrinthVersion], loader: str = "") -> None:
        if loader and str(loader).strip().lower() != self.selected_loader:
            return
        if self._selected_project is None or self._selected_project.project_id != project_id:
            return
        self._all_versions = list(versions)
        self._apply_version_filter()

    def set_project_details(self, project_type: str, project_id: str, loader: str, project: ModrinthProject) -> None:
        if project_type != self.project_type or str(loader).strip().casefold() != self.selected_loader:
            return
        current = self._selected_project
        if current is None or current.project_id != str(project_id) or project.project_id != current.project_id:
            return
        self._selected_project = replace(
            project,
            author=project.author or current.author,
            downloads=project.downloads or current.downloads,
            description=project.description or current.description,
            icon_url=project.icon_url or current.icon_url,
            date_modified=project.date_modified or current.date_modified,
            categories=project.categories or current.categories,
            versions=project.versions or current.versions,
            loaders=project.loaders or current.loaders,
        )
        self._render_project_details(self._selected_project)
        if self._versions:
            self._version_selected()

    def set_busy(self, busy: bool) -> None:
        self.search_button.setEnabled(not busy)
        self.results_table.setEnabled(not busy)
        self.version_combo.setEnabled(not busy)
        self.loader_combo.setEnabled(not busy)
        self.include_beta_checkbox.setEnabled(not busy)
        self.include_alpha_checkbox.setEnabled(not busy)
        self.install_button.setEnabled(not busy and bool(self._versions))
        self.previous_button.setEnabled(not busy and self._result is not None and self._result.offset > 0)
        self.next_button.setEnabled(not busy and self._result is not None and self._result.offset + self._result.limit < self._result.total_hits)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _apply_version_filter(self) -> None:
        self._update_channel_summary()
        allowed = set(self.allowed_version_types)
        self._versions = [version for version in self._all_versions if version.version_type in allowed and self.selected_loader in {str(loader).strip().lower() for loader in version.loaders}]
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for version in self._versions:
            game_text = ", ".join(version.game_versions[:3])
            if len(version.game_versions) > 3:
                game_text += ", …"
            label = f"{version.version_number} • {version.version_type} • Minecraft {game_text}"
            self.version_combo.addItem(label, version.version_id)
        self.version_combo.blockSignals(False)
        self.install_button.setEnabled(bool(self._versions))
        if self._versions:
            self._version_selected()
        elif self._selected_project is not None:
            channels = ", ".join(item.title() for item in self.allowed_version_types)
            self.details_label.setText(tr("modrinth.channel.no_versions", channels=channels))

    def _update_channel_summary(self) -> None:
        if not self._all_versions:
            self.release_channel_label.setText(tr("modrinth.channel.release_always"))
            return
        counts = {"release": 0, "beta": 0, "alpha": 0}
        for version in self._all_versions:
            if version.version_type in counts:
                counts[version.version_type] += 1
        self.release_channel_label.setText(tr("modrinth.channel.summary", release=counts["release"], beta=counts["beta"], alpha=counts["alpha"]))

    def _channels_changed(self, _checked: bool) -> None:
        self._pending_channel_preferences = (
            self.include_beta_checkbox.isChecked(),
            self.include_alpha_checkbox.isChecked(),
        )
        self._channel_change_timer.start()

    def _apply_queued_channel_change(self) -> None:
        include_beta, include_alpha = self._pending_channel_preferences
        self._apply_version_filter()
        self.channel_preferences_changed.emit(include_beta, include_alpha)

    def _loader_changed(self, _index: int) -> None:
        self._offset = 0
        self._result = None
        self._projects = []
        self.results_table.setRowCount(0)
        self._clear_project_selection(tr("modrinth.results.ready"))
        self.retranslate_dynamic()
        if self.isVisible():
            self._request_search()

    def _request_search(self) -> None:
        if self.project_type == "mod" and self._instance is None:
            QMessageBox.information(self, tr("modrinth.title"), tr("modrinth.mod.no_instance"))
            return
        self._offset = 0
        self.set_searching(self.selected_loader)
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset, self.selected_loader)

    def _project_selected(self) -> None:
        rows = self.results_table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.results_table.item(rows[0].row(), 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if isinstance(project, ModrinthProject):
            self._select_project(project)

    def _select_project(self, project: ModrinthProject) -> None:
        self._selected_project = project
        self._all_versions = []
        self._versions = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        if self.project_type == "modpack" and (not self._instance_name_customized or not self.instance_name_input.text().strip() or self.instance_name_input.text() == self._suggested_instance_name):
            self._suggested_instance_name = InstanceManager.next_available_name(self._safe_instance_name(project.title))
            self.instance_name_input.setText(self._suggested_instance_name)
            self._instance_name_customized = False
        game_version = self._instance.version_id if self.project_type == "mod" and self._instance is not None else ""
        message = tr("modrinth.project.loading_versions", title=project.title)
        self.detail_panel.set_loading(project.project_id, "Modrinth", project.title, project.author or tr("common.unknown"), project.description, project.icon_url, project.project_url or self._project_web_url(project), message)
        self.project_details_requested.emit(self.project_type, project.project_id, self.selected_loader)
        self.versions_requested.emit(self.project_type, project.project_id, game_version, self.selected_loader)

    def _clear_project_selection(self, message: str) -> None:
        self._selected_project = None
        self._all_versions = []
        self._versions = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        if self.project_type == "modpack" and not self._instance_name_customized:
            self._suggested_instance_name = ""
            self.instance_name_input.clear()
        self.detail_panel.clear(message)

    def _version_selected(self) -> None:
        version = self._selected_version()
        project = self._selected_project
        if version is None or project is None:
            return
        primary = next((file for file in version.files if file.primary), version.files[0] if version.files else None)
        size_text = self._format_bytes(primary.size) if primary is not None else tr("common.unknown")
        dependencies = sum(1 for dependency in version.dependencies if dependency.dependency_type == "required")
        self.detail_panel.set_status(tr("content.details.version_status", version=version.version_number, channel=version.version_type.title(), size=size_text, dependencies=dependencies))

    def _render_project_details(self, project: ModrinthProject) -> None:
        metadata = {
            tr("content.metadata.downloads"): f"{project.downloads:,}",
            tr("content.metadata.followers"): f"{project.followers:,}" if project.followers else "",
            tr("content.metadata.updated"): project.date_modified[:10],
            tr("content.metadata.published"): project.date_published[:10],
            tr("content.metadata.license"): project.license_name or project.license_id,
            tr("content.metadata.minecraft"): project.versions[:8],
            tr("content.metadata.loaders"): project.loaders or tuple(item for item in project.categories if item.casefold() in ModLoaderManager.MODDED_LOADERS),
            tr("content.metadata.categories"): project.categories[:8],
            tr("content.metadata.client"): project.client_side.title(),
            tr("content.metadata.server"): project.server_side.title(),
        }
        links = [
            (tr("content.link.source"), safe_external_url(project.source_url)),
            (tr("content.link.issues"), safe_external_url(project.issues_url)),
            (tr("content.link.wiki"), safe_external_url(project.wiki_url)),
            (tr("content.link.discord"), safe_external_url(project.discord_url)),
        ]
        link_text = " · ".join(f'<a href="{url}">{label}</a>' for label, url in links if url)
        description = project.body or project.description
        if link_text:
            description = f"{description}\n\n{link_text}"
        self.detail_panel.set_project(
            token=project.project_id,
            provider="Modrinth",
            title=project.title,
            author=project.author or tr("common.unknown"),
            summary=project.description,
            description=description,
            icon_url=project.icon_url,
            web_url=project.project_url or self._project_web_url(project),
            metadata=metadata,
            gallery_urls=project.gallery_urls,
            description_format="markdown",
            status=self.details_label.text(),
        )

    def _request_row_icon(self, row: int, project: ModrinthProject) -> None:
        self._image_cache.request(project.icon_url, lambda pixmap, row=row, project_id=project.project_id: self._apply_row_icon(row, project_id, pixmap))

    def _apply_row_icon(self, row: int, project_id: str, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return
        item = self.results_table.item(row, 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if isinstance(project, ModrinthProject) and project.project_id == project_id:
            item.setIcon(QIcon(self._image_cache.scaled(pixmap, QSize(40, 40))))

    @staticmethod
    def _project_web_url(project: ModrinthProject) -> str:
        kind = project.project_type if project.project_type in {"mod", "modpack"} else "mod"
        return f"https://modrinth.com/{kind}/{project.slug}" if project.slug else ""

    @staticmethod
    def _format_bytes(value: int) -> str:
        size = max(0, int(value))
        for unit in ("B", "KiB", "MiB", "GiB"):
            if size < 1024 or unit == "GiB":
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} GiB"

    def _instance_name_edited(self, text: str) -> None:
        self._instance_name_customized = bool(text.strip()) and text != self._suggested_instance_name

    def _request_install(self) -> None:
        version = self._selected_version()
        project = self._selected_project
        if version is None or project is None:
            return
        if self.project_type == "mod":
            if self._instance is not None:
                instance_loader, _ = ModLoaderManager.normalize(self._instance.mod_loader)
                if instance_loader != self.selected_loader:
                    QMessageBox.information(self, tr("modrinth.title"), tr("modrinth.loader.instance_mismatch", instance_loader=instance_loader.title(), selected_loader=self.selected_loader.title()))
                    return
            self.install_mod_requested.emit(version.version_id, self.selected_loader)
            return
        name = self.instance_name_input.text().strip()
        self.install_modpack_requested.emit(project.project_id, version.version_id, name, self.optional_checkbox.isChecked(), self.allowed_version_types, self.selected_loader)

    def _selected_version(self) -> ModrinthVersion | None:
        index = self.version_combo.currentIndex()
        if index < 0 or index >= len(self._versions):
            return None
        version_id = str(self.version_combo.currentData() or "")
        return next((version for version in self._versions if version.version_id == version_id), None)

    def _previous_page(self) -> None:
        self._offset = max(0, self._offset - self.PAGE_SIZE)
        self.set_searching(self.selected_loader)
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset, self.selected_loader)

    def _next_page(self) -> None:
        self._offset += self.PAGE_SIZE
        self.set_searching(self.selected_loader)
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset, self.selected_loader)

    @staticmethod
    def _safe_instance_name(value: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", str(value)).strip().rstrip(". ")
        return cleaned[:80] or "Modrinth Modpack"

    def retranslate_dynamic(self) -> None:
        is_mod = self.project_type == "mod"
        self.setWindowTitle(tr("modrinth.mod.title" if is_mod else "modrinth.modpack.title"))
        self.title_label.setText(tr("modrinth.mod.title" if is_mod else "modrinth.modpack.title"))
        if is_mod:
            if self._instance is None:
                self.context_label.setText(tr("modrinth.mod.context.none"))
            else:
                self.context_label.setText(tr("modrinth.mod.context", instance=self._instance.name, minecraft=self._instance.version_id, loader=self.selected_loader.title()))
        else:
            self.context_label.setText(tr("modrinth.modpack.context", loader=self.selected_loader.title()))
        self._update_channel_summary()
        self.include_beta_checkbox.setText(tr("modrinth.channel.beta"))
        self.include_alpha_checkbox.setText(tr("modrinth.channel.alpha"))
        self.search_input.setPlaceholderText(tr("modrinth.search.placeholder"))
        self.search_button.setText(tr("common.search"))
        self.previous_button.setText(tr("common.previous"))
        self.next_button.setText(tr("common.next"))
        self.detail_panel.set_open_web_text(tr("content.open_web"))
        self.install_button.setText(tr("modrinth.mod.install" if is_mod else "modrinth.modpack.install"))
        self.instance_name_input.setPlaceholderText(tr("modrinth.modpack.instance_name"))
        self.optional_checkbox.setText(tr("modrinth.modpack.optional_files"))
        self.loader_label.setText(tr("modrinth.loader.label"))
        self.loader_combo.setItemText(0, tr("modrinth.loader.fabric"))
        self.loader_combo.setItemText(1, tr("modrinth.loader.quilt"))
        self.loader_combo.setItemText(2, tr("modrinth.loader.forge"))
        self.loader_combo.setItemText(3, tr("modrinth.loader.neoforge"))
        self.loader_combo.setToolTip(tr("modrinth.loader.help"))
        self.sort_combo.setItemText(0, tr("modrinth.sort.relevance"))
        self.sort_combo.setItemText(1, tr("modrinth.sort.downloads"))
        self.sort_combo.setItemText(2, tr("modrinth.sort.updated"))
        self.sort_combo.setItemText(3, tr("modrinth.sort.newest"))
        if self._result is None:
            self.result_count_label.setText(tr("modrinth.results.ready"))
        else:
            start = self._result.offset + 1 if self._result.projects else 0
            end = self._result.offset + len(self._result.projects)
            self.result_count_label.setText(tr("modrinth.results.range", start=start, end=end, total=self._result.total_hits))
        self.results_table.setHorizontalHeaderLabels([tr("modrinth.column.name"), tr("modrinth.column.author"), tr("modrinth.column.downloads"), tr("modrinth.column.updated"), tr("modrinth.column.description")])
