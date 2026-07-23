from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem

from src.core.language.language_manager import tr
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.gui.pages.base_page import BasePage
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthVersion


class ModsPage(BasePage):
    search_requested = Signal(str, str, int, str)
    versions_requested = Signal(str, str)
    install_requested = Signal(object, str, object)
    channel_preferences_changed = Signal(bool, bool)

    PAGE_SIZE = 25

    def __init__(self) -> None:
        super().__init__(
            "Install mods",
            "Browse Modrinth first, then choose a compatible instance before installing.",
            "mods",
        )
        self._result: ModrinthSearchResult | None = None
        self._projects: list[ModrinthProject] = []
        self._all_versions: list[ModrinthVersion] = []
        self._versions: list[ModrinthVersion] = []
        self._selected_project: ModrinthProject | None = None
        self._offset = 0
        self._busy = False
        self._pending_channel_preferences = (False, False)
        self._channel_change_timer = QTimer(self)
        self._channel_change_timer.setSingleShot(True)
        self._channel_change_timer.setInterval(25)
        self._channel_change_timer.timeout.connect(self._apply_queued_channel_change)
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        browser_card = CardWidget(
            "Modrinth mod catalog",
            "Select a loader and mod version. The launcher will only offer instances matching both Minecraft and loader versions.",
        )

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("modrinth.search.placeholder"))
        self.search_input.returnPressed.connect(self._request_search)

        self.loader_label = QLabel("Loader")
        self.loader_label.setObjectName("MutedLabel")
        self.loader_combo = QComboBox()
        self.loader_combo.addItem("Fabric", ModLoaderManager.FABRIC)
        self.loader_combo.addItem("Forge", ModLoaderManager.FORGE)
        self.loader_combo.currentIndexChanged.connect(self._loader_changed)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Relevance", "relevance")
        self.sort_combo.addItem("Downloads", "downloads")
        self.sort_combo.addItem("Recently updated", "updated")
        self.sort_combo.addItem("Newest", "newest")

        self.search_button = set_theme_icon(QPushButton(tr("common.search")), "icon.action.search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self._request_search)

        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.loader_label)
        search_row.addWidget(self.loader_combo)
        search_row.addWidget(self.sort_combo)
        search_row.addWidget(self.search_button)
        browser_card.layout.addLayout(search_row)

        channel_row = QHBoxLayout()
        self.release_channel_label = QLabel(tr("modrinth.channel.release_always"))
        self.release_channel_label.setObjectName("MutedLabel")
        self.release_channel_label.setWordWrap(True)
        self.include_beta_checkbox = QCheckBox(tr("modrinth.channel.beta"))
        self.include_alpha_checkbox = QCheckBox(tr("modrinth.channel.alpha"))
        self.include_beta_checkbox.toggled.connect(self._channels_changed)
        self.include_alpha_checkbox.toggled.connect(self._channels_changed)
        channel_row.addWidget(self.release_channel_label, 1)
        channel_row.addWidget(self.include_beta_checkbox)
        channel_row.addWidget(self.include_alpha_checkbox)
        browser_card.layout.addLayout(channel_row)

        self.results_table = QTableWidget(0, 5)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.results_table.itemSelectionChanged.connect(self._project_selected)
        self.results_table.setMinimumHeight(260)
        browser_card.layout.addWidget(self.results_table, 1)

        page_row = QHBoxLayout()
        self.result_count_label = QLabel(tr("modrinth.results.ready"))
        self.result_count_label.setObjectName("MutedLabel")
        self.previous_button = set_theme_icon(QPushButton(tr("common.previous")), "icon.action.previous")
        self.next_button = set_theme_icon(QPushButton(tr("common.next")), "icon.action.next")
        self.previous_button.clicked.connect(self._previous_page)
        self.next_button.clicked.connect(self._next_page)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        page_row.addWidget(self.result_count_label)
        page_row.addStretch()
        page_row.addWidget(self.previous_button)
        page_row.addWidget(self.next_button)
        browser_card.layout.addLayout(page_row)

        install_row = QHBoxLayout()
        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self._version_selected)
        self.install_button = set_theme_icon(QPushButton("Choose instance and install"), "icon.action.download")
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._request_install)
        install_row.addWidget(self.version_combo, 1)
        install_row.addWidget(self.install_button)
        browser_card.layout.addLayout(install_row)

        self.details_label = QLabel("Select a project to load its compatible versions.")
        self.details_label.setObjectName("MutedLabel")
        self.details_label.setWordWrap(True)
        self.details_label.setMinimumHeight(70)
        browser_card.layout.addWidget(self.details_label)

        self.root_layout.addWidget(browser_card)
        self.root_layout.addStretch()

    @property
    def has_loaded_search(self) -> bool:
        return self._result is not None or bool(self._projects)

    @property
    def selected_loader(self) -> str:
        loader = str(self.loader_combo.currentData() or ModLoaderManager.FABRIC).strip().lower()
        return loader if loader in {ModLoaderManager.FABRIC, ModLoaderManager.FORGE} else ModLoaderManager.FABRIC

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

    def set_search_result(self, result: ModrinthSearchResult, loader: str = "") -> None:
        if loader and str(loader).strip().lower() != self.selected_loader:
            return
        self._result = result
        self._projects = list(result.projects)
        self._offset = result.offset

        signals_were_blocked = self.results_table.blockSignals(True)
        try:
            self.results_table.clearSelection()
            self.results_table.clearContents()
            self.results_table.setRowCount(len(self._projects))
            headers = [
                tr("modrinth.column.name"),
                tr("modrinth.column.author"),
                tr("modrinth.column.downloads"),
                tr("modrinth.column.updated"),
                tr("modrinth.column.description"),
            ]
            self.results_table.setHorizontalHeaderLabels(headers)
            for row, project in enumerate(self._projects):
                values = [
                    project.title,
                    project.author or tr("common.unknown"),
                    f"{project.downloads:,}",
                    project.date_modified[:10],
                    project.description,
                ]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.ItemDataRole.UserRole, project)
                    self.results_table.setItem(row, column, item)
            if self._projects:
                self.results_table.selectRow(0)
        finally:
            self.results_table.blockSignals(signals_were_blocked)

        start = result.offset + 1 if result.projects else 0
        end = result.offset + len(result.projects)
        self.result_count_label.setText(tr("modrinth.results.range", start=start, end=end, total=result.total_hits))
        self.previous_button.setEnabled(not self._busy and result.offset > 0)
        self.next_button.setEnabled(not self._busy and result.offset + result.limit < result.total_hits)
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

    def set_versions_error(self, project_id: str, loader: str, message: str) -> None:
        if loader and str(loader).strip().lower() != self.selected_loader:
            return
        if self._selected_project is None or self._selected_project.project_id != project_id:
            return
        self._all_versions = []
        self._versions = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.details_label.setText(tr("mods.catalog.version_error", error=str(message)))

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self.search_input.setEnabled(not self._busy)
        self.search_button.setEnabled(not self._busy)
        self.results_table.setEnabled(not self._busy)
        self.version_combo.setEnabled(not self._busy)
        self.loader_combo.setEnabled(not self._busy)
        self.sort_combo.setEnabled(not self._busy)
        self.include_beta_checkbox.setEnabled(not self._busy)
        self.include_alpha_checkbox.setEnabled(not self._busy)
        self.install_button.setEnabled(not self._busy and bool(self._versions))
        self.previous_button.setEnabled(not self._busy and self._result is not None and self._result.offset > 0)
        self.next_button.setEnabled(not self._busy and self._result is not None and self._result.offset + self._result.limit < self._result.total_hits)

    def start_search(self) -> None:
        self._request_search()

    def _request_search(self) -> None:
        self._offset = 0
        self.set_searching(self.selected_loader)
        self.search_requested.emit(
            self.search_input.text(),
            str(self.sort_combo.currentData() or "relevance"),
            self._offset,
            self.selected_loader,
        )

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
        self.details_label.setText(tr("modrinth.project.loading_versions", title=project.title))
        self.versions_requested.emit(project.project_id, self.selected_loader)

    def _clear_project_selection(self, message: str) -> None:
        self._selected_project = None
        self._all_versions = []
        self._versions = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.details_label.setText(message)

    def _apply_version_filter(self) -> None:
        self._update_channel_summary()
        allowed = set(self.allowed_version_types)
        loader = self.selected_loader
        self._versions = [
            version
            for version in self._all_versions
            if version.version_type in allowed
            and loader in {str(item).strip().lower() for item in version.loaders}
        ]
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for version in self._versions:
            game_text = ", ".join(version.game_versions[:4])
            if len(version.game_versions) > 4:
                game_text += ", …"
            label = f"{version.version_number} • {version.version_type} • Minecraft {game_text}"
            self.version_combo.addItem(label, version.version_id)
        self.version_combo.blockSignals(False)
        self.install_button.setEnabled(not self._busy and bool(self._versions))
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
        self.release_channel_label.setText(
            tr(
                "modrinth.channel.summary",
                release=counts["release"],
                beta=counts["beta"],
                alpha=counts["alpha"],
            )
        )

    def _version_selected(self) -> None:
        version = self.selected_version()
        project = self._selected_project
        if version is None or project is None:
            return
        game_versions = ", ".join(version.game_versions[:8])
        if len(version.game_versions) > 8:
            game_versions += ", …"
        self.details_label.setText(
            tr(
                "mods.catalog.details",
                title=project.title,
                author=project.author or tr("common.unknown"),
                version=version.version_number,
                release_type=version.version_type,
                minecraft=game_versions,
                loader=self.selected_loader.title(),
                description=project.description,
            )
        )

    def _request_install(self) -> None:
        version = self.selected_version()
        if version is None:
            return
        self.install_requested.emit(version, self.selected_loader, self.allowed_version_types)

    def selected_version(self) -> ModrinthVersion | None:
        index = self.version_combo.currentIndex()
        if index < 0 or index >= len(self._versions):
            return None
        version_id = str(self.version_combo.currentData() or "")
        return next((version for version in self._versions if version.version_id == version_id), None)

    def _previous_page(self) -> None:
        self._offset = max(0, self._offset - self.PAGE_SIZE)
        self.set_searching(self.selected_loader)
        self.search_requested.emit(
            self.search_input.text(),
            str(self.sort_combo.currentData() or "relevance"),
            self._offset,
            self.selected_loader,
        )

    def _next_page(self) -> None:
        self._offset += self.PAGE_SIZE
        self.set_searching(self.selected_loader)
        self.search_requested.emit(
            self.search_input.text(),
            str(self.sort_combo.currentData() or "relevance"),
            self._offset,
            self.selected_loader,
        )

    def _loader_changed(self, _index: int) -> None:
        self._offset = 0
        self._result = None
        self._projects = []
        self.results_table.setRowCount(0)
        self._clear_project_selection(tr("modrinth.results.ready"))
        self.retranslate_dynamic()
        if self.isVisible():
            self._request_search()

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

    def retranslate_dynamic(self) -> None:
        self.loader_label.setText(tr("modrinth.loader.label"))
        self.loader_combo.setItemText(0, tr("modrinth.loader.fabric"))
        self.loader_combo.setItemText(1, tr("modrinth.loader.forge"))
        self.sort_combo.setItemText(0, tr("modrinth.sort.relevance"))
        self.sort_combo.setItemText(1, tr("modrinth.sort.downloads"))
        self.sort_combo.setItemText(2, tr("modrinth.sort.updated"))
        self.sort_combo.setItemText(3, tr("modrinth.sort.newest"))
        self.search_input.setPlaceholderText(tr("modrinth.search.placeholder"))
        self.search_button.setText(tr("common.search"))
        self.previous_button.setText(tr("common.previous"))
        self.next_button.setText(tr("common.next"))
        self.install_button.setText(tr("mods.catalog.choose_instance"))
        self.include_beta_checkbox.setText(tr("modrinth.channel.beta"))
        self.include_alpha_checkbox.setText(tr("modrinth.channel.alpha"))
        self._update_channel_summary()
        self.results_table.setHorizontalHeaderLabels(
            [
                tr("modrinth.column.name"),
                tr("modrinth.column.author"),
                tr("modrinth.column.downloads"),
                tr("modrinth.column.updated"),
                tr("modrinth.column.description"),
            ]
        )
