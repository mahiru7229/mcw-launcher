from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.account.account_skin_manager import AccountSkinManager
from mcw_core.api.config.curseforge_config_manager import CurseForgeConfigManager
from mcw_core.api.language.language_manager import tr
from mcw_core.api.theme.theme_manager import theme_manager
from src.gui.dialogs.create_instance_dialog import CreateInstanceDialog
from src.gui.dialogs.instance_management_dialog import AdvancedInstanceManagerDialog, InstanceManagementDialog
from src.gui.media.minecraft_skin import minecraft_skin_face_icon
from src.gui.pages.base_page import BasePage
from src.gui.pages.instances_page import InstancesPage
from src.gui.theme.accent_runtime import theme_accent_runtime
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget


class InstanceWorkspacePage(BasePage):
    refresh_requested = Signal()
    selected_instance_changed = Signal(str)
    create_requested = Signal(str, str, str)
    rename_requested = Signal(str, str)
    clone_requested = Signal(str, str, bool)
    delete_requested = Signal(str)
    import_requested = Signal(object)
    export_requested = Signal(str, object, bool)
    fabric_versions_requested = Signal(str)
    quilt_versions_requested = Signal(str)
    forge_versions_requested = Signal(str)
    neoforge_versions_requested = Signal(str)
    loader_change_requested = Signal(str, str, str)
    repair_loader_requested = Signal(str)
    restore_forge_requested = Signal(str)
    open_forge_logs_requested = Signal(str)
    export_forge_diagnostics_requested = Signal(str)
    repair_instance_requested = Signal(str)
    manage_mods_requested = Signal(str)
    manage_content_packs_requested = Signal(str)
    manage_content_library_requested = Signal(str)
    browse_modpacks_requested = Signal()
    browse_curseforge_modpacks_requested = Signal()
    browse_ftb_modpacks_requested = Signal()
    backup_requested = Signal(str, str)
    restore_backup_requested = Signal(str, object)
    open_backups_requested = Signal(str)
    open_instance_folder_requested = Signal(str)
    change_icon_requested = Signal(str, object)
    reset_icon_requested = Signal(str)
    scan_modpack_requested = Signal(str)
    repair_modpack_requested = Signal(str)
    check_modpack_update_requested = Signal(str)
    apply_modpack_update_requested = Signal(str)

    launch_requested = Signal()
    instance_settings_requested = Signal(str)
    manage_accounts_requested = Signal()

    ITEM_NAME_ROLE = Qt.ItemDataRole.UserRole

    def __init__(self) -> None:
        super().__init__("Instances", "Choose an instance, then launch or edit it from one workspace.", "instances")
        self._instances: dict[str, object] = {}
        self._versions: list[object] = []
        self._selected_name = ""
        self._show_snapshots = False
        self._synchronizing = False
        self._account: object | None = None
        self._running_instances: list[object] = []
        self._health_reports: dict[str, object] = {}
        self._busy = False

        self.advanced_page = InstancesPage()
        self.advanced_dialog = AdvancedInstanceManagerDialog(self.advanced_page, self)
        self.create_dialog = CreateInstanceDialog(self)
        self.management_dialog = InstanceManagementDialog(self)

        self._build_ui()
        self._connect_dialogs()
        self._forward_advanced_signals()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        toolbar = QFrame()
        toolbar.setObjectName("InstanceToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 10, 12, 10)
        toolbar_layout.setSpacing(8)

        self.add_button = set_theme_icon(QPushButton(), "icon.action.add")
        self.add_button.setObjectName("PrimaryButton")
        self.import_button = set_theme_icon(QPushButton(), "icon.action.import")
        self.modrinth_button = set_theme_icon(QPushButton(), "icon.action.modrinth")
        self.browse_curseforge_modpacks_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.browse_ftb_modpacks_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.refresh_button = set_theme_icon(QPushButton(), "icon.action.refresh")
        self.account_button = set_theme_icon(QPushButton(), "icon.action.account")
        self.account_button.setIconSize(QSize(32, 32))
        self.account_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        self.add_button.clicked.connect(self._open_create_dialog)
        self.import_button.clicked.connect(self._choose_import)
        self.modrinth_button.clicked.connect(self.browse_modpacks_requested.emit)
        self.browse_curseforge_modpacks_button.clicked.connect(self.browse_curseforge_modpacks_requested.emit)
        self.browse_ftb_modpacks_button.clicked.connect(self.browse_ftb_modpacks_requested.emit)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.account_button.clicked.connect(self.manage_accounts_requested.emit)

        toolbar_layout.addWidget(self.add_button)
        toolbar_layout.addWidget(self.import_button)
        toolbar_layout.addWidget(self.modrinth_button)
        toolbar_layout.addWidget(self.browse_curseforge_modpacks_button)
        toolbar_layout.addWidget(self.browse_ftb_modpacks_button)
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.account_button)
        self.root_layout.addWidget(toolbar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("InstanceWorkspaceSplitter")
        self.splitter.setChildrenCollapsible(False)

        self.library_panel = QFrame()
        self.library_panel.setObjectName("InstanceLibrary")
        library_layout = QVBoxLayout(self.library_panel)
        library_layout.setContentsMargins(12, 12, 12, 12)
        library_layout.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self._apply_search)
        library_layout.addWidget(self.search_input)

        self.instance_list = QListWidget()
        self.instance_list.setObjectName("InstanceLibraryList")
        self.instance_list.setViewMode(QListView.ViewMode.IconMode)
        self.instance_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.instance_list.setMovement(QListView.Movement.Static)
        self.instance_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.instance_list.setIconSize(QSize(56, 56))
        self.instance_list.setGridSize(QSize(184, 112))
        self.instance_list.setSpacing(6)
        self.instance_list.setWordWrap(True)
        self.instance_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.instance_list.currentItemChanged.connect(self._list_selection_changed)
        self.instance_list.itemDoubleClicked.connect(lambda _item: self._request_launch())
        self.instance_list.customContextMenuRequested.connect(self._show_context_menu)
        library_layout.addWidget(self.instance_list, 1)

        self.library_status = QLabel()
        self.library_status.setObjectName("TinyLabel")
        library_layout.addWidget(self.library_status)
        self.splitter.addWidget(self.library_panel)

        self.action_panel = CardWidget("", object_name="InstanceActionPanel")
        self.action_panel.setMinimumWidth(300)
        self.instance_icon = QLabel()
        self.instance_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instance_icon.setFixedHeight(76)
        self.instance_name_label = QLabel()
        self.instance_name_label.setObjectName("SectionTitle")
        self.instance_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instance_detail_label = QLabel()
        self.instance_detail_label.setObjectName("MutedLabel")
        self.instance_detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instance_detail_label.setWordWrap(True)
        self.running_label = QLabel()
        self.running_label.setObjectName("TinyLabel")
        self.running_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_label = QLabel()
        self.health_label.setObjectName("TinyLabel")
        self.health_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_label.setWordWrap(True)

        self.launch_button = set_theme_icon(QPushButton(), "icon.action.launch")
        self.launch_button.setObjectName("PrimaryButton")
        self.edit_button = set_theme_icon(QPushButton(), "icon.action.edit")
        self.manage_mods_button = set_theme_icon(QPushButton(), "icon.action.mods")
        self.manage_content_packs_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.manage_content_library_button = set_theme_icon(QPushButton(), "icon.action.search")
        self.settings_button = set_theme_icon(QPushButton(), "icon.action.settings")
        self.change_icon_button = set_theme_icon(QPushButton(), "icon.action.edit")
        self.open_folder_button = set_theme_icon(QPushButton(), "icon.action.folder")
        self.repair_button = set_theme_icon(QPushButton(), "icon.action.repair")
        self.clone_button = set_theme_icon(QPushButton(), "icon.action.clone")
        self.export_button = set_theme_icon(QPushButton(), "icon.action.export")
        self.delete_button = set_theme_icon(QPushButton(), "icon.action.remove")
        self.delete_button.setObjectName("DangerButton")

        self.launch_button.clicked.connect(self._request_launch)
        self.edit_button.clicked.connect(self._open_management_dialog)
        self.manage_mods_button.clicked.connect(lambda: self.manage_mods_requested.emit(self.current_instance_name()))
        self.manage_content_packs_button.clicked.connect(lambda: self.manage_content_packs_requested.emit(self.current_instance_name()))
        self.manage_content_library_button.clicked.connect(lambda: self.manage_content_library_requested.emit(self.current_instance_name()))
        self.settings_button.clicked.connect(lambda: self.instance_settings_requested.emit(self.current_instance_name()))
        self.change_icon_button.clicked.connect(self._choose_icon)
        self.open_folder_button.clicked.connect(lambda: self.open_instance_folder_requested.emit(self.current_instance_name()))
        self.repair_button.clicked.connect(lambda: self.repair_instance_requested.emit(self.current_instance_name()))
        self.clone_button.clicked.connect(self._choose_clone)
        self.export_button.clicked.connect(self._choose_export)
        self.delete_button.clicked.connect(self._confirm_delete)

        self.action_panel.layout.addWidget(self.instance_icon)
        self.action_panel.layout.addWidget(self.instance_name_label)
        self.action_panel.layout.addWidget(self.instance_detail_label)
        self.action_panel.layout.addWidget(self.running_label)
        self.action_panel.layout.addWidget(self.health_label)
        self.action_panel.layout.addSpacing(4)
        self.action_panel.layout.addWidget(self.launch_button)
        self.action_panel.layout.addWidget(self.edit_button)
        self.action_panel.layout.addWidget(self.manage_content_library_button)
        self.action_panel.layout.addWidget(self.manage_mods_button)
        self.action_panel.layout.addWidget(self.manage_content_packs_button)
        self.action_panel.layout.addWidget(self.settings_button)
        self.action_panel.layout.addWidget(self.change_icon_button)
        self.action_panel.layout.addWidget(self.open_folder_button)
        self.action_panel.layout.addWidget(self.repair_button)
        self.action_panel.layout.addStretch(1)
        self.action_panel.layout.addWidget(self.clone_button)
        self.action_panel.layout.addWidget(self.export_button)
        self.action_panel.layout.addWidget(self.delete_button)
        self.splitter.addWidget(self.action_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([820, 330])
        self.root_layout.addWidget(self.splitter, 1)

    def _connect_dialogs(self) -> None:
        self.create_dialog.create_requested.connect(self.create_requested.emit)
        self.create_dialog.import_requested.connect(self._choose_import)
        self.create_dialog.browse_modrinth_requested.connect(self.browse_modpacks_requested.emit)
        self.create_dialog.browse_curseforge_requested.connect(self.browse_curseforge_modpacks_requested.emit)
        self.create_dialog.browse_ftb_requested.connect(self.browse_ftb_modpacks_requested.emit)

        self.management_dialog.launch_requested.connect(self._request_launch)
        self.management_dialog.open_folder_requested.connect(self.open_instance_folder_requested.emit)
        self.management_dialog.manage_mods_requested.connect(self.manage_mods_requested.emit)
        self.management_dialog.instance_settings_requested.connect(self.instance_settings_requested.emit)
        self.management_dialog.repair_requested.connect(self.repair_instance_requested.emit)
        self.management_dialog.create_backup_requested.connect(self.backup_requested.emit)
        self.management_dialog.restore_backup_requested.connect(self._choose_restore_backup)
        self.management_dialog.open_backups_requested.connect(self.open_backups_requested.emit)
        self.management_dialog.open_logs_requested.connect(self.open_forge_logs_requested.emit)
        self.management_dialog.export_diagnostics_requested.connect(self.export_forge_diagnostics_requested.emit)
        self.management_dialog.advanced_requested.connect(self._open_advanced_dialog)

    def _forward_advanced_signals(self) -> None:
        signal_names = (
            "refresh_requested",
            "create_requested",
            "rename_requested",
            "clone_requested",
            "delete_requested",
            "import_requested",
            "export_requested",
            "fabric_versions_requested",
            "quilt_versions_requested",
            "forge_versions_requested",
            "neoforge_versions_requested",
            "loader_change_requested",
            "repair_loader_requested",
            "restore_forge_requested",
            "open_forge_logs_requested",
            "export_forge_diagnostics_requested",
            "repair_instance_requested",
            "manage_mods_requested",
            "browse_modpacks_requested",
            "browse_curseforge_modpacks_requested",
            "browse_ftb_modpacks_requested",
            "backup_requested",
            "restore_backup_requested",
            "open_backups_requested",
            "open_instance_folder_requested",
            "scan_modpack_requested",
            "repair_modpack_requested",
            "check_modpack_update_requested",
            "apply_modpack_update_requested",
        )
        for name in signal_names:
            getattr(self.advanced_page, name).connect(getattr(self, name).emit)
        self.advanced_page.selected_instance_changed.connect(self._advanced_selection_changed)

    def set_compact_mode(self, compact: bool) -> None:
        super().set_compact_mode(compact)
        self.instance_list.setGridSize(QSize(158, 104) if compact else QSize(184, 112))
        self.instance_list.setIconSize(QSize(48, 48) if compact else QSize(56, 56))
        self.action_panel.setMinimumWidth(260 if compact else 300)
        self.splitter.setSizes([680, 280] if compact else [820, 330])

    def set_versions(self, versions: list[object]) -> None:
        self._versions = list(versions)
        self.advanced_page.set_versions(versions)
        self.create_dialog.set_versions(versions)

    def set_fabric_versions(self, game_version: str, versions: list[object]) -> None:
        self.advanced_page.set_fabric_versions(game_version, versions)

    def set_quilt_versions(self, game_version: str, versions: list[object]) -> None:
        self.advanced_page.set_quilt_versions(game_version, versions)

    def set_forge_versions(self, game_version: str, versions: list[object]) -> None:
        self.advanced_page.set_forge_versions(game_version, versions)

    def set_neoforge_versions(self, game_version: str, versions: list[object]) -> None:
        self.advanced_page.set_neoforge_versions(game_version, versions)

    def set_instances(self, instances: list[object], selected_name: str) -> None:
        self._instances = {str(instance.name): instance for instance in instances}
        self.advanced_page.set_instances(instances, selected_name)
        target = selected_name if selected_name in self._instances else self._selected_name
        if target not in self._instances:
            target = next(iter(self._instances), "")
        self._rebuild_library(target)

    def set_modpack_state(self, report: object) -> None:
        self.advanced_page.set_modpack_state(report)

    def set_modpack_update_info(self, info: object | None) -> None:
        self.advanced_page.set_modpack_update_info(info)

    def set_modpack_busy(self, busy: bool) -> None:
        self.advanced_page.set_modpack_busy(busy)

    def set_show_snapshots(self, enabled: bool) -> None:
        self._show_snapshots = bool(enabled)
        self.advanced_page.set_show_snapshots(enabled)
        self.create_dialog.set_show_snapshots(enabled)

    def set_account(self, account: object | None) -> None:
        self._account = account
        self.account_button.setProperty("themeIcon", "")
        self.account_button.setIcon(QIcon())

        if account is None:
            set_theme_icon(self.account_button, "icon.action.account")
            self.account_button.setText(tr("workspace.account.none"))
            self.account_button.setToolTip(tr("account.selection.none"))
            return

        username = str(getattr(account, "username", "?") or "?")
        account_type = str(getattr(getattr(account, "account_type", None), "value", getattr(account, "account_type", "")) or "")
        texture_path = AccountSkinManager.cached_texture(account)
        if texture_path is not None:
            icon = minecraft_skin_face_icon(texture_path, 32)
            if not icon.isNull():
                self.account_button.setIcon(icon)
            else:
                set_theme_icon(self.account_button, "icon.action.account")
        else:
            set_theme_icon(self.account_button, "icon.action.account")

        self.account_button.setText(tr("workspace.account.active", username=username))
        self.account_button.setToolTip(f"{username} — {account_type}" if account_type else username)

    def set_running_instances(self, running_instances: list[object]) -> None:
        self._running_instances = list(running_instances)
        self._rebuild_library(self.current_instance_name())

    def set_health_reports(self, reports: list[object]) -> None:
        mapped: dict[str, object] = {}
        for report in reports:
            instance_id = str(getattr(report, "instance_id", "") or "")
            name = str(getattr(report, "name", "") or "")
            if instance_id:
                mapped[f"id:{instance_id}"] = report
            if name:
                mapped[f"name:{name}"] = report
        self._health_reports = mapped
        self._rebuild_library(self.current_instance_name())

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self.set_interaction_locked(busy)
        self.advanced_page.set_busy(busy)
        self._render_selected()

    def current_instance_name(self) -> str:
        return self._selected_name if self._selected_name in self._instances else ""

    def select_instance(self, name: str) -> None:
        self._select_name(str(name or ""), emit=False)
        self.advanced_page.select_instance(str(name or ""))

    def _rebuild_library(self, selected_name: str) -> None:
        query = self.search_input.text().strip().casefold()
        self._synchronizing = True
        try:
            self.instance_list.clear()
            selected_item: QListWidgetItem | None = None
            for name, instance in sorted(self._instances.items(), key=lambda item: item[0].casefold()):
                item = QListWidgetItem(self._instance_item_icon(instance), self._instance_item_text(instance))
                item.setData(self.ITEM_NAME_ROLE, name)
                item.setToolTip(str(Path(getattr(instance, "instance_dir", ""))))
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
                self.instance_list.addItem(item)
                item.setHidden(bool(query and query not in self._search_blob(instance)))
                if name == selected_name:
                    selected_item = item
            if selected_item is not None and not selected_item.isHidden():
                self.instance_list.setCurrentItem(selected_item)
            elif self.instance_list.count():
                visible = next((self.instance_list.item(index) for index in range(self.instance_list.count()) if not self.instance_list.item(index).isHidden()), None)
                if visible is not None:
                    self.instance_list.setCurrentItem(visible)
            else:
                self._selected_name = ""
        finally:
            self._synchronizing = False
        current = self.instance_list.currentItem()
        self._selected_name = str(current.data(self.ITEM_NAME_ROLE)) if current is not None else ""
        self._render_selected()
        self._update_library_status()

    def _instance_item_icon(self, instance: object) -> QIcon:
        icon_path = str(getattr(instance, "icon", "") or "").strip()
        base_icon = QIcon()
        if icon_path and icon_path != "grass_block":
            path = Path(icon_path)
            if not path.is_absolute():
                path = Path(getattr(instance, "instance_dir", ".")) / path
            if path.is_file():
                base_icon = QIcon(str(path))
        if base_icon.isNull():
            loader_name, _loader_version = self._instance_loader(instance)
            standard = QStyle.StandardPixmap.SP_ComputerIcon if loader_name == "vanilla" else QStyle.StandardPixmap.SP_DirIcon
            base_icon = self.style().standardIcon(standard)
        return self._with_state_badge(base_icon, self._instance_state(instance))

    def _instance_item_text(self, instance: object) -> str:
        loader_name, loader_version = self._instance_loader(instance)
        loader = loader_name.title() if loader_version in {"", "-1"} else f"{loader_name.title()} {loader_version}"
        state = self._instance_state(instance)
        health = self._instance_health_state(instance)
        health_line = "" if health == "healthy" else f"\n{self._health_text(health)}"
        return f"{getattr(instance, 'name', '?')}\n{getattr(instance, 'version_id', '?')} • {loader}\n{self._state_text(state)}{health_line}"

    def _search_blob(self, instance: object) -> str:
        loader_name, loader_version = self._instance_loader(instance)
        return " ".join(
            (
                str(getattr(instance, "name", "")),
                str(getattr(instance, "version_id", "")),
                loader_name,
                loader_version,
                self._instance_health_state(instance),
            )
        ).casefold()

    @staticmethod
    def _instance_loader(instance: object) -> tuple[str, str]:
        loader = tuple(getattr(instance, "mod_loader", ("vanilla", "-1")) or ("vanilla", "-1"))
        loader_name = str(loader[0] if loader else "vanilla").strip().lower() or "vanilla"
        loader_version = str(loader[1] if len(loader) > 1 else "-1").strip()
        return loader_name, "-1" if loader_name == "vanilla" else loader_version

    def _instance_health_report(self, instance: object) -> object | None:
        instance_id = str(getattr(instance, "instance_id", "") or "")
        name = str(getattr(instance, "name", "") or "")
        return self._health_reports.get(f"id:{instance_id}") or self._health_reports.get(f"name:{name}")

    def _instance_health_state(self, instance: object) -> str:
        report = self._instance_health_report(instance)
        state = getattr(report, "state", "healthy") if report is not None else "healthy"
        return str(getattr(state, "value", state) or "healthy")

    @staticmethod
    def _health_text(state: str) -> str:
        return {
            "healthy": tr("workspace.health.healthy"),
            "needs_attention": tr("workspace.health.needs_attention"),
            "migration_required": tr("workspace.health.migration_required"),
            "missing_java": tr("workspace.health.missing_java"),
            "missing_files": tr("workspace.health.missing_files"),
            "incomplete": tr("workspace.health.incomplete"),
            "corrupted": tr("workspace.health.corrupted"),
        }.get(state, tr("workspace.health.healthy"))

    def _instance_state(self, instance: object) -> str:
        instance_id = str(getattr(instance, "instance_id", "") or "")
        instance_name = str(getattr(instance, "name", "") or "")
        running = next(
            (
                item
                for item in self._running_instances
                if (instance_id and str(getattr(item, "instance_id", "") or "") == instance_id)
                or str(getattr(item, "name", "") or "") == instance_name
            ),
            None,
        )
        if running is not None:
            return "loading" if str(getattr(running, "state", "running")) == "preparing" else "running"
        last_state = str(getattr(instance, "last_launch_state", "") or "").strip().casefold()
        if last_state == "crashed" or bool(getattr(instance, "last_launch_crashed", False)):
            return "crashed"
        if last_state == "finished" or str(getattr(instance, "last_played", "") or ""):
            return "finished"
        return "ready"

    @staticmethod
    def _state_text(state: str) -> str:
        return {
            "loading": tr("workspace.state.loading"),
            "running": tr("workspace.state.running"),
            "crashed": tr("workspace.state.crashed"),
            "finished": tr("workspace.state.finished"),
            "ready": tr("workspace.state.ready"),
        }.get(state, tr("workspace.state.ready"))

    def _with_state_badge(self, base_icon: QIcon, state: str) -> QIcon:
        if state == "ready":
            return base_icon
        size = max(32, self.instance_list.iconSize().width() or 56)
        canvas = QPixmap(size, size)
        canvas.fill(Qt.GlobalColor.transparent)
        base = base_icon.pixmap(size, size)
        painter = QPainter(canvas)
        painter.drawPixmap(0, 0, size, size, base)
        badge_key = {
            "loading": "icon.state.busy",
            "running": "icon.action.launch",
            "crashed": "icon.state.error",
            "finished": "icon.state.success",
        }.get(state, "icon.state.ready")
        badge_path = theme_manager.resolve_asset(badge_key)
        badge_size = max(16, round(size * 0.38))
        badge = QPixmap()
        if badge_path is not None:
            badge_path = theme_accent_runtime.tinted_path(badge_path, badge_key)
            badge = QPixmap(str(badge_path))
        if badge.isNull():
            standard = {
                "loading": QStyle.StandardPixmap.SP_BrowserReload,
                "running": QStyle.StandardPixmap.SP_MediaPlay,
                "crashed": QStyle.StandardPixmap.SP_MessageBoxCritical,
                "finished": QStyle.StandardPixmap.SP_DialogApplyButton,
            }.get(state, QStyle.StandardPixmap.SP_FileIcon)
            badge = self.style().standardIcon(standard).pixmap(badge_size, badge_size)
        painter.drawPixmap(size - badge_size, size - badge_size, badge_size, badge_size, badge)
        painter.end()
        return QIcon(canvas)

    def _list_selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        name = str(current.data(self.ITEM_NAME_ROLE)) if current is not None else ""
        self._selected_name = name if name in self._instances else ""
        self._render_selected()
        if not self._synchronizing:
            self.advanced_page.select_instance(self._selected_name)
            self.selected_instance_changed.emit(self._selected_name)

    def _advanced_selection_changed(self, name: str) -> None:
        self._select_name(name, emit=True)

    def _select_name(self, name: str, emit: bool) -> None:
        target: QListWidgetItem | None = None
        for index in range(self.instance_list.count()):
            item = self.instance_list.item(index)
            if str(item.data(self.ITEM_NAME_ROLE)) == name:
                target = item
                break
        self._synchronizing = True
        try:
            self.instance_list.setCurrentItem(target)
            self._selected_name = name if target is not None else ""
        finally:
            self._synchronizing = False
        self._render_selected()
        if emit:
            self.selected_instance_changed.emit(self._selected_name)

    def _render_selected(self) -> None:
        instance = self._instances.get(self.current_instance_name())
        enabled = instance is not None and not self._busy
        for button in (
            self.launch_button,
            self.edit_button,
            self.settings_button,
            self.change_icon_button,
            self.open_folder_button,
            self.repair_button,
            self.clone_button,
            self.export_button,
            self.delete_button,
        ):
            button.setEnabled(enabled)

        if instance is None:
            self.instance_icon.clear()
            self.instance_name_label.setText(tr("workspace.no_selection"))
            self.instance_detail_label.setText(tr("workspace.no_selection_detail"))
            self.running_label.setText("")
            self.health_label.setText("")
            self.manage_mods_button.setEnabled(False)
            self.manage_content_packs_button.setEnabled(False)
            self.manage_content_library_button.setEnabled(False)
            self.management_dialog.set_instance(None)
            return

        loader_name, loader_version = self._instance_loader(instance)
        loader = loader_name.title() if loader_version in {"", "-1"} else f"{loader_name.title()} {loader_version}"
        self.instance_icon.setPixmap(self._instance_item_icon(instance).pixmap(64, 64))
        self.instance_name_label.setText(str(instance.name))
        self.instance_detail_label.setText(
            tr(
                "workspace.selected.summary",
                version=str(getattr(instance, "version_id", "?")),
                loader=loader,
                path=str(Path(getattr(instance, "instance_dir", ""))),
            )
        )
        state = self._instance_state(instance)
        self.running_label.setText(self._state_text(state))
        self.running_label.setProperty("state", {"crashed": "error", "loading": "busy", "running": "success", "finished": "success"}.get(state, "ready"))
        self.running_label.style().unpolish(self.running_label)
        self.running_label.style().polish(self.running_label)
        health_state = self._instance_health_state(instance)
        report = self._instance_health_report(instance)
        issue_count = len(tuple(getattr(report, "issues", ()) or ())) if report is not None else 0
        health_text = self._health_text(health_state)
        if issue_count:
            health_text = tr("workspace.health.with_issues", state=health_text, count=issue_count)
        self.health_label.setText(health_text)
        self.health_label.setProperty("state", "success" if health_state == "healthy" else "error" if health_state in {"corrupted", "incomplete", "missing_java", "missing_files"} else "busy")
        self.health_label.style().unpolish(self.health_label)
        self.health_label.style().polish(self.health_label)
        self.manage_mods_button.setEnabled(enabled and loader_name in {"fabric", "quilt", "forge", "neoforge"})
        self.manage_content_packs_button.setEnabled(enabled)
        self.manage_content_library_button.setEnabled(enabled)
        self.management_dialog.set_instance(instance)

    def _update_library_status(self) -> None:
        total = len(self._instances)
        visible = sum(not self.instance_list.item(index).isHidden() for index in range(self.instance_list.count()))
        if total == 0:
            self.library_status.setText(tr("workspace.library.empty"))
        elif visible == total:
            self.library_status.setText(tr("workspace.library.count", count=total))
        else:
            self.library_status.setText(tr("workspace.library.filtered", visible=visible, total=total))

    def _apply_search(self, query: str) -> None:
        normalized = str(query or "").strip().casefold()
        for index in range(self.instance_list.count()):
            item = self.instance_list.item(index)
            instance = self._instances.get(str(item.data(self.ITEM_NAME_ROLE)))
            item.setHidden(instance is None or bool(normalized and normalized not in self._search_blob(instance)))
        current = self.instance_list.currentItem()
        if current is None or current.isHidden():
            visible = next((self.instance_list.item(index) for index in range(self.instance_list.count()) if not self.instance_list.item(index).isHidden()), None)
            self.instance_list.setCurrentItem(visible)
        self._update_library_status()

    def _open_create_dialog(self) -> None:
        self.create_dialog.set_versions(self._versions)
        self.create_dialog.set_show_snapshots(self._show_snapshots)
        self.create_dialog.name_input.clear()
        self.create_dialog.show()
        self.create_dialog.raise_()
        self.create_dialog.activateWindow()

    def _open_management_dialog(self) -> None:
        instance = self._instances.get(self.current_instance_name())
        if instance is None:
            return
        self.management_dialog.set_instance(instance)
        self.management_dialog.show_overview()
        self.management_dialog.show()
        self.management_dialog.raise_()
        self.management_dialog.activateWindow()

    def _open_advanced_dialog(self, name: str) -> None:
        self.advanced_page.select_instance(name)
        self.advanced_dialog.set_instance_name(name)
        self.advanced_dialog.show()
        self.advanced_dialog.raise_()
        self.advanced_dialog.activateWindow()

    def _request_launch(self) -> None:
        if self.current_instance_name():
            self.launch_requested.emit()

    def _choose_icon(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            tr("workspace.icon.choose_title"),
            "",
            tr("workspace.icon.filter"),
        )
        if path:
            self.change_icon_requested.emit(name, Path(path))

    def _confirm_reset_icon(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        answer = QMessageBox.question(
            self,
            tr("workspace.icon.reset_title"),
            tr("workspace.icon.reset_confirm", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.reset_icon_requested.emit(name)

    def _choose_import(self) -> None:
        path, _selected_filter = QFileDialog.getOpenFileName(self, tr("Import MCW instance"), "", tr("MCW Package (*.mcwpack *.zip)"))
        if path:
            self.import_requested.emit(Path(path))

    def _choose_clone(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        target, accepted = QInputDialog.getText(self, tr("workspace.clone.title"), tr("workspace.clone.name"), text=f"{name} Copy")
        if not accepted or not target.strip():
            return
        answer = QMessageBox.question(
            self,
            tr("workspace.clone.title"),
            tr("workspace.clone.include_saves"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return
        self.clone_requested.emit(name, target.strip(), answer == QMessageBox.StandardButton.Yes)

    def _choose_export(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        path, _selected_filter = QFileDialog.getSaveFileName(self, tr("Export MCW instance"), f"{name}.mcwpack", tr("MCW Package (*.mcwpack)"))
        if not path:
            return
        output_path = Path(path)
        if output_path.suffix.lower() != ".mcwpack":
            output_path = output_path.with_suffix(".mcwpack")
        answer = QMessageBox.question(
            self,
            tr("workspace.export.title"),
            tr("workspace.export.include_saves"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return
        self.export_requested.emit(name, output_path, answer == QMessageBox.StandardButton.Yes)

    def _confirm_delete(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        answer = QMessageBox.question(
            self,
            tr("Delete instance"),
            tr("Delete '{name}' and its entire folder?", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(name)

    def _choose_restore_backup(self, name: str) -> None:
        if not name:
            return
        path, _selected_filter = QFileDialog.getOpenFileName(self, tr("Restore MCW backup"), "", tr("MCW Backup (*.mcwbackup)"))
        if not path:
            return
        answer = QMessageBox.question(
            self,
            tr("Restore backup"),
            tr("Restore this backup into '{name}'? A safety backup will be created first.", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.restore_backup_requested.emit(name, Path(path))

    def _show_context_menu(self, position: QPoint) -> None:
        item = self.instance_list.itemAt(position)
        if item is None:
            return
        self.instance_list.setCurrentItem(item)
        menu = QMenu(self)
        launch = menu.addAction(tr("workspace.action.launch"))
        edit = menu.addAction(tr("workspace.action.edit"))
        change_icon = menu.addAction(tr("workspace.action.change_icon"))
        reset_icon = menu.addAction(tr("workspace.action.reset_icon"))
        manage_library = menu.addAction(tr("workspace.action.manage_content_library"))
        manage_mods = menu.addAction(tr("workspace.action.manage_mods"))
        manage_content = menu.addAction(tr("workspace.action.manage_content_packs"))
        menu.addSeparator()
        open_folder = menu.addAction(tr("workspace.action.open_folder"))
        repair = menu.addAction(tr("workspace.action.repair"))
        clone = menu.addAction(tr("workspace.action.clone"))
        export = menu.addAction(tr("workspace.action.export"))
        menu.addSeparator()
        delete = menu.addAction(tr("workspace.action.delete"))
        manage_library.setEnabled(self.manage_content_library_button.isEnabled())
        manage_mods.setEnabled(self.manage_mods_button.isEnabled())
        manage_content.setEnabled(self.manage_content_packs_button.isEnabled())
        chosen = menu.exec(self.instance_list.mapToGlobal(position))
        if chosen is launch:
            self._request_launch()
        elif chosen is edit:
            self._open_management_dialog()
        elif chosen is change_icon:
            self._choose_icon()
        elif chosen is reset_icon:
            self._confirm_reset_icon()
        elif chosen is manage_library:
            self.manage_content_library_requested.emit(self.current_instance_name())
        elif chosen is manage_mods:
            self.manage_mods_requested.emit(self.current_instance_name())
        elif chosen is manage_content:
            self.manage_content_packs_requested.emit(self.current_instance_name())
        elif chosen is open_folder:
            self.open_instance_folder_requested.emit(self.current_instance_name())
        elif chosen is repair:
            self.repair_instance_requested.emit(self.current_instance_name())
        elif chosen is clone:
            self._choose_clone()
        elif chosen is export:
            self._choose_export()
        elif chosen is delete:
            self._confirm_delete()

    def retranslate_dynamic(self) -> None:
        self.add_button.setText(tr("workspace.toolbar.add"))
        self.import_button.setText(tr("workspace.toolbar.import"))
        self.modrinth_button.setText(tr("workspace.toolbar.modrinth"))
        self.browse_curseforge_modpacks_button.setText(tr("workspace.toolbar.curseforge"))
        self.browse_ftb_modpacks_button.setText(tr("workspace.toolbar.ftb"))
        self.browse_curseforge_modpacks_button.setVisible(CurseForgeConfigManager.is_configured())
        self.refresh_button.setText(tr("workspace.toolbar.refresh"))
        self.search_input.setPlaceholderText(tr("workspace.search.placeholder"))
        self.launch_button.setText(tr("workspace.action.launch"))
        self.edit_button.setText(tr("workspace.action.edit"))
        self.manage_content_library_button.setText(tr("workspace.action.manage_content_library"))
        self.manage_mods_button.setText(tr("workspace.action.manage_mods"))
        self.manage_content_packs_button.setText(tr("workspace.action.manage_content_packs"))
        self.settings_button.setText(tr("workspace.action.instance_settings"))
        self.change_icon_button.setText(tr("workspace.action.change_icon"))
        self.open_folder_button.setText(tr("workspace.action.open_folder"))
        self.repair_button.setText(tr("workspace.action.repair"))
        self.clone_button.setText(tr("workspace.action.clone"))
        self.export_button.setText(tr("workspace.action.export"))
        self.delete_button.setText(tr("workspace.action.delete"))
        self.set_account(self._account)
        self.create_dialog.retranslate_dynamic()
        self.management_dialog.retranslate_dynamic()
        self.advanced_dialog.set_instance_name(self.current_instance_name())
        self._render_selected()
        self._update_library_status()
