from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from mcw_core.api.config.curseforge_config_manager import CurseForgeConfigManager
from mcw_core.api.content.content_pack_manager import ContentPackManager
from mcw_core.api.language.language_manager import tr
from src.gui.media.remote_image_cache import RemoteImageCache
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.content_project_detail import ContentProjectDetailPanel
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.project import CurseForgeProject, CurseForgeSearchResult
from src.models.instance.instance import Instance
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthVersion


class ContentPackBrowserDialog(QDialog):
    search_requested = Signal(str, str, str, str, int, str)
    versions_requested = Signal(str, str, str, str, object)
    project_details_requested = Signal(str, str, str)
    install_modrinth_requested = Signal(str, str, str)
    install_curseforge_requested = Signal(str, str, str, object)
    channel_preferences_changed = Signal(bool, bool)

    PAGE_SIZE = 25

    def __init__(self, content_type: str, parent=None) -> None:
        super().__init__(parent)
        self.content_type = ContentPackManager.normalize_type(content_type)
        self._instance: Instance | None = None
        self._projects: list[object] = []
        self._selected_project: object | None = None
        self._versions: list[object] = []
        self._offset = 0
        self._total = 0
        self._page_size = self.PAGE_SIZE
        self._busy = False
        self._image_cache = RemoteImageCache(self)
        self._channel_timer = QTimer(self)
        self._channel_timer.setSingleShot(True)
        self._channel_timer.setInterval(60)
        self._channel_timer.timeout.connect(self._apply_channel_change)
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        _, dialog_height = resize_dialog_to_screen(self, 1380, 680, 1060, 540)
        self.setMaximumHeight(dialog_height)
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

        search_row = QHBoxLayout()
        self.provider_combo = QComboBox()
        self.provider_combo.addItem(tr("content.provider.modrinth"), "modrinth")
        if CurseForgeConfigManager.is_configured():
            self.provider_combo.addItem(tr("content.provider.curseforge"), "curseforge")
        self.provider_combo.currentIndexChanged.connect(self._provider_changed)
        self.search_input = QLineEdit()
        self.search_input.textEdited.connect(lambda _text: setattr(self, "_offset", 0))
        self.search_input.returnPressed.connect(self._request_search)
        self.sort_combo = QComboBox()
        self.sort_combo.currentIndexChanged.connect(lambda _index: setattr(self, "_offset", 0))
        self.search_button = set_theme_icon(QPushButton(), "icon.action.search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self._request_search)
        search_row.addWidget(self.provider_combo)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.sort_combo)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        channel_row = QHBoxLayout()
        self.channel_label = QLabel()
        self.channel_label.setObjectName("MutedLabel")
        self.include_beta = QCheckBox()
        self.include_alpha = QCheckBox()
        self.include_beta.toggled.connect(self._channel_changed)
        self.include_alpha.toggled.connect(self._channel_changed)
        channel_row.addWidget(self.channel_label, 1)
        channel_row.addWidget(self.include_beta)
        channel_row.addWidget(self.include_alpha)
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
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.results_table.itemSelectionChanged.connect(self._project_selected)
        results_layout.addWidget(self.results_table, 1)

        page_row = QHBoxLayout()
        self.result_count = QLabel()
        self.result_count.setObjectName("MutedLabel")
        self.previous_button = set_theme_icon(QPushButton(), "icon.action.previous")
        self.next_button = set_theme_icon(QPushButton(), "icon.action.next")
        self.previous_button.clicked.connect(self._previous_page)
        self.next_button.clicked.connect(self._next_page)
        page_row.addWidget(self.result_count)
        page_row.addStretch()
        page_row.addWidget(self.previous_button)
        page_row.addWidget(self.next_button)
        results_layout.addLayout(page_row)

        self.detail_panel = ContentProjectDetailPanel(self._image_cache)
        self.version_combo = QComboBox()
        self.version_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.version_combo.setMinimumContentsLength(30)
        self.version_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.version_combo.currentIndexChanged.connect(self._version_selected)
        self.install_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setMinimumWidth(190)
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._request_install)
        self.detail_panel.add_action_row((self.version_combo, 1), (self.install_button, 0))

        results_panel.setMinimumWidth(430)
        splitter.addWidget(results_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 7)
        splitter.setSizes([560, 760])
        root.addWidget(splitter, 1)
        self._populate_sort_options()

    @property
    def provider(self) -> str:
        return str(self.provider_combo.currentData() or "modrinth")

    @property
    def game_version(self) -> str:
        return self._instance.version_id if self._instance is not None else ""

    @property
    def allowed_release_types(self) -> tuple[str, ...]:
        output = ["release"]
        if self.include_beta.isChecked():
            output.append("beta")
        if self.include_alpha.isChecked():
            output.append("alpha")
        return tuple(output)

    def set_instance(self, instance: Instance) -> None:
        self._instance = instance
        self._offset = 0
        self._clear_results()
        self.retranslate_dynamic()

    def set_show_project_descriptions(self, visible: bool) -> None:
        self.detail_panel.set_description_visible(visible)

    def set_channel_preferences(self, include_beta: bool, include_alpha: bool) -> None:
        self.include_beta.blockSignals(True)
        self.include_alpha.blockSignals(True)
        self.include_beta.setChecked(bool(include_beta))
        self.include_alpha.setChecked(bool(include_alpha))
        self.include_beta.blockSignals(False)
        self.include_alpha.blockSignals(False)

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        for widget in (self.provider_combo, self.search_input, self.sort_combo, self.search_button, self.results_table, self.version_combo, self.include_beta, self.include_alpha):
            widget.setEnabled(not self._busy)
        self.install_button.setEnabled(not self._busy and self.version_combo.count() > 0)
        self.previous_button.setEnabled(not self._busy and self._offset > 0)
        self.next_button.setEnabled(not self._busy and self._offset + self._page_size < self._total)

    def set_searching(self, provider: str = "") -> None:
        if provider and provider != self.provider:
            return
        self._clear_results()
        self.result_count.setText(tr("content.browser.searching"))
        self.detail_panel.clear(tr("content.browser.contacting", provider=self.provider.title()))

    def set_search_error(self, provider: str, content_type: str, message: str) -> None:
        if provider != self.provider or content_type != self.content_type:
            return
        self._clear_results()
        self.result_count.setText(tr("content.browser.failed"))
        self.detail_panel.clear(str(message))

    def set_search_result(self, provider: str, content_type: str, result: object) -> None:
        if provider != self.provider or content_type != self.content_type:
            return
        if isinstance(result, ModrinthSearchResult):
            self._projects = list(result.projects)
            self._offset = result.offset
            self._total = result.total_hits
            self._page_size = result.limit
        elif isinstance(result, CurseForgeSearchResult):
            self._projects = list(result.projects)
            self._offset = result.index
            self._total = result.total_count
            self._page_size = result.page_size
        else:
            return
        self._render_rows()
        start = self._offset + 1 if self._projects else 0
        end = self._offset + len(self._projects)
        self.result_count.setText(tr("content.browser.range", start=start, end=end, total=self._total))
        self.previous_button.setEnabled(not self._busy and self._offset > 0)
        self.next_button.setEnabled(not self._busy and self._offset + self._page_size < self._total)
        if self._projects:
            self.results_table.selectRow(0)
        else:
            self.detail_panel.clear(tr("content.browser.empty"))

    def set_project_details(self, provider: str, content_type: str, project_id: str, project: object) -> None:
        if provider != self.provider or content_type != self.content_type or self._selected_project is None:
            return
        if str(self._project_id(self._selected_project)) != str(project_id):
            return
        if isinstance(project, ModrinthProject) and isinstance(self._selected_project, ModrinthProject):
            self._selected_project = replace(project, title=project.title or self._selected_project.title, description=project.description or self._selected_project.description, icon_url=project.icon_url or self._selected_project.icon_url, project_url=project.project_url or self._selected_project.project_url)
        elif isinstance(project, CurseForgeProject) and isinstance(self._selected_project, CurseForgeProject):
            self._selected_project = replace(project, name=project.name or self._selected_project.name, summary=project.summary or self._selected_project.summary, logo_url=project.logo_url or self._selected_project.logo_url, project_url=project.project_url or self._selected_project.project_url)
        self._render_details(self._selected_project)

    def set_versions(self, provider: str, content_type: str, project_id: str, versions: list[ModrinthVersion]) -> None:
        if provider != "modrinth" or self.provider != provider or content_type != self.content_type or self._selected_project is None or str(self._project_id(self._selected_project)) != str(project_id):
            return
        self._versions = [version for version in versions if version.version_type in self.allowed_release_types and any(file.filename.casefold().endswith(".zip") for file in version.files)]
        self._render_versions()

    def set_files(self, provider: str, content_type: str, project_id: int, files: list[CurseForgeFile]) -> None:
        if provider != "curseforge" or self.provider != provider or content_type != self.content_type or self._selected_project is None or int(self._project_id(self._selected_project)) != int(project_id):
            return
        self._versions = [file for file in files if file.release_type in self.allowed_release_types and file.file_name.casefold().endswith(".zip")]
        self._render_versions()

    def selected_curseforge_file(self) -> CurseForgeFile | None:
        index = self.version_combo.currentIndex()
        if self.provider != "curseforge" or index < 0 or index >= len(self._versions):
            return None
        value = self._versions[index]
        return value if isinstance(value, CurseForgeFile) else None

    def selected_project(self) -> object | None:
        return self._selected_project

    def _request_search(self) -> None:
        if self._instance is None or self._busy:
            return
        self.set_searching(self.provider)
        self.search_button.setEnabled(False)
        QTimer.singleShot(0, lambda: self.search_requested.emit(self.provider, self.content_type, self.search_input.text().strip(), str(self.sort_combo.currentData() or "downloads"), self._offset, self.game_version))

    def _provider_changed(self, _index: int) -> None:
        self._offset = 0
        self._populate_sort_options()
        self._clear_results()
        self.retranslate_dynamic()

    def _channel_changed(self, _checked: bool) -> None:
        self.channel_label.setText(tr("content.channels.applying"))
        self.include_beta.setEnabled(False)
        self.include_alpha.setEnabled(False)
        self._channel_timer.start()

    def _apply_channel_change(self) -> None:
        self.channel_preferences_changed.emit(self.include_beta.isChecked(), self.include_alpha.isChecked())
        self.channel_label.setText(tr("content.browser.channels"))
        if self._selected_project is not None:
            self.versions_requested.emit(self.provider, self.content_type, str(self._project_id(self._selected_project)), self.game_version, self.allowed_release_types)
        if not self._busy:
            self.include_beta.setEnabled(True)
            self.include_alpha.setEnabled(True)

    def _project_selected(self) -> None:
        row = self.results_table.currentRow()
        if row < 0 or row >= len(self._projects):
            return
        project = self._projects[row]
        self._selected_project = project
        self._versions = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self._render_details(project, loading=True)
        project_id = str(self._project_id(project))
        self.project_details_requested.emit(self.provider, self.content_type, project_id)
        self.versions_requested.emit(self.provider, self.content_type, project_id, self.game_version, self.allowed_release_types)

    def _version_selected(self, _index: int) -> None:
        self.install_button.setEnabled(not self._busy and self.version_combo.currentIndex() >= 0)
        if self.version_combo.currentIndex() >= 0:
            self.detail_panel.set_status(tr("content.browser.ready_install"))

    def _request_install(self) -> None:
        if self._instance is None or self._selected_project is None or self._busy:
            return
        index = self.version_combo.currentIndex()
        if index < 0 or index >= len(self._versions):
            return
        self.install_button.setEnabled(False)
        self.install_button.setText(tr("content.browser.preparing"))
        if self.provider == "modrinth":
            version = self._versions[index]
            if isinstance(version, ModrinthVersion):
                QTimer.singleShot(0, lambda: self.install_modrinth_requested.emit(self._instance.name, self.content_type, version.version_id))
        else:
            file = self._versions[index]
            project = self._selected_project
            if isinstance(file, CurseForgeFile) and isinstance(project, CurseForgeProject):
                QTimer.singleShot(0, lambda: self.install_curseforge_requested.emit(self._instance.name, self.content_type, project.name, file))

    def _previous_page(self) -> None:
        self._offset = max(0, self._offset - self._page_size)
        self._request_search()

    def _next_page(self) -> None:
        self._offset += self._page_size
        self._request_search()

    def _render_rows(self) -> None:
        self.results_table.blockSignals(True)
        try:
            self.results_table.clearSelection()
            self.results_table.clearContents()
            self.results_table.setRowCount(len(self._projects))
            for row, project in enumerate(self._projects):
                if isinstance(project, ModrinthProject):
                    values = (project.title, project.author or tr("common.unknown"), f"{project.downloads:,}", project.date_modified[:10], project.description)
                    icon_url = project.icon_url
                else:
                    values = (project.name, ", ".join(project.authors) or tr("common.unknown"), f"{project.download_count:,}", project.date_modified[:10], project.summary)
                    icon_url = project.logo_url
                for column, value in enumerate(values):
                    self.results_table.setItem(row, column, QTableWidgetItem(str(value)))
                self._image_cache.request(icon_url, lambda pixmap, target_row=row: self._apply_row_icon(target_row, pixmap))
        finally:
            self.results_table.blockSignals(False)

    def _apply_row_icon(self, row: int, pixmap) -> None:
        if row < 0 or row >= self.results_table.rowCount() or pixmap.isNull():
            return
        item = self.results_table.item(row, 0)
        if item is not None:
            item.setIcon(QIcon(self._image_cache.scaled(pixmap, QSize(40, 40))))

    def _render_details(self, project: object, loading: bool = False) -> None:
        if isinstance(project, ModrinthProject):
            self.detail_panel.set_project(
                token=f"modrinth:{project.project_id}",
                provider="Modrinth",
                title=project.title,
                author=project.author,
                summary=project.description,
                description=project.body or project.description,
                icon_url=project.icon_url,
                web_url=project.project_url,
                metadata={tr("content.metadata.downloads"): f"{project.downloads:,}", tr("content.metadata.updated"): project.date_modified[:10], tr("content.metadata.minecraft"): project.versions, tr("content.metadata.categories"): project.categories, tr("content.metadata.license"): project.license_name or project.license_id},
                gallery_urls=project.gallery_urls,
                description_format="markdown",
                status=tr("content.browser.loading_versions") if loading else "",
            )
        elif isinstance(project, CurseForgeProject):
            self.detail_panel.set_project(
                token=f"curseforge:{project.project_id}",
                provider="CurseForge",
                title=project.name,
                author=", ".join(project.authors),
                summary=project.summary,
                description=project.description or project.summary,
                icon_url=project.logo_url,
                web_url=project.project_url,
                metadata={tr("content.metadata.downloads"): f"{project.download_count:,}", tr("content.metadata.updated"): project.date_modified[:10], tr("content.metadata.minecraft"): project.game_versions, tr("content.metadata.categories"): project.categories},
                gallery_urls=project.screenshot_urls,
                description_format="html",
                status=tr("content.browser.loading_versions") if loading else "",
            )

    def _render_versions(self) -> None:
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for version in self._versions:
            if isinstance(version, ModrinthVersion):
                games = ", ".join(version.game_versions[:3]) or tr("common.unknown")
                self.version_combo.addItem(f"{version.version_number} • {version.version_type.title()} • {games}", version.version_id)
            elif isinstance(version, CurseForgeFile):
                games = ", ".join(version.game_versions[:3]) or tr("common.unknown")
                self.version_combo.addItem(f"{version.display_name} • {version.release_type.title()} • {games}", version.file_id)
        self.version_combo.blockSignals(False)
        self.install_button.setText(tr("content.browser.install"))
        self.install_button.setEnabled(not self._busy and bool(self._versions))
        self.detail_panel.set_status(tr("content.browser.no_versions") if not self._versions else tr("content.browser.ready_install"))

    def _clear_results(self) -> None:
        self._projects = []
        self._selected_project = None
        self._versions = []
        self.results_table.clearSelection()
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def _populate_sort_options(self) -> None:
        current = self.provider
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        if current == "modrinth":
            self.sort_combo.addItem(tr("content.sort.downloads"), "downloads")
            self.sort_combo.addItem(tr("content.sort.updated"), "updated")
            self.sort_combo.addItem(tr("content.sort.newest"), "newest")
            self.sort_combo.addItem(tr("content.sort.relevance"), "relevance")
        else:
            self.sort_combo.addItem(tr("content.sort.popularity"), "popularity")
            self.sort_combo.addItem(tr("content.sort.updated"), "updated")
            self.sort_combo.addItem(tr("content.sort.newest"), "newest")
            self.sort_combo.addItem(tr("content.sort.downloads"), "downloads")
        self.sort_combo.blockSignals(False)

    def retranslate_dynamic(self) -> None:
        name = tr("content.kind.resourcepack") if self.content_type == ContentPackManager.RESOURCE_PACK else tr("content.kind.shader")
        self.setWindowTitle(tr("content.browser.title", kind=name))
        self.title_label.setText(tr("content.browser.title", kind=name))
        self.context_label.setText(tr("content.browser.context", instance=self._instance.name if self._instance is not None else tr("common.none")))
        self.search_input.setPlaceholderText(tr("content.browser.search_placeholder", kind=name.lower()))
        self.search_button.setText(tr("content.browser.search"))
        self.channel_label.setText(tr("content.browser.channels"))
        self.include_beta.setText(tr("content.channel.beta"))
        self.include_alpha.setText(tr("content.channel.alpha"))
        self.results_table.setHorizontalHeaderLabels((tr("content.column.project"), tr("content.column.author"), tr("content.column.downloads"), tr("content.column.updated"), tr("content.column.summary")))
        self.previous_button.setText(tr("content.previous"))
        self.next_button.setText(tr("content.next"))
        self.detail_panel.set_open_web_text(tr("content.open_web"))
        self.install_button.setText(tr("content.browser.install"))

    @staticmethod
    def _project_id(project: object) -> str | int:
        return getattr(project, "project_id", "")
