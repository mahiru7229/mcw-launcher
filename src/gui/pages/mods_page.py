from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from PySide6.QtCore import QSize, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from mcw_core.api.curseforge.curseforge_client import CurseForgeClient
from mcw_core.api.language.language_manager import tr
from mcw_core.api.modloader.mod_loader_manager import ModLoaderManager
from src.gui.media.remote_image_cache import RemoteImageCache
from src.gui.media.safe_rich_text import safe_external_url, sanitize_html
from src.gui.pages.base_page import BasePage
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget
from src.gui.widget.content_project_detail import ContentProjectDetailPanel
from src.models.curseforge.cache import CurseForgeCacheInfo
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.project import CurseForgeProject, CurseForgeSearchResult
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthVersion


class ModsPage(BasePage):
    search_requested = Signal(str, str, int, str)
    versions_requested = Signal(str, str)
    project_details_requested = Signal(str, str)
    install_requested = Signal(object, str, object)
    curseforge_search_requested = Signal(str, str, int, str)
    curseforge_refresh_requested = Signal(str, str, int, str)
    curseforge_files_requested = Signal(int, str, object)
    curseforge_project_details_requested = Signal(int, str)
    curseforge_files_refresh_requested = Signal(int, str, object)
    curseforge_clear_cache_requested = Signal()
    curseforge_install_requested = Signal(object, str, object)
    channel_preferences_changed = Signal(bool, bool)

    PAGE_SIZE = 25

    def __init__(self) -> None:
        super().__init__(tr("mods.title"), tr("mods.subtitle"), "mods")
        self._result: ModrinthSearchResult | CurseForgeSearchResult | None = None
        self._projects: list[ModrinthProject | CurseForgeProject] = []
        self._all_versions: list[ModrinthVersion] = []
        self._versions: list[ModrinthVersion] = []
        self._curseforge_files: list[CurseForgeFile] = []
        self._selected_project: ModrinthProject | CurseForgeProject | None = None
        self._offset = 0
        self._busy = False
        self._refresh_files_after_search = False
        self._pending_channel_preferences = (False, False)
        self._cache_info = CurseForgeClient.api_cache_status()
        self._image_cache = RemoteImageCache(self)

        self._channel_change_timer = QTimer(self)
        self._channel_change_timer.setSingleShot(True)
        self._channel_change_timer.setInterval(60)
        self._channel_change_timer.timeout.connect(self._apply_queued_channel_change)

        self._cooldown_timer = QTimer(self)
        self._cooldown_timer.setInterval(1000)
        self._cooldown_timer.timeout.connect(self._render_cache_status)
        self._cooldown_timer.start()

        self._build_ui()
        self.retranslate_dynamic()
        self.set_curseforge_cache_info(self._cache_info)

    def _build_ui(self) -> None:
        selector_card = CardWidget(tr("mods.catalog.selector.title"), tr("mods.catalog.selector.subtitle"))
        selector_grid = QGridLayout()
        selector_grid.setHorizontalSpacing(12)
        selector_grid.setVerticalSpacing(10)
        selector_grid.setColumnStretch(1, 1)

        self.provider_label = QLabel()
        self.provider_label.setObjectName("MutedLabel")
        self.provider_combo = QComboBox()
        self.provider_combo.addItem(tr("mods.catalog.provider.modrinth"), "modrinth")
        self.provider_combo.addItem(tr("mods.catalog.provider.curseforge"), "curseforge")
        self.provider_combo.currentIndexChanged.connect(self._provider_changed)

        self.loader_label = QLabel()
        self.loader_label.setObjectName("MutedLabel")
        self.loader_combo = QComboBox()
        self.loader_combo.addItem("Fabric", ModLoaderManager.FABRIC)
        self.loader_combo.addItem("Quilt", ModLoaderManager.QUILT)
        self.loader_combo.addItem("Forge", ModLoaderManager.FORGE)
        self.loader_combo.addItem("NeoForge", ModLoaderManager.NEOFORGE)
        self.loader_combo.currentIndexChanged.connect(self._loader_changed)

        selector_grid.addWidget(self.provider_label, 0, 0)
        selector_grid.addWidget(self.provider_combo, 0, 1)
        selector_grid.addWidget(self.loader_label, 1, 0)
        selector_grid.addWidget(self.loader_combo, 1, 1)
        selector_card.layout.addLayout(selector_grid)

        browser_card = CardWidget("")
        self.browser_card = browser_card
        self.catalog_title_label = QLabel()
        self.catalog_title_label.setObjectName("CardTitle")
        self.catalog_subtitle_label = QLabel()
        self.catalog_subtitle_label.setObjectName("CardSubtitle")
        self.catalog_subtitle_label.setWordWrap(True)
        browser_card.layout.addWidget(self.catalog_title_label)
        browser_card.layout.addWidget(self.catalog_subtitle_label)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self._request_search)

        self.sort_combo = QComboBox()

        self.search_button = set_theme_icon(QPushButton(tr("common.search")), "icon.action.search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self._request_search)

        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.sort_combo)
        search_row.addWidget(self.search_button)
        browser_card.layout.addLayout(search_row)

        cache_row = QHBoxLayout()
        self.cache_status_label = QLabel()
        self.cache_status_label.setObjectName("MutedLabel")
        self.cache_status_label.setWordWrap(True)
        self.refresh_button = set_theme_icon(QPushButton(), "icon.action.refresh")
        self.refresh_button.clicked.connect(self._request_refresh)
        self.clear_cache_button = QPushButton()
        self.clear_cache_button.clicked.connect(self._request_clear_cache)
        cache_row.addWidget(self.cache_status_label, 1)
        cache_row.addWidget(self.refresh_button)
        cache_row.addWidget(self.clear_cache_button)
        browser_card.layout.addLayout(cache_row)

        channel_row = QHBoxLayout()
        self.release_channel_label = QLabel()
        self.release_channel_label.setObjectName("MutedLabel")
        self.release_channel_label.setWordWrap(True)
        self.include_beta_checkbox = QCheckBox()
        self.include_alpha_checkbox = QCheckBox()
        self.include_beta_checkbox.toggled.connect(self._channels_changed)
        self.include_alpha_checkbox.toggled.connect(self._channels_changed)
        channel_row.addWidget(self.release_channel_label, 1)
        channel_row.addWidget(self.include_beta_checkbox)
        channel_row.addWidget(self.include_alpha_checkbox)
        browser_card.layout.addLayout(channel_row)

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
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.results_table.itemSelectionChanged.connect(self._project_selected)
        self.results_table.setMinimumHeight(320)
        results_layout.addWidget(self.results_table, 1)

        page_row = QHBoxLayout()
        self.result_count_label = QLabel()
        self.result_count_label.setObjectName("MutedLabel")
        self.previous_button = set_theme_icon(QPushButton(), "icon.action.previous")
        self.next_button = set_theme_icon(QPushButton(), "icon.action.next")
        self.previous_button.clicked.connect(self._previous_page)
        self.next_button.clicked.connect(self._next_page)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        page_row.addWidget(self.result_count_label)
        page_row.addStretch()
        page_row.addWidget(self.previous_button)
        page_row.addWidget(self.next_button)
        results_layout.addLayout(page_row)

        self.detail_panel = ContentProjectDetailPanel(self._image_cache)
        self.details_label = self.detail_panel.status_label
        self.open_browser_button = self.detail_panel.open_web_button
        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self._version_selected)
        self.install_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._request_install)
        self.detail_panel.add_action_widget(self.version_combo, 1)
        self.detail_panel.add_action_widget(self.install_button)

        splitter.addWidget(results_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([720, 480])
        browser_card.layout.addWidget(splitter, 1)

        self.root_layout.addWidget(selector_card)
        self.root_layout.addWidget(browser_card)
        self.root_layout.addStretch()

    @property
    def has_loaded_search(self) -> bool:
        return self._result is not None or bool(self._projects)

    @property
    def selected_provider(self) -> str:
        provider = str(self.provider_combo.currentData() or "modrinth").strip().lower()
        return provider if provider in {"modrinth", "curseforge"} else "modrinth"

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
        if self.selected_provider == "modrinth":
            self._apply_modrinth_version_filter()
        if not self._busy:
            self.include_beta_checkbox.setEnabled(True)
            self.include_alpha_checkbox.setEnabled(True)

    def set_show_project_descriptions(self, visible: bool) -> None:
        self.detail_panel.set_description_visible(visible)

    def set_searching(self, loader: str = "", provider: str = "modrinth") -> None:
        if str(provider).strip().lower() != self.selected_provider:
            return
        if loader and str(loader).strip().lower() != self.selected_loader:
            return
        self._clear_search_state()
        if self.selected_provider == "curseforge":
            self.result_count_label.setText(tr("mods.catalog.curseforge.searching"))
            self._clear_project_selection(tr("mods.catalog.curseforge.contacting"))
        else:
            self.result_count_label.setText(tr("modrinth.results.searching"))
            self._clear_project_selection(tr("modrinth.results.contacting"))

    def set_search_error(self, loader: str, message: str) -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        self._clear_search_state()
        self.result_count_label.setText(tr("modrinth.results.failed"))
        self._clear_project_selection(tr("modrinth.results.error", error=str(message)))

    def set_curseforge_search_error(self, loader: str, message: str) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        self._clear_search_state()
        self.result_count_label.setText(tr("mods.catalog.curseforge.failed"))
        self._clear_project_selection(tr("mods.catalog.curseforge.error", error=str(message)))

    def set_curseforge_files_error(self, project_id: int, loader: str, message: str) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        if not isinstance(self._selected_project, CurseForgeProject) or self._selected_project.project_id != int(project_id):
            return
        self._curseforge_files = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.details_label.setText(tr("mods.catalog.version_error", error=str(message)))

    def set_search_result(self, result: ModrinthSearchResult, loader: str = "") -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        self._result = result
        self._projects = list(result.projects)
        self._offset = result.offset
        self._render_project_rows()
        start = result.offset + 1 if result.projects else 0
        end = result.offset + len(result.projects)
        self.result_count_label.setText(tr("modrinth.results.range", start=start, end=end, total=result.total_hits))
        self.previous_button.setEnabled(not self._busy and result.offset > 0)
        self.next_button.setEnabled(not self._busy and result.offset + result.limit < result.total_hits)
        self._select_first_project_or_show_empty(tr("modrinth.results.empty"))

    def set_curseforge_search_result(self, loader: str, result: CurseForgeSearchResult) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        self._result = result
        self._projects = list(result.projects)
        self._offset = result.index
        self.set_curseforge_cache_info(result.cache_info)
        self._render_project_rows()
        start = result.index + 1 if result.projects else 0
        end = result.index + len(result.projects)
        self.result_count_label.setText(tr("curseforge.results.range", start=start, end=end, total=result.total_count))
        self.previous_button.setEnabled(not self._busy and result.index > 0)
        self.next_button.setEnabled(not self._busy and result.index + result.page_size < result.total_count)
        self._select_first_project_or_show_empty(tr("curseforge.results.empty"))

    def set_modrinth_project_details(self, project_id: str, loader: str, project: ModrinthProject) -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().casefold() != self.selected_loader):
            return
        current = self._selected_project
        if not isinstance(current, ModrinthProject) or current.project_id != str(project_id) or project.project_id != current.project_id:
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
        self._render_modrinth_details(self._selected_project)
        if self._versions:
            self._version_selected()

    def set_curseforge_project_details(self, project_id: int, loader: str, project: CurseForgeProject) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().casefold() != self.selected_loader):
            return
        current = self._selected_project
        if not isinstance(current, CurseForgeProject) or current.project_id != int(project_id) or project.project_id != current.project_id:
            return
        self._selected_project = replace(
            project,
            authors=project.authors or current.authors,
            summary=project.summary or current.summary,
            download_count=project.download_count or current.download_count,
            logo_url=project.logo_url or current.logo_url,
            project_url=project.project_url or current.project_url,
            game_versions=project.game_versions or current.game_versions,
            loaders=project.loaders or current.loaders,
            date_modified=project.date_modified or current.date_modified,
        )
        self._render_curseforge_details(self._selected_project)
        if self._curseforge_files:
            self._version_selected()

    def set_versions(self, project_id: str, versions: list[ModrinthVersion], loader: str = "") -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        if not isinstance(self._selected_project, ModrinthProject) or self._selected_project.project_id != project_id:
            return
        self._all_versions = list(versions)
        self._apply_modrinth_version_filter()

    def set_versions_error(self, project_id: str, loader: str, message: str) -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        if not isinstance(self._selected_project, ModrinthProject) or self._selected_project.project_id != project_id:
            return
        self._all_versions = []
        self._versions = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.details_label.setText(tr("mods.catalog.version_error", error=str(message)))

    def set_curseforge_files(self, project_id: int, loader: str, files: list[CurseForgeFile]) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        if not isinstance(self._selected_project, CurseForgeProject) or self._selected_project.project_id != int(project_id):
            return
        self._curseforge_files = list(files)
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for file in self._curseforge_files:
            games = ", ".join(file.game_versions[:4]) or tr("common.unknown")
            if len(file.game_versions) > 4:
                games += ", …"
            loader_status = self._curseforge_loader_status_text(file)
            self.version_combo.addItem(f"{file.display_name} • {file.release_type} • {loader_status} • Minecraft {games}", file.file_id)
        self.version_combo.blockSignals(False)
        self.install_button.setEnabled(not self._busy and bool(self._curseforge_files))
        self._update_channel_summary()
        if self._curseforge_files:
            self._version_selected()
        else:
            channels = ", ".join(value.title() for value in self.allowed_version_types)
            self.details_label.setText(tr("curseforge.files.none_for_loader", loader=self.selected_loader.title(), channels=channels))

    def set_curseforge_cache_info(self, info: CurseForgeCacheInfo) -> None:
        if isinstance(info, CurseForgeCacheInfo):
            self._cache_info = info
        self._render_cache_status()

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self.set_interaction_locked(self._busy)
        self.provider_combo.setEnabled(not self._busy)
        self.loader_combo.setEnabled(not self._busy)
        self.search_input.setEnabled(not self._busy)
        self.search_button.setEnabled(not self._busy)
        self.results_table.setEnabled(not self._busy)
        self.version_combo.setEnabled(not self._busy)
        self.sort_combo.setEnabled(not self._busy)
        self.include_beta_checkbox.setEnabled(not self._busy)
        self.include_alpha_checkbox.setEnabled(not self._busy)
        self.clear_cache_button.setEnabled(not self._busy)
        self.open_browser_button.setEnabled(not self._busy and self._has_selected_project_url())
        self.install_button.setEnabled(not self._busy and self._has_installable_items())
        self._update_pagination_buttons()
        self._render_cache_status()

    def start_search(self) -> None:
        if self.selected_provider == "modrinth":
            self._request_search()

    def _request_search(self) -> None:
        self._offset = 0
        if self.selected_provider == "curseforge":
            if not self.search_input.text().strip():
                self.result_count_label.setText(tr("curseforge.results.ready"))
                self._clear_project_selection(tr("curseforge.search.required"))
                return
            self._refresh_files_after_search = False
            self.set_searching(self.selected_loader, "curseforge")
            self.search_button.setEnabled(False)
            self._commit_feedback(self.search_button, self.result_count_label, self.details_label)
            request = (self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._offset, self.selected_loader)
            QTimer.singleShot(0, lambda values=request: self.curseforge_search_requested.emit(*values))
            return
        self.set_searching(self.selected_loader, "modrinth")
        self.search_button.setEnabled(False)
        self._commit_feedback(self.search_button, self.result_count_label, self.details_label)
        request = (self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset, self.selected_loader)
        QTimer.singleShot(0, lambda values=request: self.search_requested.emit(*values))

    def _request_refresh(self) -> None:
        if self.selected_provider != "curseforge":
            return
        if not self.search_input.text().strip():
            self.result_count_label.setText(tr("curseforge.results.ready"))
            self._clear_project_selection(tr("curseforge.search.required"))
            return
        if CurseForgeClient.manual_refresh_remaining_seconds() > 0:
            self._render_cache_status()
            return
        self._refresh_files_after_search = True
        self.set_searching(self.selected_loader, "curseforge")
        self.refresh_button.setEnabled(False)
        self._commit_feedback(self.refresh_button, self.result_count_label, self.details_label)
        request = (self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._offset, self.selected_loader)
        QTimer.singleShot(0, lambda values=request: self.curseforge_refresh_requested.emit(*values))

    def _request_clear_cache(self) -> None:
        self.clear_cache_button.setEnabled(False)
        self.cache_status_label.setText(tr("content.cache.clearing"))
        self._commit_feedback(self.clear_cache_button, self.cache_status_label)
        QTimer.singleShot(0, self.curseforge_clear_cache_requested.emit)

    def _project_selected(self) -> None:
        rows = self.results_table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.results_table.item(rows[0].row(), 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if isinstance(project, (ModrinthProject, CurseForgeProject)):
            self._select_project(project)

    def _select_project(self, project: ModrinthProject | CurseForgeProject) -> None:
        self._selected_project = project
        self._all_versions = []
        self._versions = []
        self._curseforge_files = []
        self.version_combo.clear()
        self.open_browser_button.setEnabled(not self._busy and bool(self._project_web_url(project)))
        self.install_button.setEnabled(False)
        if isinstance(project, CurseForgeProject):
            message = tr("curseforge.project.loading_files", name=project.name)
            self.detail_panel.set_loading(str(project.project_id), "CurseForge", project.name, ", ".join(project.authors) or tr("common.unknown"), project.summary, project.logo_url, project.project_url, message)
            self.curseforge_project_details_requested.emit(project.project_id, self.selected_loader)
            if self._refresh_files_after_search:
                self._refresh_files_after_search = False
                self.curseforge_files_refresh_requested.emit(project.project_id, self.selected_loader, self.allowed_version_types)
            else:
                self.curseforge_files_requested.emit(project.project_id, self.selected_loader, self.allowed_version_types)
            return
        message = tr("modrinth.project.loading_versions", title=project.title)
        self.detail_panel.set_loading(project.project_id, "Modrinth", project.title, project.author or tr("common.unknown"), project.description, project.icon_url, project.project_url or self._project_web_url(project), message)
        self.project_details_requested.emit(project.project_id, self.selected_loader)
        self.versions_requested.emit(project.project_id, self.selected_loader)

    def _clear_project_selection(self, message: str) -> None:
        self._selected_project = None
        self._all_versions = []
        self._versions = []
        self._curseforge_files = []
        self.version_combo.clear()
        self.open_browser_button.setEnabled(False)
        self.install_button.setEnabled(False)
        self.detail_panel.clear(message)

    def _apply_modrinth_version_filter(self) -> None:
        self._update_channel_summary()
        allowed = set(self.allowed_version_types)
        loader = self.selected_loader
        self._versions = [version for version in self._all_versions if version.version_type in allowed and loader in {str(item).strip().lower() for item in version.loaders}]
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for version in self._versions:
            game_text = ", ".join(version.game_versions[:4])
            if len(version.game_versions) > 4:
                game_text += ", …"
            self.version_combo.addItem(f"{version.version_number} • {version.version_type} • Minecraft {game_text}", version.version_id)
        self.version_combo.blockSignals(False)
        self.install_button.setEnabled(not self._busy and bool(self._versions))
        if self._versions:
            self._version_selected()
        elif isinstance(self._selected_project, ModrinthProject):
            channels = ", ".join(item.title() for item in self.allowed_version_types)
            self.details_label.setText(tr("modrinth.channel.no_versions", channels=channels))

    def _update_channel_summary(self) -> None:
        if self.selected_provider == "curseforge":
            self.release_channel_label.setText(tr("curseforge.channel.release_always"))
            return
        if not self._all_versions:
            self.release_channel_label.setText(tr("modrinth.channel.release_always"))
            return
        counts = {"release": 0, "beta": 0, "alpha": 0}
        for version in self._all_versions:
            if version.version_type in counts:
                counts[version.version_type] += 1
        self.release_channel_label.setText(tr("modrinth.channel.summary", release=counts["release"], beta=counts["beta"], alpha=counts["alpha"]))

    def _version_selected(self) -> None:
        if self.selected_provider == "curseforge":
            file = self.selected_curseforge_file()
            project = self._selected_project
            if file is None or not isinstance(project, CurseForgeProject):
                return
            distribution = tr("curseforge.file.manual_required") if not file.download_url or not file.is_available else tr("curseforge.file.automatic")
            loader_status = self._curseforge_loader_status_text(file, detailed=True)
            dependencies = sum(1 for dependency in file.dependencies if dependency.required)
            self.detail_panel.set_status(tr("content.details.file_status", version=file.display_name, channel=file.release_type.title(), size=self._format_bytes(file.file_length), dependencies=dependencies, distribution=distribution, loader_status=loader_status))
            return
        version = self.selected_version()
        project = self._selected_project
        if version is None or not isinstance(project, ModrinthProject):
            return
        primary = next((file for file in version.files if file.primary), version.files[0] if version.files else None)
        size_text = self._format_bytes(primary.size) if primary is not None else tr("common.unknown")
        dependencies = sum(1 for dependency in version.dependencies if dependency.dependency_type == "required")
        self.detail_panel.set_status(tr("content.details.version_status", version=version.version_number, channel=version.version_type.title(), size=size_text, dependencies=dependencies))

    def _has_selected_project_url(self) -> bool:
        return bool(self._project_web_url(self._selected_project))

    def _open_selected_project(self) -> None:
        url = self._project_web_url(self._selected_project)
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _render_modrinth_details(self, project: ModrinthProject) -> None:
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

    def _render_curseforge_details(self, project: CurseForgeProject) -> None:
        metadata = {
            tr("content.metadata.downloads"): f"{project.download_count:,}",
            tr("content.metadata.updated"): project.date_modified[:10],
            tr("content.metadata.published"): project.date_created[:10],
            tr("content.metadata.released"): project.date_released[:10],
            tr("content.metadata.minecraft"): project.game_versions[:8],
            tr("content.metadata.loaders"): project.loaders,
            tr("content.metadata.categories"): project.categories[:8],
            tr("content.metadata.featured"): tr("common.yes") if project.is_featured else "",
        }
        links = [
            (tr("content.link.source"), safe_external_url(project.source_url)),
            (tr("content.link.issues"), safe_external_url(project.issues_url)),
            (tr("content.link.wiki"), safe_external_url(project.wiki_url)),
        ]
        links_html = " · ".join(f'<a href="{url}">{label}</a>' for label, url in links if url)
        description = sanitize_html(project.description) if project.description else ""
        if links_html:
            description = f"{description}<p>{links_html}</p>"
        self.detail_panel.set_project(
            token=str(project.project_id),
            provider="CurseForge",
            title=project.name,
            author=", ".join(project.authors) or tr("common.unknown"),
            summary=project.summary,
            description=description or project.summary,
            icon_url=project.logo_url,
            web_url=project.project_url,
            metadata=metadata,
            gallery_urls=project.screenshot_urls,
            description_format="html" if description else "plain",
            status=self.details_label.text(),
        )

    def _request_row_icon(self, row: int, project: ModrinthProject | CurseForgeProject) -> None:
        url = project.logo_url if isinstance(project, CurseForgeProject) else project.icon_url
        project_id = project.project_id
        self._image_cache.request(url, lambda pixmap, row=row, project_id=project_id: self._apply_row_icon(row, project_id, pixmap))

    def _apply_row_icon(self, row: int, project_id: object, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return
        item = self.results_table.item(row, 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if isinstance(project, (ModrinthProject, CurseForgeProject)) and project.project_id == project_id:
            item.setIcon(QIcon(self._image_cache.scaled(pixmap, QSize(40, 40))))

    @staticmethod
    def _project_web_url(project: ModrinthProject | CurseForgeProject | None) -> str:
        if isinstance(project, CurseForgeProject):
            return project.project_url
        if isinstance(project, ModrinthProject):
            if project.project_url:
                return project.project_url
            kind = project.project_type if project.project_type in {"mod", "modpack"} else "mod"
            return f"https://modrinth.com/{kind}/{project.slug}" if project.slug else ""
        return ""

    @staticmethod
    def _format_bytes(value: int) -> str:
        size = max(0, int(value))
        for unit in ("B", "KiB", "MiB", "GiB"):
            if size < 1024 or unit == "GiB":
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} GiB"

    def _curseforge_loader_status_text(self, file: CurseForgeFile, detailed: bool = False) -> str:
        status = CurseForgeClient.loader_compatibility(file, self.selected_loader)
        if status == "compatible":
            return tr("curseforge.file.loader.compatible", loader=self.selected_loader.title())
        if status == "universal":
            return tr("curseforge.file.loader.universal")
        if status == "unknown":
            return tr("curseforge.file.loader.unknown")
        key = "curseforge.file.loader.unverified_detail" if detailed else "curseforge.file.loader.unverified"
        return tr(key, loader=self.selected_loader.title())

    def _request_install(self) -> None:
        self.install_button.setEnabled(False)
        self.details_label.setText(tr("content.install.preparing"))
        self._commit_feedback(self.install_button, self.details_label)
        if self.selected_provider == "curseforge":
            file = self.selected_curseforge_file()
            if file is not None:
                request = (file, self.selected_loader, self.allowed_version_types)
                QTimer.singleShot(0, lambda values=request: self.curseforge_install_requested.emit(*values))
            return
        version = self.selected_version()
        if version is not None:
            request = (version, self.selected_loader, self.allowed_version_types)
            QTimer.singleShot(0, lambda values=request: self.install_requested.emit(*values))

    def selected_version(self) -> ModrinthVersion | None:
        if self.selected_provider != "modrinth":
            return None
        index = self.version_combo.currentIndex()
        if index < 0 or index >= len(self._versions):
            return None
        version_id = str(self.version_combo.currentData() or "")
        return next((version for version in self._versions if version.version_id == version_id), None)

    def selected_curseforge_file(self) -> CurseForgeFile | None:
        if self.selected_provider != "curseforge":
            return None
        file_id = int(self.version_combo.currentData() or 0)
        return next((file for file in self._curseforge_files if file.file_id == file_id), None)

    def _previous_page(self) -> None:
        self._offset = max(0, self._offset - self.PAGE_SIZE)
        self._request_current_page()

    def _next_page(self) -> None:
        self._offset += self.PAGE_SIZE
        self._request_current_page()

    def _request_current_page(self) -> None:
        if self.selected_provider == "curseforge":
            self.set_searching(self.selected_loader, "curseforge")
            self._commit_feedback(self.result_count_label, self.details_label)
            request = (self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._offset, self.selected_loader)
            QTimer.singleShot(0, lambda values=request: self.curseforge_search_requested.emit(*values))
            return
        self.set_searching(self.selected_loader, "modrinth")
        self._commit_feedback(self.result_count_label, self.details_label)
        request = (self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset, self.selected_loader)
        QTimer.singleShot(0, lambda values=request: self.search_requested.emit(*values))

    def _provider_changed(self, _index: int) -> None:
        self._reset_catalog()
        self._update_provider_ui()

    def _loader_changed(self, _index: int) -> None:
        self._reset_catalog()
        self._update_provider_ui()

    def _channels_changed(self, _checked: bool) -> None:
        self._pending_channel_preferences = (self.include_beta_checkbox.isChecked(), self.include_alpha_checkbox.isChecked())
        self.release_channel_label.setText(tr("content.channels.applying"))
        self.include_beta_checkbox.setEnabled(False)
        self.include_alpha_checkbox.setEnabled(False)
        self._commit_feedback(self.include_beta_checkbox, self.include_alpha_checkbox, self.release_channel_label)
        self._channel_change_timer.start()

    def _apply_queued_channel_change(self) -> None:
        include_beta, include_alpha = self._pending_channel_preferences
        self.channel_preferences_changed.emit(include_beta, include_alpha)
        if self.selected_provider == "curseforge" and isinstance(self._selected_project, CurseForgeProject):
            self._update_channel_summary()
            self.curseforge_files_requested.emit(self._selected_project.project_id, self.selected_loader, self.allowed_version_types)
        else:
            self._apply_modrinth_version_filter()
        if not self._busy:
            self.include_beta_checkbox.setEnabled(True)
            self.include_alpha_checkbox.setEnabled(True)

    def _render_project_rows(self) -> None:
        self.results_table.blockSignals(True)
        try:
            self.results_table.clearSelection()
            self.results_table.clearContents()
            self.results_table.setRowCount(len(self._projects))
            for row, project in enumerate(self._projects):
                if isinstance(project, CurseForgeProject):
                    values = [project.name, ", ".join(project.authors) or tr("common.unknown"), f"{project.download_count:,}", project.date_modified[:10], project.summary]
                else:
                    values = [project.title, project.author or tr("common.unknown"), f"{project.downloads:,}", project.date_modified[:10], project.description]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.ItemDataRole.UserRole, project)
                    self.results_table.setItem(row, column, item)
                self._request_row_icon(row, project)
            if self._projects:
                self.results_table.selectRow(0)
        finally:
            self.results_table.blockSignals(False)

    def _select_first_project_or_show_empty(self, empty_message: str) -> None:
        if self._projects:
            self._select_project(self._projects[0])
        else:
            self._clear_project_selection(empty_message)

    def _clear_search_state(self) -> None:
        self._result = None
        self._projects = []
        self.results_table.clearSelection()
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def _reset_catalog(self) -> None:
        self._offset = 0
        self._refresh_files_after_search = False
        self._clear_search_state()
        if self.selected_provider == "curseforge":
            self.result_count_label.setText(tr("curseforge.results.ready"))
            self._clear_project_selection(tr("mods.catalog.curseforge.select_project"))
        else:
            self.result_count_label.setText(tr("modrinth.results.ready"))
            self._clear_project_selection(tr("mods.catalog.select_project"))

    def _configure_sort_combo(self) -> None:
        previous = str(self.sort_combo.currentData() or "")
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        if self.selected_provider == "curseforge":
            options = [
                (tr("curseforge.sort.popularity"), "popularity"),
                (tr("curseforge.sort.downloads"), "downloads"),
                (tr("curseforge.sort.updated"), "updated"),
                (tr("curseforge.sort.newest"), "newest"),
            ]
        else:
            options = [
                (tr("modrinth.sort.relevance"), "relevance"),
                (tr("modrinth.sort.downloads"), "downloads"),
                (tr("modrinth.sort.updated"), "updated"),
                (tr("modrinth.sort.newest"), "newest"),
            ]
        for label, value in options:
            self.sort_combo.addItem(label, value)
        index = self.sort_combo.findData(previous)
        self.sort_combo.setCurrentIndex(index if index >= 0 else 0)
        self.sort_combo.blockSignals(False)

    def _update_provider_ui(self) -> None:
        is_curseforge = self.selected_provider == "curseforge"
        self.catalog_title_label.setText(tr("mods.catalog.title.curseforge" if is_curseforge else "mods.catalog.title.modrinth"))
        self.catalog_subtitle_label.setText(tr("mods.catalog.subtitle.curseforge" if is_curseforge else "mods.catalog.subtitle.modrinth"))
        self.search_input.setPlaceholderText(tr("curseforge.search.placeholder" if is_curseforge else "modrinth.search.placeholder"))
        self.cache_status_label.setVisible(is_curseforge)
        self.refresh_button.setVisible(is_curseforge)
        self.clear_cache_button.setVisible(is_curseforge)
        self.open_browser_button.setVisible(True)
        self.open_browser_button.setEnabled(not self._busy and self._has_selected_project_url())
        self._configure_sort_combo()
        self._update_channel_summary()
        self.results_table.setHorizontalHeaderLabels(
            [
                tr("curseforge.column.name" if is_curseforge else "modrinth.column.name"),
                tr("curseforge.column.author" if is_curseforge else "modrinth.column.author"),
                tr("curseforge.column.downloads" if is_curseforge else "modrinth.column.downloads"),
                tr("curseforge.column.updated" if is_curseforge else "modrinth.column.updated"),
                tr("curseforge.column.description" if is_curseforge else "modrinth.column.description"),
            ]
        )
        self._render_cache_status()

    def _update_pagination_buttons(self) -> None:
        if self._busy or self._result is None:
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return
        if isinstance(self._result, CurseForgeSearchResult):
            self.previous_button.setEnabled(self._result.index > 0)
            self.next_button.setEnabled(self._result.index + self._result.page_size < self._result.total_count)
            return
        self.previous_button.setEnabled(self._result.offset > 0)
        self.next_button.setEnabled(self._result.offset + self._result.limit < self._result.total_hits)

    def _has_installable_items(self) -> bool:
        return bool(self._curseforge_files if self.selected_provider == "curseforge" else self._versions)

    def _render_cache_status(self) -> None:
        if not hasattr(self, "cache_status_label") or self.selected_provider != "curseforge":
            return
        info = self._cache_info
        age = self._format_age(info.refreshed_at)
        size_mb = info.cache_size_bytes / (1024 * 1024)
        limit_mb = info.cache_limit_bytes / (1024 * 1024)
        source = tr("curseforge.cache.source.stale") if info.stale else tr("curseforge.cache.source.cached") if info.from_cache else tr("curseforge.cache.source.live")
        if not info.refreshed_at:
            text = tr("curseforge.cache.never", size=f"{size_mb:.1f}", limit=f"{limit_mb:.0f}")
        else:
            text = tr("curseforge.cache.status", age=age, source=source, size=f"{size_mb:.1f}", limit=f"{limit_mb:.0f}")
        if info.last_error:
            text += " · " + tr("curseforge.cache.last_error")
        self.cache_status_label.setText(text)
        remaining = CurseForgeClient.manual_refresh_remaining_seconds()
        self.refresh_button.setEnabled(not self._busy and remaining <= 0)
        self.refresh_button.setText(tr("curseforge.cache.refresh_wait", seconds=remaining) if remaining > 0 else tr("curseforge.cache.refresh"))

    @staticmethod
    def _format_age(value: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            return tr("curseforge.cache.never_value")
        try:
            refreshed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return normalized
        if refreshed.tzinfo is None:
            refreshed = refreshed.replace(tzinfo=timezone.utc)
        seconds = max(0, int((datetime.now(timezone.utc) - refreshed).total_seconds()))
        if seconds < 10:
            return tr("curseforge.cache.just_now")
        if seconds < 60:
            return tr("curseforge.cache.seconds_ago", value=seconds)
        minutes = seconds // 60
        if minutes < 60:
            return tr("curseforge.cache.minutes_ago", value=minutes)
        hours = minutes // 60
        if hours < 24:
            return tr("curseforge.cache.hours_ago", value=hours)
        return tr("curseforge.cache.days_ago", value=hours // 24)

    @staticmethod
    def _commit_feedback(*widgets: QWidget) -> None:
        for widget in widgets:
            widget.update()
            widget.repaint()

    def retranslate_dynamic(self) -> None:
        self.provider_label.setText(tr("mods.catalog.provider.label"))
        self.provider_combo.setItemText(0, tr("mods.catalog.provider.modrinth"))
        self.provider_combo.setItemText(1, tr("mods.catalog.provider.curseforge"))
        self.loader_label.setText(tr("mods.catalog.loader.label"))
        self.loader_combo.setItemText(0, tr("modrinth.loader.fabric"))
        self.loader_combo.setItemText(1, tr("modrinth.loader.forge"))
        self.search_button.setText(tr("common.search"))
        self.clear_cache_button.setText(tr("curseforge.cache.clear"))
        self.previous_button.setText(tr("common.previous"))
        self.next_button.setText(tr("common.next"))
        self.detail_panel.set_open_web_text(tr("content.open_web"))
        self.install_button.setText(tr("mods.catalog.choose_instance"))
        self.include_beta_checkbox.setText(tr("modrinth.channel.beta"))
        self.include_alpha_checkbox.setText(tr("modrinth.channel.alpha"))
        self._update_provider_ui()
        if self._result is None:
            self._reset_catalog()
