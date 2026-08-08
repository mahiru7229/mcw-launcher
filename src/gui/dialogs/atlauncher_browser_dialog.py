from __future__ import annotations

from dataclasses import replace
import re

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from mcw_core.api.atlauncher.atlauncher_client import ATLauncherClient
from mcw_core.api.instance.instance_manager import InstanceManager
from mcw_core.api.language.language_manager import tr
from src.gui.media.remote_image_cache import RemoteImageCache
from src.gui.media.safe_rich_text import sanitize_html
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.content_project_detail import ContentProjectDetailPanel
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.atlauncher.cache import ATLauncherCacheInfo
from src.models.atlauncher.pack import ATLauncherPack, ATLauncherSearchResult
from src.models.atlauncher.version import ATLauncherVersion, ATLauncherVersionSummary


class ATLauncherBrowserDialog(QDialog):
    search_requested = Signal(str, str, int)
    refresh_requested = Signal(str, str, int)
    project_details_requested = Signal(str)
    versions_requested = Signal(str, object)
    version_details_requested = Signal(str, str)
    clear_cache_requested = Signal()
    install_modpack_requested = Signal(str, str, str, bool, object)
    channel_preferences_changed = Signal(bool, bool)

    PAGE_SIZE = 25

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ATLauncherDialog")
        self._result: ATLauncherSearchResult | None = None
        self._projects: list[ATLauncherPack] = []
        self._selected_project: ATLauncherPack | None = None
        self._versions: list[ATLauncherVersionSummary] = []
        self._selected_version: ATLauncherVersion | None = None
        self._index = 0
        self._busy = False
        self._suggested_instance_name = ""
        self._instance_name_customized = False
        self._pending_channel_preferences = (False, False)
        self._cache_info = ATLauncherClient.api_cache_status()
        self._image_cache = RemoteImageCache(self)
        self._channel_change_timer = QTimer(self)
        self._channel_change_timer.setSingleShot(True)
        self._channel_change_timer.setInterval(60)
        self._channel_change_timer.timeout.connect(self._apply_queued_channel_change)
        self._build_ui()
        self.retranslate_dynamic()
        self.set_cache_info(self._cache_info)

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 1240, 620, 1000, 500)
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
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Popularity", "popularity")
        self.sort_combo.addItem("Recently updated", "updated")
        self.sort_combo.addItem("Newest", "newest")
        self.sort_combo.addItem("Name", "name")
        self.search_button = set_theme_icon(QPushButton(), "icon.action.search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self._request_search)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.sort_combo)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        provider_row = QHBoxLayout()
        self.cache_status_label = QLabel()
        self.cache_status_label.setObjectName("MutedLabel")
        self.cache_status_label.setWordWrap(True)
        self.refresh_button = set_theme_icon(QPushButton(), "icon.action.refresh")
        self.refresh_button.clicked.connect(self._request_refresh)
        self.clear_cache_button = QPushButton()
        self.clear_cache_button.clicked.connect(self._request_clear_cache)
        provider_row.addWidget(self.cache_status_label, 1)
        provider_row.addWidget(self.refresh_button)
        provider_row.addWidget(self.clear_cache_button)
        root.addLayout(provider_row)

        channel_row = QHBoxLayout()
        self.release_channel_label = QLabel()
        self.release_channel_label.setObjectName("MutedLabel")
        self.include_beta_checkbox = QCheckBox()
        self.include_alpha_checkbox = QCheckBox()
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
        self.version_combo = QComboBox()
        self.version_combo.setMinimumContentsLength(28)
        self.version_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.version_combo.currentIndexChanged.connect(self._version_selected)
        self.instance_name_input = QLineEdit()
        self.instance_name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.instance_name_input.textEdited.connect(self._instance_name_edited)
        self.optional_checkbox = QCheckBox()
        self.optional_checkbox.setChecked(True)
        self.install_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setMinimumWidth(220)
        self.install_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._request_install)
        self.detail_panel.add_action_row((self.version_combo, 1))
        self.detail_panel.add_action_row((self.instance_name_input, 1))
        install_row = self.detail_panel.add_action_row((self.optional_checkbox, 0))
        install_row.addStretch()
        install_row.addWidget(self.install_button)

        results_panel.setMinimumWidth(420)
        splitter.addWidget(results_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 7)
        splitter.setSizes([540, 760])
        root.addWidget(splitter, 1)

    @property
    def selected_project(self) -> ATLauncherPack | None:
        return self._selected_project

    @property
    def selected_version(self) -> ATLauncherVersion | None:
        return self._selected_version

    @property
    def allowed_release_types(self) -> tuple[str, ...]:
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

    def set_show_project_descriptions(self, visible: bool) -> None:
        self.detail_panel.set_description_visible(visible)

    def set_searching(self) -> None:
        self._result = None
        self._projects = []
        self.results_table.clearSelection()
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.result_count_label.setText(tr("atlauncher.results.searching"))
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self._clear_selection(tr("atlauncher.results.contacting"))

    def set_search_result(self, result: ATLauncherSearchResult) -> None:
        self._result = result
        self._projects = list(result.projects)
        self._index = result.index
        self.set_cache_info(result.cache_info)
        self.results_table.blockSignals(True)
        try:
            self.results_table.clearSelection()
            self.results_table.clearContents()
            self.results_table.setRowCount(len(self._projects))
            for row, project in enumerate(self._projects):
                latest = project.versions[0] if project.versions else None
                values = [
                    project.name,
                    project.pack_type or tr("common.unknown"),
                    latest.minecraft_version if latest is not None else tr("common.unknown"),
                    project.updated_at[:10],
                    project.synopsis,
                ]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.ItemDataRole.UserRole, project)
                    self.results_table.setItem(row, column, item)
                self._image_cache.request(project.icon_url, lambda pixmap, row=row, safe_name=project.safe_name: self._apply_row_icon(row, safe_name, pixmap))
            if self._projects:
                self.results_table.selectRow(0)
        finally:
            self.results_table.blockSignals(False)
        start = result.index + 1 if result.projects else 0
        end = result.index + len(result.projects)
        if result.has_more:
            self.result_count_label.setText(tr("atlauncher.results.more", start=start, end=end))
        else:
            self.result_count_label.setText(tr("atlauncher.results.range", start=start, end=end))
        self.previous_button.setEnabled(not self._busy and result.index > 0)
        self.next_button.setEnabled(not self._busy and result.has_more)
        if self._projects:
            self._select_project(self._projects[0])
        else:
            self._clear_selection(tr("atlauncher.results.empty"))

    def set_project_details(self, safe_name: str, project: ATLauncherPack) -> None:
        current = self._selected_project
        if current is None or current.safe_name != str(safe_name) or project.safe_name != current.safe_name:
            return
        self._selected_project = replace(
            project,
            authors=project.authors or current.authors,
            synopsis=project.synopsis or current.synopsis,
            icon_url=project.icon_url or current.icon_url,
            website_url=project.website_url or current.website_url,
            versions=project.versions or current.versions,
        )
        self._render_project_details(self._selected_project)

    def set_versions(self, safe_name: str, versions: object) -> None:
        if self._selected_project is None or self._selected_project.safe_name != str(safe_name):
            return
        self._versions = [version for version in tuple(versions or ()) if isinstance(version, ATLauncherVersionSummary)]
        self._versions.sort(key=lambda version: (version.published_at, version.updated_at, version.version_id), reverse=True)
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for version in self._versions:
            runtime = version.minecraft_version or tr("common.unknown")
            self.version_combo.addItem(f"{version.version} • {version.release_type.title()} • {runtime}", version.version)
        self.version_combo.blockSignals(False)
        self.install_button.setEnabled(False)
        if self._versions:
            self._version_selected()
        else:
            channels = ", ".join(value.title() for value in self.allowed_release_types)
            self.detail_panel.set_status(tr("atlauncher.versions.none", channels=channels))

    def set_version_details(self, safe_name: str, version_name: str, version: ATLauncherVersion) -> None:
        if self._selected_project is None or self._selected_project.safe_name != str(safe_name):
            return
        if str(self.version_combo.currentData() or "") != str(version_name):
            return
        self._selected_version = version
        loader = version.loader.title() if version.loader else tr("common.unknown")
        memory = f"{version.recommended_memory_mb} MiB" if version.recommended_memory_mb > 0 else tr("common.unknown")
        blocked = bool(version.unsupported_actions) or any(file.download_type == "browser" for file in version.files)
        status_key = "atlauncher.version.status_limited" if blocked else "atlauncher.version.status"
        self.detail_panel.set_status(tr(
            status_key,
            version=version.version,
            channel=version.release_type.title(),
            minecraft=version.minecraft_version or tr("common.unknown"),
            loader=loader,
            files=len([file for file in version.files if not file.server_only]),
            size=self._format_bytes(version.downloadable_size),
            memory=memory,
        ))
        self.install_button.setEnabled(not self._busy and not blocked)

    def set_cache_info(self, info: ATLauncherCacheInfo) -> None:
        if isinstance(info, ATLauncherCacheInfo):
            self._cache_info = info
        size_mb = self._cache_info.cache_size_bytes / (1024 * 1024)
        limit_mb = self._cache_info.cache_limit_bytes / (1024 * 1024)
        source = tr("atlauncher.cache.source.cached") if self._cache_info.from_cache else tr("atlauncher.cache.source.live")
        if not self._cache_info.refreshed_at:
            text = tr("atlauncher.cache.never", size=f"{size_mb:.1f}", limit=f"{limit_mb:.0f}")
        else:
            text = tr("atlauncher.cache.status", source=source, size=f"{size_mb:.1f}", limit=f"{limit_mb:.0f}")
        if self._cache_info.last_error:
            text += " · " + tr("atlauncher.cache.last_error")
        self.cache_status_label.setText(text)

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        for widget in (self.search_button, self.refresh_button, self.clear_cache_button, self.results_table, self.version_combo, self.include_beta_checkbox, self.include_alpha_checkbox):
            widget.setEnabled(not self._busy)
        blocked = bool(self._selected_version and (self._selected_version.unsupported_actions or any(file.download_type == "browser" for file in self._selected_version.files)))
        self.install_button.setEnabled(not self._busy and self._selected_version is not None and not blocked)
        self.detail_panel.open_web_button.setEnabled(not self._busy and bool(self._selected_project and self._selected_project.website_url))
        self.previous_button.setEnabled(not self._busy and self._result is not None and self._result.index > 0)
        self.next_button.setEnabled(not self._busy and self._result is not None and self._result.has_more)

    def _channels_changed(self, _checked: bool) -> None:
        self._pending_channel_preferences = (self.include_beta_checkbox.isChecked(), self.include_alpha_checkbox.isChecked())
        self.release_channel_label.setText(tr("content.channels.applying"))
        self.include_beta_checkbox.setEnabled(False)
        self.include_alpha_checkbox.setEnabled(False)
        self._commit_feedback(self.release_channel_label, self.include_beta_checkbox, self.include_alpha_checkbox)
        self._channel_change_timer.start()

    def _apply_queued_channel_change(self) -> None:
        include_beta, include_alpha = self._pending_channel_preferences
        self.channel_preferences_changed.emit(include_beta, include_alpha)
        self.release_channel_label.setText(tr("atlauncher.channel.release_always"))
        if self._selected_project is not None:
            self.versions_requested.emit(self._selected_project.safe_name, self.allowed_release_types)
        if not self._busy:
            self.include_beta_checkbox.setEnabled(True)
            self.include_alpha_checkbox.setEnabled(True)

    def _request_search(self) -> None:
        self._index = 0
        self.set_searching()
        self.search_button.setEnabled(False)
        self._commit_feedback(self.search_button, self.result_count_label)
        request = (self.search_input.text().strip(), str(self.sort_combo.currentData() or "popularity"), self._index)
        QTimer.singleShot(0, lambda values=request: self.search_requested.emit(*values))

    def _request_refresh(self) -> None:
        self.set_searching()
        self.refresh_button.setEnabled(False)
        self._commit_feedback(self.refresh_button, self.result_count_label)
        request = (self.search_input.text().strip(), str(self.sort_combo.currentData() or "popularity"), self._index)
        QTimer.singleShot(0, lambda values=request: self.refresh_requested.emit(*values))

    def _request_clear_cache(self) -> None:
        self.clear_cache_button.setEnabled(False)
        self.cache_status_label.setText(tr("content.cache.clearing"))
        self._commit_feedback(self.clear_cache_button, self.cache_status_label)
        QTimer.singleShot(0, self.clear_cache_requested.emit)

    def _project_selected(self) -> None:
        rows = self.results_table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.results_table.item(rows[0].row(), 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if isinstance(project, ATLauncherPack):
            self._select_project(project)

    def _select_project(self, project: ATLauncherPack) -> None:
        self._selected_project = project
        self._versions = []
        self._selected_version = None
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        if not self._instance_name_customized or not self.instance_name_input.text().strip() or self.instance_name_input.text() == self._suggested_instance_name:
            self._suggested_instance_name = InstanceManager.next_available_name(self._safe_instance_name(project.name))
            self.instance_name_input.setText(self._suggested_instance_name)
            self._instance_name_customized = False
        self.detail_panel.set_loading(
            project.safe_name,
            "ATLauncher",
            project.name,
            ", ".join(project.authors) or tr("common.unknown"),
            project.synopsis,
            project.icon_url,
            project.website_url,
            tr("atlauncher.project.loading_versions", name=project.name),
        )
        self.project_details_requested.emit(project.safe_name)
        self.versions_requested.emit(project.safe_name, self.allowed_release_types)

    def _clear_selection(self, message: str) -> None:
        self._selected_project = None
        self._versions = []
        self._selected_version = None
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.detail_panel.clear(message)

    def _version_selected(self, _index: int = -1) -> None:
        self._selected_version = None
        project = self._selected_project
        version_name = str(self.version_combo.currentData() or "").strip()
        self.install_button.setEnabled(False)
        if project is None or not version_name:
            return
        self.detail_panel.set_status(tr("atlauncher.version.loading"))
        self.version_details_requested.emit(project.safe_name, version_name)

    def _render_project_details(self, project: ATLauncherPack) -> None:
        game_versions = tuple(dict.fromkeys(version.minecraft_version for version in project.versions if version.minecraft_version))
        metadata = {
            tr("content.metadata.updated"): project.updated_at[:10],
            tr("content.metadata.published"): project.created_at[:10],
            tr("content.metadata.minecraft"): game_versions[:8],
            tr("content.metadata.categories"): (project.pack_type,) if project.pack_type else (),
            tr("atlauncher.metadata.versions"): len(project.versions),
        }
        is_html = "<" in project.description and ">" in project.description
        description = sanitize_html(project.description) if is_html else project.description
        self.detail_panel.set_project(
            token=project.safe_name,
            provider="ATLauncher",
            title=project.name,
            author=", ".join(project.authors) or tr("common.unknown"),
            summary=project.synopsis,
            description=description or project.synopsis,
            icon_url=project.icon_url,
            web_url=project.website_url,
            metadata=metadata,
            gallery_urls=project.gallery_urls,
            description_format="html" if is_html else "plain",
            status=self.detail_panel.status_label.text(),
        )

    def _apply_row_icon(self, row: int, safe_name: str, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return
        item = self.results_table.item(row, 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if isinstance(project, ATLauncherPack) and project.safe_name == safe_name:
            item.setIcon(QIcon(self._image_cache.scaled(pixmap, QSize(40, 40))))

    def _instance_name_edited(self, text: str) -> None:
        self._instance_name_customized = bool(text.strip()) and text != self._suggested_instance_name

    def _request_install(self) -> None:
        project = self._selected_project
        version = self._selected_version
        if project is None or version is None:
            return
        self.install_button.setEnabled(False)
        self.detail_panel.set_status(tr("content.install.preparing"))
        self._commit_feedback(self.install_button, self.detail_panel.status_label)
        request = (project.safe_name, version.version, self.instance_name_input.text().strip(), self.optional_checkbox.isChecked(), self.allowed_release_types)
        QTimer.singleShot(0, lambda values=request: self.install_modpack_requested.emit(*values))

    def _previous_page(self) -> None:
        self._index = max(0, self._index - self.PAGE_SIZE)
        self.set_searching()
        self._commit_feedback(self.result_count_label)
        request = (self.search_input.text().strip(), str(self.sort_combo.currentData() or "popularity"), self._index)
        QTimer.singleShot(0, lambda values=request: self.search_requested.emit(*values))

    def _next_page(self) -> None:
        self._index += self.PAGE_SIZE
        self.set_searching()
        self._commit_feedback(self.result_count_label)
        request = (self.search_input.text().strip(), str(self.sort_combo.currentData() or "popularity"), self._index)
        QTimer.singleShot(0, lambda values=request: self.search_requested.emit(*values))

    @staticmethod
    def _safe_instance_name(value: str) -> str:
        cleaned = re.sub(r'[^\w .()\-\[\]]+', "_", str(value), flags=re.UNICODE).strip().rstrip(". ")
        return cleaned[:80] or "ATLauncher Pack"

    @staticmethod
    def _format_bytes(value: int) -> str:
        size = float(max(0, int(value)))
        for unit in ("B", "KiB", "MiB", "GiB"):
            if size < 1024 or unit == "GiB":
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024
        return f"{size:.1f} GiB"

    @staticmethod
    def _commit_feedback(*widgets: QWidget) -> None:
        for widget in widgets:
            widget.update()
            widget.repaint()

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("atlauncher.modpack.title"))
        self.title_label.setText(tr("atlauncher.modpack.title"))
        self.context_label.setText(tr("atlauncher.modpack.context"))
        self.search_input.setPlaceholderText(tr("atlauncher.search.placeholder"))
        self.search_button.setText(tr("common.search"))
        self.refresh_button.setText(tr("atlauncher.cache.refresh"))
        self.clear_cache_button.setText(tr("atlauncher.cache.clear"))
        self.release_channel_label.setText(tr("atlauncher.channel.release_always"))
        self.include_beta_checkbox.setText(tr("atlauncher.channel.beta"))
        self.include_alpha_checkbox.setText(tr("atlauncher.channel.alpha"))
        self.previous_button.setText(tr("common.previous"))
        self.next_button.setText(tr("common.next"))
        self.detail_panel.set_open_web_text(tr("content.open_web"))
        self.instance_name_input.setPlaceholderText(tr("atlauncher.modpack.instance_name"))
        self.optional_checkbox.setText(tr("atlauncher.modpack.optional_files"))
        self.install_button.setText(tr("atlauncher.modpack.install"))
        self.sort_combo.setItemText(0, tr("atlauncher.sort.popularity"))
        self.sort_combo.setItemText(1, tr("atlauncher.sort.updated"))
        self.sort_combo.setItemText(2, tr("atlauncher.sort.newest"))
        self.sort_combo.setItemText(3, tr("atlauncher.sort.name"))
        self.results_table.setHorizontalHeaderLabels([
            tr("atlauncher.column.name"),
            tr("atlauncher.column.type"),
            tr("atlauncher.column.minecraft"),
            tr("atlauncher.column.updated"),
            tr("atlauncher.column.description"),
        ])
        if self._result is None:
            self.result_count_label.setText(tr("atlauncher.results.ready"))
        self.set_cache_info(self._cache_info)
