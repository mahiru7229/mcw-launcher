from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QGuiApplication, QScreen
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from mcw_core import CompatibilityConfirmationRequired
from mcw_core.api.config.curseforge_config_manager import CurseForgeConfigManager
from mcw_core.api.content.content_pack_manager import ContentPackManager
from mcw_core.api.config.managed_content_policy import ManagedContentPolicy
from mcw_core.api.content.installed_content_library import InstalledContentLibraryManager
from mcw_core.api.curseforge.curseforge_client import CurseForgeClient
from mcw_core.api.curseforge.curseforge_errors import CurseForgeManagedFilesRequired, CurseForgeModpackManualDownloadRequired
from mcw_core.api.diagnostics.diagnostics_manager import DiagnosticsManager
from mcw_core.api.fs.paths import Paths
from mcw_core.api.hardware.gpu_preference_manager import GraphicsDetectionResult
from mcw_core.api.instance.instance_manager import InstanceManager
from mcw_core.api.instance.settings_manager import SettingsManager
from mcw_core.api.instance.instance_run_lock import InstanceRunLock
from mcw_core.api.language.language_manager import language_manager, tr
from mcw_core.api.lan.lan_agent_manager import LanAgentManager
from mcw_core.api.modloader.mod_loader_manager import ModLoaderManager
from mcw_core.api.modrinth.modrinth_errors import ModrinthManagedFilesRequired, ModrinthModpackManualDownloadRequired
from mcw_core.api.network.download_pause import is_download_cancelled, is_download_paused
from mcw_core.api.runtime.game_runtime_manager import GameRuntimeManager
from mcw_core.api.update.windows_update_installer import AutomaticUpdateUnsupportedError, WindowsUpdateInstaller
from src.gui.application import create_application
from src.gui.animation.motion_runtime import MotionRuntime
from src.gui.app_restart import start_restarted_process
from src.gui.config import LAUNCHER_NAME, VERSION_ID
from src.gui.controllers.account_controller import AccountController
from src.gui.controllers.curseforge_controller import CurseForgeController
from src.gui.controllers.content_pack_controller import ContentPackController
from src.gui.controllers.content_library_controller import ContentLibraryController
from src.gui.controllers.ftb_controller import FTBController
from src.gui.controllers.atlauncher_controller import ATLauncherController
from src.gui.controllers.backup_controller import BackupController
from src.gui.controllers.java_controller import JavaController
from src.gui.controllers.modpack_lifecycle_controller import ModpackLifecycleController
from src.gui.controllers.gui_settings_controller import GuiSettingsController
from src.gui.controllers.instance_controller import InstanceController
from src.gui.controllers.launch_controller import LaunchController
from src.gui.controllers.lan_hosting_controller import LanHostingController
from src.gui.controllers.mod_catalog_controller import ModCatalogController
from src.gui.controllers.mod_controller import ModController
from src.gui.controllers.mod_loader_controller import ModLoaderController
from src.gui.controllers.modrinth_controller import ModrinthController
from src.gui.controllers.optifine_controller import OptiFineController
from src.gui.controllers.settings_controller import InstanceSettingsController
from src.gui.controllers.storage_controller import StorageController
from src.gui.controllers.version_controller import VersionController
from src.gui.controllers.update_controller import UpdateController
from src.gui.dialogs.compatible_instance_dialog import CompatibleInstanceDialog
from src.gui.dialogs.curseforge_browser_dialog import CurseForgeBrowserDialog
from src.gui.dialogs.content_pack_browser_dialog import ContentPackBrowserDialog
from src.gui.dialogs.content_pack_manager_dialog import ContentPackManagerDialog
from src.gui.dialogs.content_library_dialog import ContentLibraryDialog
from src.gui.dialogs.curseforge_manual_download_dialog import CurseForgeManualDownloadDialog
from src.gui.dialogs.ftb_browser_dialog import FTBBrowserDialog
from src.gui.dialogs.atlauncher_browser_dialog import ATLauncherBrowserDialog
from src.gui.dialogs.lan_agent_log_dialog import LanAgentLogDialog
from src.gui.dialogs.legacy_storage_cleanup_dialog import LegacyStorageCleanupDialog, format_bytes
from src.gui.dialogs.instance_import_settings_dialog import InstanceImportSettingsDialog
from src.gui.dialogs.modpack_export_dialog import ModpackExportDialog
from src.gui.dialogs.modpack_import_settings_dialog import ModpackImportSettingsDialog
from src.gui.dialogs.instance_settings_editor_dialog import InstanceSettingsEditorDialog
from src.gui.dialogs.mod_manager_dialog import ModManagerDialog
from src.gui.dialogs.modrinth_browser_dialog import ModrinthBrowserDialog
from src.gui.dialogs.optifine_dialog import OptiFineDialog
from src.gui.dialogs.repair_center_dialog import RepairCenterDialog
from src.gui.dialogs.update_dialog import UpdateDialog
from src.gui.dialogs.unsaved_changes_dialog import UnsavedChangesDecision, prompt_unsaved_changes
from src.gui.display_profile import DisplayProfile, select_display_profile
from src.gui.localization import retranslate_widget_tree
from src.gui.pages.about_page import AboutPage
from src.gui.pages.account_page import AccountPage
from src.gui.pages.home_page import HomePage
from src.gui.pages.instance_settings_page import InstanceSettingsPage
from src.gui.pages.instance_workspace_page import InstanceWorkspacePage
from src.gui.pages.launcher_settings_page import LauncherSettingsPage
from src.gui.pages.logs_page import LogsPage
from src.gui.pages.mods_page import ModsPage
from src.gui.presenters.launch_error_presenter import LaunchErrorPresenter
from src.gui.style import APP_STYLE
from src.gui.task_progress import task_progress_profile
from src.gui.task_runner import TaskRunner
from src.gui.theme.runtime import ThemeRuntime
from src.gui.widget.launch_control_style import LAUNCH_CONTROL_STYLE
from src.gui.widget.launch_control_widget import LaunchControlWidget
from src.gui.widget.right_panel_widget import RightPanelWidget
from src.gui.widget.sidebar_widget import SidebarWidget
from src.gui.widget.toast_notification import ToastManager
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_state import ProgressState
from src.models.update.update_info import PreparedUpdate, UpdateInfo


class MainWindow(QMainWindow):
    def __init__(self, gpu_detection: GraphicsDetectionResult | None = None) -> None:
        super().__init__()

        self.setWindowTitle(LAUNCHER_NAME)
        self._gpu_detection = gpu_detection or GraphicsDetectionResult(supported=False)
        self._display_profile = self._detect_display_profile()
        self.resize(self._display_profile.window_width, self._display_profile.window_height)
        self.setMinimumSize(self._display_profile.minimum_width, self._display_profile.minimum_height)

        self.task_runner = TaskRunner(self)
        self.version_controller = VersionController(self.task_runner)
        self.account_controller = AccountController(self.task_runner)
        self.backup_controller = BackupController(self.task_runner)
        self.java_controller = JavaController(self.task_runner)
        self.modpack_lifecycle_controller = ModpackLifecycleController(self.task_runner)
        self.instance_controller = InstanceController(self.task_runner)
        self.mod_loader_controller = ModLoaderController(self.task_runner)
        self.mod_controller = ModController(self.task_runner)
        self.mod_catalog_controller = ModCatalogController(self.task_runner)
        self.modrinth_controller = ModrinthController(self.task_runner)
        self.curseforge_controller = CurseForgeController(self.task_runner)
        self.content_pack_controller = ContentPackController(self.task_runner)
        self.content_library_controller = ContentLibraryController(self.task_runner)
        self.ftb_controller = FTBController(self.task_runner)
        self.atlauncher_controller = ATLauncherController(self.task_runner)
        self.optifine_controller = OptiFineController(self.task_runner)
        self.instance_settings_controller = InstanceSettingsController()
        self.gui_settings_controller = GuiSettingsController()
        self.storage_controller = StorageController(self.task_runner)
        self._startup_settings = self.gui_settings_controller.load()
        self._session_locale = str(self._startup_settings.get("language", "en-US"))
        self._pending_restart_locale = ""
        self._dismissed_restart_locale = ""
        self._language_restart_prompt_scheduled = False
        self._legacy_storage_notice_shown = False
        self._legacy_storage_notice = None
        self._legacy_cleanup_dialog = None
        self.theme_runtime = ThemeRuntime()
        self.motion_runtime = MotionRuntime(parent=self)
        language_manager.reload()
        language_manager.set_language(self._session_locale, notify=False)
        self.launch_controller = LaunchController(self.task_runner)
        self.lan_hosting_controller = LanHostingController(self.task_runner)
        self.update_controller = UpdateController(self.task_runner, channel=self._startup_settings.get("update_channel", "stable"))
        self.running_instances_timer = QTimer(self)
        self._modrinth_tasks: set[str] = set()
        self._mod_catalog_tasks: set[str] = set()
        self._curseforge_tasks: set[str] = set()
        self._ftb_tasks: set[str] = set()
        self._atlauncher_tasks: set[str] = set()
        self._curseforge_catalog_tasks: set[str] = set()
        self._content_tasks: set[str] = set()
        self._suppress_loader_progress = False
        self._prompted_update_versions: set[str] = set()
        self._selected_instance: object | None = None
        self._restoring_instance_selection = False
        self._pending_mod_install_after_create: dict[str, object] | None = None
        self._modrinth_manual_instance_name = ""
        self._modrinth_pending_modpack_install: ModrinthModpackManualDownloadRequired | None = None
        self._curseforge_manual_instance_name = ""
        self._curseforge_pending_modpack_install: CurseForgeModpackManualDownloadRequired | None = None
        self._manual_launch_provider = ""
        self._manual_launch_lock_token = ""
        self._portable_manual_request: object | None = None
        self._page_history: list[str] = []
        self._page_history_index = -1
        self.running_instances_timer.setInterval(1000)

        self._build_ui()
        self.toast_manager = ToastManager(self.centralWidget(), self.motion_runtime, self)
        retranslate_widget_tree(self)
        self._connect_signals()
        self.launch_control.set_motion_runtime(self.motion_runtime)

        self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, str(self._startup_settings.get("theme", "mcw-default")), bool(self._startup_settings.get("show_static_text", False)), str(self._startup_settings.get("accent_mode", "theme")), str(self._startup_settings.get("accent_color", "#8ed35b")), str(self._startup_settings.get("text_color_mode", "theme")), str(self._startup_settings.get("text_color", "#f4f4f4")))
        self.motion_runtime.apply(self._startup_settings.get("motion_mode", "full"))
        self._initialize_data()

    @staticmethod
    def _primary_screen() -> QScreen | None:
        return QGuiApplication.primaryScreen()

    def _detect_display_profile(self) -> DisplayProfile:
        screen = self._primary_screen()
        if screen is None:
            return select_display_profile(1920, 1080)
        geometry = screen.geometry()
        return select_display_profile(geometry.width(), geometry.height())

    def _apply_display_profile_geometry(self, preserve_position: bool) -> None:
        screen = self.screen() or self._primary_screen()
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.resize(self._display_profile.window_width, self._display_profile.window_height)
        if screen is None:
            return

        available = screen.availableGeometry()
        width = min(self.width(), available.width())
        height = min(self.height(), available.height())
        if width != self.width() or height != self.height():
            self.resize(width, height)

        max_x = available.right() - self.width() + 1
        max_y = available.bottom() - self.height() + 1
        if preserve_position:
            x = min(max(self.x(), available.left()), max(available.left(), max_x))
            y = min(max(self.y(), available.top()), max(available.top(), max_y))
        else:
            x = available.left() + max(0, (available.width() - self.width()) // 2)
            y = available.top() + max(0, (available.height() - self.height()) // 2)
        self.move(x, y)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        root.setProperty("compactLayout", self._display_profile.compact)
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = SidebarWidget(compact=self._display_profile.compact)
        self.sidebar.setFixedWidth(self._display_profile.sidebar_width)

        center = QWidget()
        center.setObjectName("CenterArea")

        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.page_navigation = QWidget()
        self.page_navigation.setObjectName("PageNavigationBar")
        navigation_layout = QHBoxLayout(self.page_navigation)
        navigation_layout.setContentsMargins(10, 6, 10, 6)
        navigation_layout.setSpacing(8)
        self.page_back_button = QPushButton(chr(0x2190))
        self.page_back_button.setObjectName("PageBackButton")
        self.page_back_button.setFixedWidth(44)
        self.page_forward_button = QPushButton(chr(0x2192))
        self.page_forward_button.setObjectName("PageForwardButton")
        self.page_forward_button.setFixedWidth(44)
        navigation_layout.addWidget(self.page_back_button)
        navigation_layout.addWidget(self.page_forward_button)
        navigation_layout.addStretch(1)
        self._update_page_navigation()

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")

        self.launch_control = LaunchControlWidget(compact=self._display_profile.compact)

        center_layout.addWidget(self.page_navigation)
        center_layout.addWidget(self.content_stack, 1)
        center_layout.addWidget(self.launch_control)

        self.right_panel = RightPanelWidget(compact=self._display_profile.compact)
        self.right_panel.setFixedWidth(self._display_profile.right_panel_width)

        self.home_page = HomePage()
        self.account_page = AccountPage()
        self.instances_page = InstanceWorkspacePage()
        self.mods_page = ModsPage()
        self.instance_settings_page = InstanceSettingsPage()
        self.launcher_settings_page = LauncherSettingsPage()
        self.launcher_settings_page.set_gpu_detection(self._gpu_detection)
        self.logs_page = LogsPage()
        self.about_page = AboutPage()
        self.mod_manager_dialog = ModManagerDialog(self)
        self.modrinth_mod_dialog = ModrinthBrowserDialog("mod", self)
        self.modrinth_modpack_dialog = ModrinthBrowserDialog("modpack", self)
        self.modrinth_manual_dialog = CurseForgeManualDownloadDialog(self)
        self.curseforge_mod_dialog = CurseForgeBrowserDialog("mod", self)
        self.curseforge_modpack_dialog = CurseForgeBrowserDialog("modpack", self)
        self.content_pack_manager_dialog = ContentPackManagerDialog(self)
        self.content_library_dialog = ContentLibraryDialog(self)
        self.resource_pack_browser_dialog = ContentPackBrowserDialog(ContentPackManager.RESOURCE_PACK, self)
        self.shader_pack_browser_dialog = ContentPackBrowserDialog(ContentPackManager.SHADER_PACK, self)
        self.ftb_modpack_dialog = FTBBrowserDialog(self)
        self.atlauncher_modpack_dialog = ATLauncherBrowserDialog(self)
        self.optifine_dialog = OptiFineDialog(self)
        self.curseforge_manual_dialog = CurseForgeManualDownloadDialog(self)
        self.portable_manual_dialog = CurseForgeManualDownloadDialog(self)
        self.repair_center_dialog = RepairCenterDialog(self)

        self.pages = {
            "home": self.home_page,
            "accounts": self.account_page,
            "instances": self.instances_page,
            "mods": self.mods_page,
            "instance_settings": self.instance_settings_page,
            "launcher_settings": self.launcher_settings_page,
            "logs": self.logs_page,
            "about": self.about_page,
        }

        for page in self.pages.values():
            page.set_compact_mode(self._display_profile.compact)
            self.content_stack.addWidget(page)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(center, 1)
        self.right_panel.setVisible(False)
        root_layout.addWidget(self.right_panel)

    def _connect_signals(self) -> None:
        self.sidebar.page_requested.connect(self.show_page)
        self.sidebar.collapse_requested.connect(lambda collapsed: self.motion_runtime.set_sidebar_collapsed(self.sidebar, collapsed, self._display_profile.sidebar_width))
        self.page_back_button.clicked.connect(lambda: self._navigate_page_history(-1))
        self.page_forward_button.clicked.connect(lambda: self._navigate_page_history(1))

        self.home_page.manage_accounts_requested.connect(lambda: self.show_page("accounts"))
        self.home_page.manage_instances_requested.connect(lambda: self.show_page("instances"))
        self.home_page.open_settings_requested.connect(lambda: self.show_page("launcher_settings"))

        self.right_panel.manage_accounts_requested.connect(lambda: self.show_page("accounts"))
        self.right_panel.manage_instances_requested.connect(lambda: self.show_page("instances"))
        self.right_panel.manage_mods_requested.connect(self._open_mod_manager)
        self.right_panel.refresh_requested.connect(self._refresh_all)
        self.running_instances_timer.timeout.connect(self.instance_controller.refresh_running)

        self.account_page.create_offline_requested.connect(self.account_controller.create_offline)
        self.account_page.create_microsoft_requested.connect(self.account_controller.create_microsoft)
        self.account_page.cancel_microsoft_requested.connect(self.account_controller.cancel_microsoft)
        self.account_page.select_requested.connect(self.account_controller.select)
        self.account_page.remove_requested.connect(self.account_controller.remove)
        self.account_page.refresh_requested.connect(self.account_controller.refresh)
        self.account_page.security_audit_requested.connect(self.account_controller.audit_security)
        self.account_page.security_reprotect_requested.connect(self.account_controller.reprotect_security)

        self.instances_page.refresh_requested.connect(self.instance_controller.refresh)
        self.instances_page.launch_requested.connect(self._request_launch)
        self.instances_page.instance_settings_requested.connect(self._open_instance_settings_workspace)
        self.instances_page.manage_accounts_requested.connect(lambda: self.show_page("accounts"))
        self.instances_page.selected_instance_changed.connect(self.instance_controller.select)
        self.instances_page.favorite_changed.connect(self.instance_controller.set_favorite)
        self.instances_page.group_changed.connect(self.instance_controller.set_group)
        self.instances_page.tags_changed.connect(self.instance_controller.set_tags)
        self.instances_page.runtime_scan_requested.connect(self.java_controller.scan)
        self.instances_page.runtime_install_requested.connect(self.java_controller.install)
        self.instances_page.java_runtime_apply_requested.connect(self.instance_controller.set_java_runtime)
        self.instances_page.create_requested.connect(self.instance_controller.create)
        self.instances_page.create_with_optifine_requested.connect(self.instance_controller.create_with_optifine)
        self.instances_page.fabric_versions_requested.connect(self.mod_loader_controller.load_fabric_versions)
        self.instances_page.quilt_versions_requested.connect(self.mod_loader_controller.load_quilt_versions)
        self.instances_page.forge_versions_requested.connect(self.mod_loader_controller.load_forge_versions)
        self.instances_page.neoforge_versions_requested.connect(self.mod_loader_controller.load_neoforge_versions)
        self.instances_page.loader_change_requested.connect(self.instance_controller.change_loader)
        self.instances_page.repair_loader_requested.connect(self.instance_controller.repair_loader)
        self.instances_page.restore_forge_requested.connect(self.instance_controller.restore_previous_forge)
        self.instances_page.open_forge_logs_requested.connect(self._open_forge_logs)
        self.instances_page.export_forge_diagnostics_requested.connect(self._export_forge_diagnostics)
        self.instances_page.repair_instance_requested.connect(self._open_repair_center)
        self.repair_center_dialog.scan_requested.connect(self.instance_controller.scan_repair_center)
        self.repair_center_dialog.repair_requested.connect(self.instance_controller.execute_repair_plan)
        self.instances_page.manage_mods_requested.connect(self._open_mod_manager)
        self.instances_page.manage_content_packs_requested.connect(self._open_content_pack_manager)
        self.instances_page.manage_content_library_requested.connect(self._open_content_library)
        self.instances_page.manage_optifine_requested.connect(self._open_optifine)
        self.instances_page.browse_modpacks_requested.connect(self._open_modrinth_modpacks)
        self.instances_page.browse_curseforge_modpacks_requested.connect(self._open_curseforge_modpacks)
        self.instances_page.browse_ftb_modpacks_requested.connect(self._open_ftb_modpacks)
        self.instances_page.browse_atlauncher_modpacks_requested.connect(self._open_atlauncher_modpacks)
        self.instances_page.rename_requested.connect(self.instance_controller.rename)
        self.instances_page.clone_requested.connect(self.instance_controller.clone)
        self.instances_page.delete_requested.connect(self.instance_controller.delete)
        self.instances_page.import_requested.connect(self.instance_controller.inspect_package)
        self.instances_page.export_requested.connect(self.instance_controller.export_package)
        self.instances_page.import_modpack_package_requested.connect(self.instance_controller.inspect_modpack_package)
        self.instances_page.export_modpack_requested.connect(self._open_modpack_export)
        self.instances_page.backup_requested.connect(self.backup_controller.create)
        self.instances_page.restore_backup_requested.connect(self.backup_controller.restore)
        self.instances_page.open_backups_requested.connect(self._open_backups_folder)
        self.instances_page.open_instance_folder_requested.connect(self._open_instance_folder)
        self.instances_page.change_icon_requested.connect(self.instance_controller.change_icon)
        self.instances_page.reset_icon_requested.connect(self.instance_controller.reset_icon)
        self.instances_page.scan_modpack_requested.connect(self.modpack_lifecycle_controller.scan)
        self.instances_page.repair_modpack_requested.connect(self.modpack_lifecycle_controller.repair)
        self.instances_page.check_modpack_update_requested.connect(lambda name: self.modpack_lifecycle_controller.check_update(name, self.modrinth_modpack_dialog.allowed_version_types, force_refresh=True))
        self.instances_page.apply_modpack_update_requested.connect(lambda name: self.modpack_lifecycle_controller.preview_update(name, self.modrinth_modpack_dialog.allowed_version_types))

        self.mods_page.search_requested.connect(self.mod_catalog_controller.search)
        self.mods_page.versions_requested.connect(self.mod_catalog_controller.load_versions)
        self.mods_page.project_details_requested.connect(lambda project_id, loader: self.modrinth_controller.load_project_details("mod", project_id, loader))
        self.mods_page.install_requested.connect(self._choose_instance_for_mod_install)
        self.mods_page.curseforge_search_requested.connect(self._search_curseforge_catalog)
        self.mods_page.curseforge_refresh_requested.connect(self._refresh_curseforge_catalog)
        self.mods_page.curseforge_files_requested.connect(self._load_curseforge_catalog_files)
        self.mods_page.curseforge_project_details_requested.connect(lambda project_id, loader: self.curseforge_controller.load_project_details("mod", project_id, loader))
        self.mods_page.curseforge_files_refresh_requested.connect(self._refresh_curseforge_catalog_files)
        self.mods_page.curseforge_clear_cache_requested.connect(lambda: self.curseforge_controller.clear_api_cache(context=CurseForgeController.CATALOG_CONTEXT))
        self.mods_page.curseforge_install_requested.connect(self._choose_instance_for_curseforge_install)
        self.mods_page.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.mod_catalog_controller.search_results_changed.connect(lambda loader, result: self.mods_page.set_search_result(result, loader))
        self.mod_catalog_controller.search_failed.connect(self.mods_page.set_search_error)
        self.mod_catalog_controller.versions_changed.connect(lambda project_id, loader, versions: self.mods_page.set_versions(project_id, versions, loader))
        self.mod_catalog_controller.versions_failed.connect(self.mods_page.set_versions_error)

        self.instance_settings_page.load_requested.connect(self._request_instance_settings_load)
        self.instance_settings_page.save_requested.connect(self.instance_settings_controller.save)
        self.instance_settings_page.lan_prepare_requested.connect(self._request_lan_hosting_prepare)
        self.instance_settings_page.lan_agent_log_requested.connect(self._open_lan_agent_log)
        self.instance_settings_page.dirty_changed.connect(lambda dirty: self.sidebar.set_page_dirty("instance_settings", dirty))

        self.launcher_settings_page.save_requested.connect(self.gui_settings_controller.save)
        self.launcher_settings_page.dirty_changed.connect(lambda dirty: self.sidebar.set_page_dirty("launcher_settings", dirty))
        self.launcher_settings_page.reset_requested.connect(self.gui_settings_controller.reset)
        self.launcher_settings_page.first_run_setup_requested.connect(self._run_first_run_setup)
        self.launcher_settings_page.review_legacy_storage_requested.connect(self._review_legacy_storage)
        self.launcher_settings_page.check_updates_requested.connect(lambda: self.update_controller.check(manual=True))
        self.launcher_settings_page.reload_theme_requested.connect(self._preview_theme)
        self.launcher_settings_page.live_theme_reload_requested.connect(self._reload_theme_silently)
        self.launcher_settings_page.motion_mode_changed.connect(self._preview_motion)
        self.launcher_settings_page.accent_changed.connect(self._preview_accent)
        self.launcher_settings_page.text_color_changed.connect(self._preview_text_color)
        self.launcher_settings_page.preview_toast_requested.connect(
            lambda: self.toast_manager.show(
                tr("motion.preview.toast.message"),
                "success",
                tr("motion.preview.toast.title"),
            )
        )
        self.launcher_settings_page.scan_java_requested.connect(self.java_controller.scan)
        self.launcher_settings_page.install_java_requested.connect(self.java_controller.install)
        self.launcher_settings_page.open_java_requested.connect(self._open_java_folder)
        self.logs_page.export_diagnostics_requested.connect(self._export_diagnostics)
        self.logs_page.open_logs_folder_requested.connect(self._open_logs_folder)
        self.logs_page.open_latest_game_log_requested.connect(self._open_latest_game_log)
        self.logs_page.open_latest_crash_report_requested.connect(self._open_latest_crash_report)

        self.launch_control.launch_clicked.connect(self._request_launch)
        self.launch_control.cancel_clicked.connect(self.launch_controller.cancel)

        self.version_controller.versions_changed.connect(self.instances_page.set_versions)
        self.version_controller.versions_changed.connect(lambda versions: self.home_page.set_manifest_count(len(versions)))
        self.mod_loader_controller.fabric_versions_changed.connect(self.instances_page.set_fabric_versions)
        self.mod_loader_controller.quilt_versions_changed.connect(self.instances_page.set_quilt_versions)
        self.mod_loader_controller.forge_versions_changed.connect(self.instances_page.set_forge_versions)
        self.mod_loader_controller.neoforge_versions_changed.connect(self.instances_page.set_neoforge_versions)

        self.account_controller.accounts_changed.connect(self.account_page.set_accounts)
        self.account_controller.selected_account_changed.connect(self._account_selected)
        self.account_controller.microsoft_auth_state_changed.connect(self.account_page.set_microsoft_auth_state)
        self.account_controller.security_report_changed.connect(self.account_page.set_security_report)
        self.java_controller.installations_changed.connect(self.launcher_settings_page.set_java_installations)
        self.java_controller.installations_changed.connect(self.instances_page.set_java_installations)
        self.java_controller.latest_release_changed.connect(self.launcher_settings_page.set_latest_java_release)
        self.java_controller.latest_release_failed.connect(self.launcher_settings_page.set_latest_java_release_failed)
        self.java_controller.installation_finished.connect(self.launcher_settings_page.set_java_installation_result)
        self.java_controller.installation_cancelled.connect(self.launcher_settings_page.set_java_installation_cancelled)
        self.java_controller.installation_failed.connect(self.launcher_settings_page.set_java_installation_failed)
        self.backup_controller.backup_created.connect(self._on_backup_created)
        self.backup_controller.restore_finished.connect(self._on_backup_restored)
        self.modpack_lifecycle_controller.state_changed.connect(self.instances_page.set_modpack_state)
        self.modpack_lifecycle_controller.update_checked.connect(self._on_modpack_update_checked)
        self.modpack_lifecycle_controller.update_previewed.connect(self._on_modpack_update_previewed)
        self.modpack_lifecycle_controller.update_finished.connect(self._on_modpack_updated)
        self.modpack_lifecycle_controller.repair_finished.connect(self._on_modpack_repaired)

        self.instance_controller.instances_changed.connect(self.instances_page.set_instances)
        self.instance_controller.health_reports_changed.connect(self.instances_page.set_health_reports)
        self.instance_controller.instances_changed.connect(self.instance_settings_page.set_instances)
        self.instance_controller.running_instances_changed.connect(self.right_panel.set_running_instances)
        self.instance_controller.running_instances_changed.connect(self.instances_page.set_running_instances)
        self.instance_controller.selected_instance_changed.connect(self._instance_selected)
        self.instance_controller.runtime_profile_changed.connect(self.instances_page.set_runtime_profile)
        self.instance_controller.forge_diagnostics_finished.connect(self._forge_diagnostics_finished)
        self.instance_controller.export_finished.connect(self._show_export_finished)
        self.instance_controller.import_preview_ready.connect(self._show_instance_import_settings)
        self.instance_controller.modpack_import_preview_ready.connect(self._show_modpack_import_settings)
        self.instance_controller.modpack_export_finished.connect(self._show_modpack_export_finished)

        self.instance_settings_controller.settings_loaded.connect(self.instance_settings_page.set_settings)
        self.storage_controller.legacy_probe_ready.connect(self._on_legacy_storage_probe_ready)
        self.storage_controller.cleanup_plan_ready.connect(self._on_legacy_storage_plan_ready)
        self.storage_controller.cleanup_completed.connect(self._on_legacy_storage_cleanup_completed)
        self.gui_settings_controller.settings_changed.connect(self._apply_gui_settings)

        self.mod_manager_dialog.refresh_requested.connect(self.mod_controller.refresh)
        self.mod_manager_dialog.add_requested.connect(self.mod_controller.add)
        self.mod_manager_dialog.remove_requested.connect(self.mod_controller.remove)
        self.mod_manager_dialog.enabled_requested.connect(self.mod_controller.set_enabled)
        self.mod_manager_dialog.modrinth_requested.connect(self._open_modrinth_mod_browser)
        self.mod_manager_dialog.curseforge_requested.connect(self._open_curseforge_mod_browser)
        self.mod_manager_dialog.check_updates_requested.connect(self.mod_controller.check_updates)
        self.mod_manager_dialog.update_projects_requested.connect(self.mod_controller.update_projects)
        self.mod_manager_dialog.update_all_requested.connect(self.mod_controller.update_all)
        self.mod_manager_dialog.lock_requested.connect(self.mod_controller.set_locked)
        self.mod_manager_dialog.analyze_requested.connect(self.mod_controller.analyze)
        self.mod_controller.instance_changed.connect(self.mod_manager_dialog.set_instance)
        self.mod_controller.mods_changed.connect(self.mod_manager_dialog.set_mods)
        self.mod_controller.updates_changed.connect(self.mod_manager_dialog.set_update_report)
        self.mod_controller.health_changed.connect(self.mod_manager_dialog.set_health_report)

        self.content_library_dialog.refresh_requested.connect(self.content_library_controller.refresh)
        self.content_library_dialog.enabled_requested.connect(self.content_library_controller.set_enabled)
        self.content_library_dialog.remove_requested.connect(self.content_library_controller.remove)
        self.content_library_dialog.pin_requested.connect(self.content_library_controller.set_pinned)
        self.content_library_dialog.ignore_update_requested.connect(self.content_library_controller.set_ignored_update)
        self.content_library_dialog.import_requested.connect(self.content_library_controller.import_local)
        self.content_library_dialog.open_folder_requested.connect(self._open_content_library_folder)
        self.content_library_dialog.open_manager_requested.connect(self._open_content_library_manager)
        self.content_library_controller.instance_changed.connect(self.content_library_dialog.set_instance)
        self.content_library_controller.library_changed.connect(self.content_library_dialog.set_library)

        self.modrinth_mod_dialog.search_requested.connect(self._search_modrinth_mods)
        self.modrinth_modpack_dialog.search_requested.connect(self._search_modrinth_modpacks)
        self.modrinth_mod_dialog.versions_requested.connect(self.modrinth_controller.load_versions)
        self.modrinth_modpack_dialog.versions_requested.connect(self.modrinth_controller.load_versions)
        self.modrinth_mod_dialog.project_details_requested.connect(self.modrinth_controller.load_project_details)
        self.modrinth_modpack_dialog.project_details_requested.connect(self.modrinth_controller.load_project_details)
        self.modrinth_mod_dialog.install_mod_requested.connect(self._install_modrinth_mod)
        self.modrinth_modpack_dialog.install_modpack_requested.connect(self._install_modrinth_modpack)
        self.modrinth_mod_dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.modrinth_modpack_dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.modrinth_controller.search_results_changed.connect(self._set_modrinth_results)
        self.modrinth_controller.search_failed.connect(self._set_modrinth_search_error)
        self.modrinth_controller.versions_changed.connect(self._set_modrinth_versions)
        self.modrinth_controller.project_details_changed.connect(self._set_modrinth_project_details)
        self.modrinth_controller.mod_installed.connect(self._modrinth_mod_installed)
        self.modrinth_controller.manual_files_installed.connect(self._modrinth_manual_files_installed)
        self.modrinth_controller.modpack_installed.connect(self._modrinth_modpack_installed)
        self.modrinth_controller.modpack_manual_download_required.connect(self._modrinth_modpack_manual_download_required)
        self.modrinth_manual_dialog.files_selected.connect(self._install_manual_modrinth_files)
        self.launch_controller.portable_manual_download_required.connect(self._portable_manual_download_required)
        self.launch_controller.compatibility_confirmation_required.connect(self._confirm_compatibility_launch)
        self.launch_controller.manual_content_required.connect(self._on_launch_manual_content_required)
        self.portable_manual_dialog.files_selected.connect(self._install_portable_manual_files)
        self.instance_controller.portable_manual_files_installed.connect(self._portable_manual_files_installed)

        self.curseforge_mod_dialog.search_requested.connect(self._search_curseforge_mods)
        self.curseforge_modpack_dialog.search_requested.connect(self._search_curseforge_modpacks)
        self.curseforge_mod_dialog.refresh_requested.connect(self._refresh_curseforge_mods)
        self.curseforge_modpack_dialog.refresh_requested.connect(self._refresh_curseforge_modpacks)
        self.curseforge_mod_dialog.files_requested.connect(self.curseforge_controller.load_files)
        self.curseforge_modpack_dialog.files_requested.connect(self.curseforge_controller.load_files)
        self.curseforge_mod_dialog.project_details_requested.connect(self.curseforge_controller.load_project_details)
        self.curseforge_modpack_dialog.project_details_requested.connect(self.curseforge_controller.load_project_details)
        self.curseforge_mod_dialog.files_refresh_requested.connect(lambda project_type, project_id, game_version, loader, channels: self.curseforge_controller.load_files(project_type, project_id, game_version, loader, tuple(channels), force_refresh=True, manual_refresh=False))
        self.curseforge_modpack_dialog.files_refresh_requested.connect(lambda project_type, project_id, game_version, loader, channels: self.curseforge_controller.load_files(project_type, project_id, game_version, loader, tuple(channels), force_refresh=True, manual_refresh=False))
        self.curseforge_mod_dialog.clear_cache_requested.connect(self.curseforge_controller.clear_api_cache)
        self.curseforge_modpack_dialog.clear_cache_requested.connect(self.curseforge_controller.clear_api_cache)
        self.curseforge_mod_dialog.install_mod_requested.connect(self._install_curseforge_mod)
        self.curseforge_modpack_dialog.install_modpack_requested.connect(self._install_curseforge_modpack)
        self.curseforge_mod_dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.curseforge_modpack_dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.curseforge_controller.search_results_changed.connect(self._set_curseforge_results)
        self.curseforge_controller.files_changed.connect(self._set_curseforge_files)
        self.curseforge_controller.project_details_changed.connect(self._set_curseforge_project_details)
        self.curseforge_controller.cache_info_changed.connect(self._set_curseforge_cache_info)
        self.curseforge_controller.catalog_search_results_changed.connect(self.mods_page.set_curseforge_search_result)
        self.curseforge_controller.catalog_files_changed.connect(self.mods_page.set_curseforge_files)
        self.curseforge_controller.catalog_cache_info_changed.connect(self.mods_page.set_curseforge_cache_info)
        self.curseforge_controller.catalog_request_failed.connect(self._on_curseforge_catalog_failed)
        self.curseforge_controller.cache_cleared.connect(lambda _info: QMessageBox.information(self, tr("curseforge.title"), tr("curseforge.cache.cleared")))
        self.curseforge_controller.mod_installed.connect(self._curseforge_mod_installed)
        self.curseforge_controller.manual_file_installed.connect(self._curseforge_manual_file_installed)
        self.curseforge_controller.manual_files_installed.connect(self._curseforge_manual_files_installed)
        self.curseforge_controller.modpack_installed.connect(self._curseforge_modpack_installed)
        self.curseforge_controller.modpack_manual_download_required.connect(self._curseforge_modpack_manual_download_required)

        self.ftb_modpack_dialog.search_requested.connect(self.ftb_controller.search)
        self.ftb_modpack_dialog.refresh_requested.connect(lambda query, sort, index: self.ftb_controller.search(query, sort, index, force_refresh=True))
        self.ftb_modpack_dialog.project_details_requested.connect(self.ftb_controller.load_project_details)
        self.ftb_modpack_dialog.versions_requested.connect(self.ftb_controller.load_versions)
        self.ftb_modpack_dialog.version_details_requested.connect(self.ftb_controller.load_version_details)
        self.ftb_modpack_dialog.clear_cache_requested.connect(self.ftb_controller.clear_api_cache)
        self.ftb_modpack_dialog.install_modpack_requested.connect(self._install_ftb_modpack)
        self.ftb_modpack_dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.ftb_controller.search_results_changed.connect(self.ftb_modpack_dialog.set_search_result)
        self.ftb_controller.project_details_changed.connect(self.ftb_modpack_dialog.set_project_details)
        self.ftb_controller.versions_changed.connect(self.ftb_modpack_dialog.set_versions)
        self.ftb_controller.version_details_changed.connect(self.ftb_modpack_dialog.set_version_details)
        self.ftb_controller.cache_cleared.connect(lambda info: (self.ftb_modpack_dialog.set_cache_info(info), QMessageBox.information(self, tr("ftb.modpack.title"), tr("ftb.cache.cleared"))))
        self.ftb_controller.modpack_installed.connect(self._ftb_modpack_installed)

        self.atlauncher_modpack_dialog.search_requested.connect(self.atlauncher_controller.search)
        self.atlauncher_modpack_dialog.refresh_requested.connect(lambda query, sort, index: self.atlauncher_controller.search(query, sort, index, force_refresh=True))
        self.atlauncher_modpack_dialog.project_details_requested.connect(self.atlauncher_controller.load_project_details)
        self.atlauncher_modpack_dialog.versions_requested.connect(self.atlauncher_controller.load_versions)
        self.atlauncher_modpack_dialog.version_details_requested.connect(self.atlauncher_controller.load_version_details)
        self.atlauncher_modpack_dialog.clear_cache_requested.connect(self.atlauncher_controller.clear_api_cache)
        self.atlauncher_modpack_dialog.install_modpack_requested.connect(self._install_atlauncher_modpack)
        self.atlauncher_modpack_dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.atlauncher_controller.search_results_changed.connect(self.atlauncher_modpack_dialog.set_search_result)
        self.atlauncher_controller.project_details_changed.connect(self.atlauncher_modpack_dialog.set_project_details)
        self.atlauncher_controller.versions_changed.connect(self.atlauncher_modpack_dialog.set_versions)
        self.atlauncher_controller.version_details_changed.connect(self.atlauncher_modpack_dialog.set_version_details)
        self.atlauncher_controller.cache_cleared.connect(lambda info: (self.atlauncher_modpack_dialog.set_cache_info(info), QMessageBox.information(self, tr("atlauncher.modpack.title"), tr("atlauncher.cache.cleared"))))
        self.atlauncher_controller.modpack_installed.connect(self._atlauncher_modpack_installed)

        self.content_pack_manager_dialog.browse_requested.connect(self._open_content_pack_browser)
        self.content_pack_manager_dialog.import_requested.connect(self._import_content_pack)
        self.content_pack_manager_dialog.refresh_requested.connect(self._refresh_content_pack_entries)
        self.content_pack_manager_dialog.toggle_requested.connect(self._toggle_content_pack)
        self.content_pack_manager_dialog.remove_requested.connect(self._remove_content_pack)
        self.content_pack_manager_dialog.open_folder_requested.connect(self._open_content_pack_folder)
        for dialog in (self.resource_pack_browser_dialog, self.shader_pack_browser_dialog):
            dialog.search_requested.connect(self.content_pack_controller.search)
            dialog.versions_requested.connect(self.content_pack_controller.load_versions)
            dialog.project_details_requested.connect(self.content_pack_controller.load_project_details)
            dialog.install_modrinth_requested.connect(self.content_pack_controller.install_modrinth)
            dialog.install_curseforge_requested.connect(self._install_curseforge_content_pack)
            dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.content_pack_controller.search_results_changed.connect(self.resource_pack_browser_dialog.set_search_result)
        self.content_pack_controller.search_results_changed.connect(self.shader_pack_browser_dialog.set_search_result)
        self.content_pack_controller.search_failed.connect(self.resource_pack_browser_dialog.set_search_error)
        self.content_pack_controller.search_failed.connect(self.shader_pack_browser_dialog.set_search_error)
        self.content_pack_controller.versions_changed.connect(self.resource_pack_browser_dialog.set_versions)
        self.content_pack_controller.versions_changed.connect(self.shader_pack_browser_dialog.set_versions)
        self.content_pack_controller.files_changed.connect(self.resource_pack_browser_dialog.set_files)
        self.content_pack_controller.files_changed.connect(self.shader_pack_browser_dialog.set_files)
        self.content_pack_controller.project_details_changed.connect(self.resource_pack_browser_dialog.set_project_details)
        self.content_pack_controller.project_details_changed.connect(self.shader_pack_browser_dialog.set_project_details)
        self.content_pack_controller.entries_changed.connect(self.content_pack_manager_dialog.set_entries)
        self.content_pack_controller.installed.connect(self._content_pack_installed)
        self.curseforge_manual_dialog.files_selected.connect(self._install_manual_curseforge_files)

        self.launch_controller.progress_received.connect(self._on_progress)
        self.launch_controller.progress_received.connect(lambda _event: self.instance_controller.refresh_running())
        self.modrinth_controller.progress_received.connect(self._on_progress)
        self.curseforge_controller.progress_received.connect(self._on_progress)
        self.ftb_controller.progress_received.connect(self._on_progress)
        self.atlauncher_controller.progress_received.connect(self._on_progress)
        self.content_pack_controller.progress_received.connect(self._on_progress)
        self.mod_controller.progress_received.connect(self._on_progress)
        self.java_controller.progress_received.connect(self._on_progress)
        self.modpack_lifecycle_controller.progress_received.connect(self._on_progress)
        self.update_controller.progress_received.connect(self._on_progress)
        self.lan_hosting_controller.progress_received.connect(self._on_progress)
        self.lan_hosting_controller.prepared.connect(self._on_lan_hosting_prepared)
        self.launch_controller.launch_finished.connect(self.launch_control.set_result)
        self.launch_controller.launch_finished.connect(lambda _result: self.instance_controller.refresh_running(force=True))
        self.launch_controller.game_exited.connect(self._on_game_exited)
        self.launch_controller.pause_requested.connect(self.launch_control.set_pause_pending)
        self.launch_controller.launch_paused.connect(self._on_launch_paused)
        self.launch_controller.launch_resumed.connect(self._on_launch_resumed)
        self.launch_controller.cancel_requested.connect(self._on_launch_cancel_requested)
        self.launch_controller.launch_cancelled.connect(self._on_launch_cancelled)
        self.instance_controller.repair_progress.connect(self._on_progress)
        self.instance_controller.repair_progress.connect(self.repair_center_dialog.set_progress)
        self.instance_controller.loader_progress.connect(self._on_progress)
        self.instance_controller.package_progress.connect(self._on_progress)
        self.instance_controller.repair_finished.connect(self._on_repair_finished)
        self.instance_controller.repair_scan_finished.connect(self.repair_center_dialog.set_report)
        self.instance_controller.repair_execution_finished.connect(self.repair_center_dialog.set_repair_result)
        self.instance_controller.repair_center_failed.connect(self.repair_center_dialog.set_error)

        self.optifine_dialog.state_requested.connect(self.optifine_controller.load_state)
        self.optifine_dialog.install_requested.connect(self.optifine_controller.install)
        self.optifine_dialog.repair_requested.connect(self.optifine_controller.repair)
        self.optifine_dialog.uninstall_requested.connect(self.optifine_controller.uninstall)
        self.optifine_controller.state_ready.connect(self.optifine_dialog.set_state)
        self.optifine_controller.progress.connect(self._on_progress)
        self.optifine_controller.install_finished.connect(lambda result: self.instance_controller.refresh(result.instance_name))
        self.optifine_controller.repair_finished.connect(lambda result: self.instance_controller.refresh(result.instance_name))
        self.optifine_controller.uninstall_finished.connect(self.instance_controller.refresh)

        self.update_controller.update_available.connect(self._on_update_available)
        self.update_controller.no_update_available.connect(self._on_no_update_available)
        self.update_controller.update_prepared.connect(self._on_update_prepared)
        self.update_controller.update_check_failed.connect(self._on_update_check_failed)

        self.task_runner.task_started.connect(self._on_task_started)
        self.task_runner.task_failed.connect(self._on_task_failed)
        self.task_runner.task_succeeded.connect(self._on_task_completed)
        self.task_runner.task_succeeded.connect(self._on_task_succeeded)
        self.task_runner.task_failed.connect(self._on_task_completed)
        self.task_runner.task_settled.connect(self._on_task_settled)
        self.task_runner.busy_changed.connect(self._set_busy)
        self.task_runner.busy_changed.connect(self.mod_manager_dialog.set_busy)
        self.task_runner.task_rejected.connect(lambda message: QMessageBox.information(self, tr("MCW Launcher"), tr(message)))

        controllers = (
            self.version_controller,
            self.account_controller,
            self.backup_controller,
            self.java_controller,
            self.modpack_lifecycle_controller,
            self.instance_controller,
            self.mod_loader_controller,
            self.mod_controller,
            self.mod_catalog_controller,
            self.modrinth_controller,
            self.curseforge_controller,
            self.ftb_controller,
            self.atlauncher_controller,
            self.optifine_controller,
            self.content_pack_controller,
            self.content_library_controller,
            self.instance_settings_controller,
            self.gui_settings_controller,
            self.launch_controller,
            self.lan_hosting_controller,
            self.update_controller,
            self.storage_controller,
        )

        for controller in controllers:
            controller.status_changed.connect(self._set_status)
            controller.log_created.connect(self.logs_page.append)
            controller.error_created.connect(self._show_error)
            controller.network_retry_available.connect(
                lambda task_id, title, message, owner=controller: self._show_network_retry(owner, task_id, title, message)
            )

    def _initialize_data(self) -> None:
        settings = dict(self._startup_settings)
        self._apply_gui_settings(settings)

        restored_geometry = False
        if settings.get("remember_window_size", True):
            geometry = self.gui_settings_controller.saved_geometry()
            if geometry is not None:
                restored_geometry = bool(self.restoreGeometry(geometry))

        self._apply_display_profile_geometry(preserve_position=restored_geometry)
        QTimer.singleShot(0, lambda: self._apply_display_profile_geometry(preserve_position=True))

        self.show_page(settings.get("start_page", "instances"))
        self.account_controller.refresh()
        self.account_controller.audit_security()
        self.instance_controller.refresh()
        self.instance_controller.refresh_running(force=True)
        self.running_instances_timer.start()
        self.version_controller.refresh()
        self.java_controller.scan()
        self.logs_page.append(tr("Started {launcher_name}", launcher_name=LAUNCHER_NAME))
        if settings.get("auto_check_updates", True):
            QTimer.singleShot(1500, lambda: self.update_controller.check(manual=False))
        if settings.get("notify_legacy_cache_cleanup", True):
            QTimer.singleShot(2500, self.storage_controller.probe)

    def _review_legacy_storage(self) -> None:
        self.storage_controller.scan()

    def _on_legacy_storage_probe_ready(self, probe: object) -> None:
        if self._legacy_storage_notice_shown or not bool(self.gui_settings_controller.current.get("notify_legacy_cache_cleanup", True)):
            return
        if not bool(getattr(probe, "has_candidates", False)):
            return
        self._legacy_storage_notice_shown = True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle(tr("storage.legacy.startup.title"))
        box.setText(tr("storage.legacy.startup.message"))
        review = box.addButton(tr("storage.legacy.startup.review"), QMessageBox.ButtonRole.AcceptRole)
        later = box.addButton(tr("storage.legacy.startup.later"), QMessageBox.ButtonRole.RejectRole)
        disable = box.addButton(tr("storage.legacy.startup.disable"), QMessageBox.ButtonRole.ActionRole)
        box.setDefaultButton(review)
        box.buttonClicked.connect(lambda button: self._handle_legacy_storage_notice_button(button, review, disable))
        box.finished.connect(lambda _result: setattr(self, "_legacy_storage_notice", None))
        self._legacy_storage_notice = box
        box.open()

    def _handle_legacy_storage_notice_button(self, button: object, review_button: object, disable_button: object) -> None:
        if button is review_button:
            self._review_legacy_storage()
        elif button is disable_button:
            self.gui_settings_controller.set_notify_legacy_cache_cleanup(False)

    def _on_legacy_storage_plan_ready(self, plan: object) -> None:
        candidates = tuple(getattr(plan, "candidates", ()) or ())
        if not candidates:
            QMessageBox.information(self, tr("storage.legacy.none.title"), tr("storage.legacy.none.message"))
            return
        dialog = LegacyStorageCleanupDialog(plan, self)
        self._legacy_cleanup_dialog = dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._legacy_cleanup_dialog = None
            return
        selected = dialog.selected_candidate_ids()
        self._legacy_cleanup_dialog = None
        if selected:
            self.storage_controller.clean(plan, selected)

    def _on_legacy_storage_cleanup_completed(self, result: object) -> None:
        reclaimed = int(getattr(result, "reclaimed_bytes", 0) or 0)
        removed = len(tuple(getattr(result, "removed", ()) or ()))
        skipped = len(tuple(getattr(result, "skipped", ()) or ()))
        failures = len(tuple(getattr(result, "failures", ()) or ()))
        QMessageBox.information(
            self,
            tr("storage.legacy.completed.title"),
            tr("storage.legacy.completed.message", size=format_bytes(reclaimed), removed=removed, skipped=skipped, failed=failures),
        )

    def _refresh_all(self) -> None:
        self.account_controller.refresh()
        self.instance_controller.refresh()
        self.instance_controller.refresh_running(force=True)
        self.version_controller.refresh()
        self._set_status("Refreshing launcher data...")

    def show_page(self, page_id: str, *, record_history: bool = True) -> bool:
        requested_page = page_id if page_id in self.pages else "instances"
        current_page = self._current_page_id()
        if requested_page != current_page and not self._confirm_unsaved_page(current_page):
            self.sidebar.set_current_page(current_page)
            return False

        page = self.pages.get(requested_page, self.instances_page)
        self.motion_runtime.switch_page(self.content_stack, page)
        self.sidebar.set_current_page(requested_page)
        if record_history:
            self._record_page_history(requested_page)
        else:
            self._update_page_navigation()
        if requested_page == "mods" and self.mods_page.selected_provider == "modrinth" and not self.mods_page.has_loaded_search and not self.task_runner.is_task_active(f"{self.mod_catalog_controller.SEARCH_PREFIX}{self.mods_page.selected_loader}"):
            QTimer.singleShot(0, self.mods_page.start_search)
        return True

    def _record_page_history(self, page_id: str) -> None:
        normalized = str(page_id or "instances")
        if self._page_history_index >= 0 and self._page_history[self._page_history_index] == normalized:
            self._update_page_navigation()
            return
        del self._page_history[self._page_history_index + 1:]
        self._page_history.append(normalized)
        self._page_history_index = len(self._page_history) - 1
        self._update_page_navigation()

    def _navigate_page_history(self, offset: int) -> None:
        target_index = self._page_history_index + int(offset)
        if target_index < 0 or target_index >= len(self._page_history):
            self._update_page_navigation()
            return
        target_page = self._page_history[target_index]
        if self.show_page(target_page, record_history=False):
            self._page_history_index = target_index
            self._update_page_navigation()

    def _update_page_navigation(self) -> None:
        back_enabled = self._page_history_index > 0
        forward_enabled = 0 <= self._page_history_index < len(self._page_history) - 1
        back = getattr(self, "page_back_button", None)
        forward = getattr(self, "page_forward_button", None)
        if back is not None:
            back.setEnabled(back_enabled)
            back.setToolTip(tr("navigation.back"))
            back.setAccessibleName(tr("navigation.back"))
            back.setAccessibleDescription(tr("navigation.back.description"))
        if forward is not None:
            forward.setEnabled(forward_enabled)
            forward.setToolTip(tr("navigation.forward"))
            forward.setAccessibleName(tr("navigation.forward"))
            forward.setAccessibleDescription(tr("navigation.forward.description"))

    def _current_page_id(self) -> str:
        current = self.content_stack.currentWidget()
        return next((page_id for page_id, page in self.pages.items() if page is current), "instances")

    def _confirm_unsaved_page(self, page_id: str) -> bool:
        page = {
            "instance_settings": self.instance_settings_page,
            "launcher_settings": self.launcher_settings_page,
        }.get(page_id)
        if page is None or not page.is_dirty:
            return True

        scope = tr("navigation.instance_settings" if page_id == "instance_settings" else "navigation.launcher_settings")
        decision = prompt_unsaved_changes(self, scope)
        if decision is UnsavedChangesDecision.CANCEL:
            return False
        if decision is UnsavedChangesDecision.DISCARD:
            page.discard_changes()
            return True

        page.request_save()
        return not page.is_dirty

    def _confirm_all_unsaved_settings(self) -> bool:
        for page_id in ("instance_settings", "launcher_settings"):
            if not self._confirm_unsaved_page(page_id):
                return False
        return True

    def _request_instance_settings_load(self, instance_name: str) -> None:
        instance_name = instance_name.strip()
        page = self.instance_settings_page
        if page.is_dirty:
            scope = tr("navigation.instance_settings")
            decision = prompt_unsaved_changes(self, scope)
            if decision is UnsavedChangesDecision.CANCEL:
                page.revert_instance_selection()
                return
            if decision is UnsavedChangesDecision.DISCARD:
                page.discard_changes()
            else:
                page.request_save()
                if page.is_dirty:
                    page.revert_instance_selection()
                    return
        page.select_instance(instance_name)
        self.instance_settings_controller.load(instance_name)

    def _request_launch(self) -> None:
        if self._confirm_all_unsaved_settings():
            self.launch_controller.launch()

    def _open_instance_settings_workspace(self, instance_name: str) -> None:
        name = str(instance_name or "").strip()
        if not name:
            return
        self.instances_page.select_instance(name)
        self.instance_settings_page.select_instance(name)
        self.instance_settings_controller.load(name)
        self.show_page("instance_settings")

    def _open_repair_center(self, instance_name: str) -> None:
        name = str(instance_name or "").strip()
        if not name:
            QMessageBox.information(self, tr("repair.center.title"), tr("repair.center.no_instance"))
            return
        try:
            InstanceManager.load(name)
        except Exception as error:
            self._show_error(tr("repair.center.title"), str(error))
            return
        self.repair_center_dialog.set_instance(name)
        self.repair_center_dialog.show()
        self.repair_center_dialog.raise_()
        self.repair_center_dialog.activateWindow()

    def _open_mod_manager(self, instance_name: str) -> None:
        instance_name = instance_name.strip()
        if not instance_name:
            QMessageBox.information(self, tr("Mod Manager"), tr("Select an instance first."))
            return
        try:
            instance = InstanceManager.load(instance_name)
        except Exception as error:
            self._show_error(tr("Mod Manager"), str(error))
            return
        self.mod_controller.set_instance(instance)
        self.mod_manager_dialog.show()
        self.mod_manager_dialog.raise_()
        self.mod_manager_dialog.activateWindow()
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        if loader_name in ModLoaderManager.MODDED_LOADERS and not self.task_runner.is_task_active("mods.update.check"):
            QTimer.singleShot(0, lambda: self.mod_controller.check_updates(self.mod_manager_dialog.allowed_version_types, force_refresh=False))

    def _open_content_library(self, instance_name: str) -> None:
        name = str(instance_name or "").strip()
        if not name:
            QMessageBox.information(self, tr("content.library.title"), tr("Select an instance first."))
            return
        try:
            instance = InstanceManager.load(name)
        except Exception as error:
            self._show_error(tr("content.library.title"), str(error))
            return
        self.content_library_controller.set_instance(instance)
        self.content_library_dialog.show()
        self.content_library_dialog.raise_()
        self.content_library_dialog.activateWindow()

    def _open_content_library_folder(self, content_type: str) -> None:
        instance = self.content_library_controller.current_instance
        if instance is None:
            return
        try:
            path = InstalledContentLibraryManager.destination_folder(instance, content_type)
        except Exception as error:
            self._show_error(tr("content.library.title"), str(error))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_content_library_manager(self, content_type: str) -> None:
        instance = self.content_library_controller.current_instance
        if instance is None:
            return
        kind = str(content_type).strip().casefold()
        if kind == InstalledContentLibraryManager.MOD:
            self._open_mod_manager(instance.name)
            return
        if kind in {ContentPackManager.RESOURCE_PACK, ContentPackManager.SHADER_PACK}:
            self._open_content_pack_manager(instance.name)
            self.content_pack_manager_dialog.set_current_kind(kind)
            return
        QMessageBox.information(self, tr("content.library.title"), tr("content.library.modpack_manage_hint"))

    def _open_content_pack_manager(self, instance_name: str) -> None:
        name = str(instance_name or "").strip()
        if not name:
            QMessageBox.information(self, tr("content.manager.title"), tr("Select an instance first."))
            return
        try:
            instance = InstanceManager.load(name)
        except Exception as error:
            self._show_error(tr("content.manager.title"), str(error))
            return
        self.content_pack_manager_dialog.set_instance(instance)
        self.content_pack_manager_dialog.show()
        self.content_pack_manager_dialog.raise_()
        self.content_pack_manager_dialog.activateWindow()
        self.content_pack_controller.refresh_entries(name, ContentPackManager.RESOURCE_PACK)
        self.content_pack_controller.refresh_entries(name, ContentPackManager.SHADER_PACK)

    def _open_content_pack_browser(self, content_type: str) -> None:
        instance = self.content_pack_manager_dialog.instance
        if instance is None:
            QMessageBox.information(self, tr("content.manager.title"), tr("Select an instance first."))
            return
        kind = ContentPackManager.normalize_type(content_type)
        dialog = self.resource_pack_browser_dialog if kind == ContentPackManager.RESOURCE_PACK else self.shader_pack_browser_dialog
        dialog.set_instance(instance)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        dialog.set_searching(dialog.provider)
        self.content_pack_controller.search(dialog.provider, kind, "", "downloads", 0, instance.version_id)

    def _import_content_pack(self, content_type: str, source: object) -> None:
        instance = self.content_pack_manager_dialog.instance
        if instance is not None:
            self.content_pack_controller.import_local(instance.name, content_type, Path(source))

    def _refresh_content_pack_entries(self, content_type: str) -> None:
        instance = self.content_pack_manager_dialog.instance
        if instance is not None:
            self.content_pack_controller.refresh_entries(instance.name, content_type)

    def _toggle_content_pack(self, content_type: str, entry_id: str, enabled: bool) -> None:
        instance = self.content_pack_manager_dialog.instance
        if instance is not None:
            self.content_pack_controller.set_enabled(instance.name, content_type, entry_id, enabled)

    def _remove_content_pack(self, content_type: str, entry_id: str) -> None:
        instance = self.content_pack_manager_dialog.instance
        if instance is not None:
            self.content_pack_controller.remove(instance.name, content_type, entry_id)

    def _open_content_pack_folder(self, content_type: str) -> None:
        instance = self.content_pack_manager_dialog.instance
        if instance is None:
            return
        try:
            path = ContentPackManager.destination_dir(instance, content_type)
        except Exception as error:
            self._show_error(tr("content.manager.title"), str(error))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _install_curseforge_content_pack(self, instance_name: str, content_type: str, project_name: str, file: object) -> None:
        kind = ContentPackManager.normalize_type(content_type)
        dialog = self.resource_pack_browser_dialog if kind == ContentPackManager.RESOURCE_PACK else self.shader_pack_browser_dialog
        project = dialog.selected_project()
        project_url = str(getattr(project, "project_url", "") or "")
        self.content_pack_controller.install_curseforge(instance_name, kind, project_name, project_url, file)

    def _content_pack_installed(self, result: object) -> None:
        instance_name = str(getattr(result, "instance_name", "") or "")
        content_type = str(getattr(result, "content_type", "") or "")
        if instance_name and content_type:
            self.content_pack_controller.refresh_entries(instance_name, content_type)
        kind_name = tr("content.kind.resourcepack") if content_type == ContentPackManager.RESOURCE_PACK else tr("content.kind.shader")
        message = tr("content.install.success", kind=kind_name, name=str(getattr(result, "project_name", "") or getattr(result, "file_name", "")))
        if content_type == ContentPackManager.SHADER_PACK and instance_name and not self._shader_environment_available(instance_name):
            message += "\n\n" + tr("content.shader.environment_warning")
        QMessageBox.information(self, tr("content.manager.title"), message)

    @staticmethod
    def _shader_environment_available(instance_name: str) -> bool:
        try:
            instance = InstanceManager.load(instance_name)
        except Exception:
            return False
        mods_dir = Path(instance.instance_dir) / "minecraft" / "mods"
        if not mods_dir.is_dir():
            return False
        markers = ("iris", "oculus", "optifine", "canvas")
        return any(path.is_file() and any(marker in path.name.casefold() for marker in markers) for path in mods_dir.iterdir())

    def _open_modrinth_mod_browser(self) -> None:
        instance = self.mod_controller.current_instance
        if instance is None:
            QMessageBox.information(self, tr("modrinth.title"), tr("modrinth.mod.no_instance"))
            return
        self.modrinth_mod_dialog.set_instance(instance)
        self.modrinth_mod_dialog.show()
        self.modrinth_mod_dialog.raise_()
        self.modrinth_mod_dialog.activateWindow()
        self.modrinth_mod_dialog.set_searching(self.modrinth_mod_dialog.selected_loader)
        self.modrinth_controller.search("mod", "", "downloads", 0, game_version=instance.version_id, loader=self.modrinth_mod_dialog.selected_loader)

    def _open_modrinth_modpacks(self) -> None:
        self.modrinth_modpack_dialog.set_instance(None)
        self.modrinth_modpack_dialog.show()
        self.modrinth_modpack_dialog.raise_()
        self.modrinth_modpack_dialog.activateWindow()
        self.modrinth_modpack_dialog.set_searching(self.modrinth_modpack_dialog.selected_loader)
        self.modrinth_controller.search("modpack", "", "downloads", 0, loader=self.modrinth_modpack_dialog.selected_loader)

    def _search_modrinth_mods(self, project_type: str, query: str, index: str, offset: int, loader: str) -> None:
        self.modrinth_controller.search(project_type, query, index, offset, game_version=self.modrinth_mod_dialog.game_version, loader=loader)

    def _search_modrinth_modpacks(self, project_type: str, query: str, index: str, offset: int, loader: str) -> None:
        self.modrinth_controller.search(project_type, query, index, offset, loader=loader)

    def _install_modrinth_mod(self, version_id: str, loader: str) -> None:
        instance = self.mod_controller.current_instance
        if instance is None:
            QMessageBox.information(self, tr("modrinth.title"), tr("modrinth.mod.no_instance"))
            return
        instance_loader, _ = ModLoaderManager.normalize(instance.mod_loader)
        if instance_loader != loader:
            QMessageBox.information(self, tr("modrinth.title"), tr("modrinth.loader.instance_mismatch", instance_loader=instance_loader.title(), selected_loader=loader.title()))
            return
        self.modrinth_controller.install_mod(instance.name, version_id, self.modrinth_mod_dialog.allowed_version_types)

    def _choose_instance_for_mod_install(self, version: object, loader: str, allowed_version_types: object) -> None:
        try:
            instances = list(InstanceManager.list_instances())
            dialog = CompatibleInstanceDialog(version, loader, instances, self)
        except Exception as error:
            self._show_error(tr("mods.instance_dialog.title"), str(error))
            return

        if not dialog.exec():
            return
        if dialog.requested_instance_creation:
            self._pending_mod_install_after_create = {
                "provider": "modrinth",
                "instance_name": dialog.created_instance_name,
                "version_id": str(getattr(version, "version_id", "")),
                "loader": str(loader).strip().lower(),
                "allowed_version_types": tuple(allowed_version_types),
            }
            started = self.instance_controller.create(
                dialog.created_instance_name,
                dialog.created_game_version,
                loader,
                ModLoaderManager.AUTO,
            )
            if not started:
                self._pending_mod_install_after_create = None
            return

        instance_name = dialog.selected_instance_name
        if not instance_name:
            return
        try:
            target_instance = InstanceManager.load(instance_name)
        except Exception as error:
            self._show_error(tr("mods.instance_dialog.title"), str(error))
            return
        self.mod_controller.set_instance(target_instance, refresh=False)
        self.modrinth_controller.install_mod(instance_name, str(getattr(version, "version_id", "")), tuple(allowed_version_types))

    def _on_task_settled(self, task_id: str, succeeded: bool, result: object) -> None:
        if task_id != self.instance_controller.CREATE_TASK_ID:
            return

        pending = self._pending_mod_install_after_create
        if pending is None:
            return

        self._pending_mod_install_after_create = None
        if not succeeded:
            self.logs_page.append(tr("mods.instance_create.followup_cancelled"))
            return

        instance_name = str(getattr(result, "name", ""))
        expected_name = str(pending.get("instance_name", ""))
        if not instance_name or instance_name != expected_name:
            self._show_error(
                tr("mods.instance_create.title"),
                tr("mods.instance_create.result_mismatch", name=expected_name),
            )
            return

        try:
            instance = InstanceManager.load(instance_name)
            actual_loader, _ = ModLoaderManager.normalize(instance.mod_loader)
        except Exception as error:
            self._show_error(tr("mods.instance_create.title"), str(error))
            return

        expected_loader = str(pending.get("loader", "")).strip().lower()
        if actual_loader != expected_loader:
            self._show_error(
                tr("mods.instance_create.title"),
                tr(
                    "mods.instance_create.loader_mismatch",
                    expected=expected_loader.title(),
                    actual=actual_loader.title(),
                ),
            )
            return

        allowed_version_types = tuple(pending.get("allowed_version_types", ("release",)))
        self.mod_controller.set_instance(instance, refresh=False)
        provider = str(pending.get("provider", "modrinth"))
        if provider == "curseforge":
            started = self.curseforge_controller.install_mod(
                instance_name,
                int(pending.get("project_id", 0) or 0),
                int(pending.get("file_id", 0) or 0),
                allowed_version_types,
                allow_unverified=bool(pending.get("allow_unverified", False)),
            )
            title = tr("curseforge.mod.install")
        else:
            started = self.modrinth_controller.install_mod(
                instance_name,
                str(pending.get("version_id", "")),
                allowed_version_types,
            )
            title = tr("modrinth.mod.install")
        if not started:
            self._show_error(title, tr("mods.instance_create.install_start_failed", name=instance_name))

    def _set_modrinth_results(self, project_type: str, loader: str, result: object) -> None:
        dialog = self.modrinth_mod_dialog if project_type == "mod" else self.modrinth_modpack_dialog
        dialog.set_search_result(result, loader)

    def _set_modrinth_search_error(self, project_type: str, loader: str, message: str) -> None:
        dialog = self.modrinth_mod_dialog if project_type == "mod" else self.modrinth_modpack_dialog
        dialog.set_search_error(loader, message)

    def _set_modrinth_versions(self, project_type: str, project_id: str, loader: str, versions: list) -> None:
        dialog = self.modrinth_mod_dialog if project_type == "mod" else self.modrinth_modpack_dialog
        dialog.set_versions(project_id, versions, loader)

    def _set_modrinth_project_details(self, project_type: str, project_id: str, loader: str, project: object) -> None:
        dialog = self.modrinth_mod_dialog if project_type == "mod" else self.modrinth_modpack_dialog
        dialog.set_project_details(project_type, project_id, loader, project)
        if project_type == "mod":
            self.mods_page.set_modrinth_project_details(project_id, loader, project)

    def _modrinth_mod_installed(self, result: object) -> None:
        self.mod_controller.refresh()
        if self.mod_manager_dialog.isVisible():
            self.mod_controller.check_updates(self.mod_manager_dialog.allowed_version_types, force_refresh=False)
        count = len(getattr(result, "installed_files", ()) or ())
        warnings = tuple(getattr(result, "warnings", ()) or ())
        message = tr("modrinth.mod.installed", count=count)
        if warnings:
            message += "\n\n" + "\n".join(str(item) for item in warnings)
        manual_downloads = tuple(getattr(result, "manual_downloads", ()) or ())
        if manual_downloads:
            message += "\n\n" + tr("artifact.manual.pending", provider="Modrinth", count=len(manual_downloads))
        QMessageBox.information(self, tr("modrinth.mod.install"), message)
        if manual_downloads:
            self._modrinth_pending_modpack_install = None
            self._modrinth_manual_instance_name = str(getattr(result, "instance_name", ""))
            try:
                manual_instance = InstanceManager.load(self._modrinth_manual_instance_name)
                self.modrinth_manual_dialog.set_instance_context(manual_instance.name, manual_instance.instance_dir)
            except Exception:
                self.modrinth_manual_dialog.set_instance_context(self._modrinth_manual_instance_name, None)
            self.modrinth_manual_dialog.set_requirements(manual_downloads)
            self.modrinth_manual_dialog.show()
            self.modrinth_manual_dialog.raise_()
            self.modrinth_manual_dialog.activateWindow()

    def _modrinth_modpack_installed(self, result: object) -> None:
        instance = getattr(result, "instance", None)
        selected_name = str(getattr(instance, "name", ""))
        self.instance_controller.refresh(selected_name=selected_name)
        self.modrinth_modpack_dialog.close()
        if self._modrinth_pending_modpack_install is not None:
            self.modrinth_manual_dialog.mark_installed(self._modrinth_pending_modpack_install.requirement)
            self.modrinth_manual_dialog.close()
            self._modrinth_pending_modpack_install = None
        QMessageBox.information(self, tr("modrinth.modpack.install"), tr("modrinth.modpack.installed", name=selected_name))

    def _install_manual_modrinth_files(self, sources: object) -> None:
        paths = [Path(source) for source in sources] if isinstance(sources, (list, tuple)) else []
        if not paths:
            return
        if self._modrinth_pending_modpack_install is not None:
            if len(paths) != 1:
                QMessageBox.warning(self, tr("artifact.manual.modpack_archive_title", provider="Modrinth"), tr("artifact.manual.modpack_single_file", provider="Modrinth"))
                return
            self.modrinth_controller.install_manual_modpack(self._modrinth_pending_modpack_install, paths[0])
            return
        if not self._modrinth_manual_instance_name:
            QMessageBox.warning(self, tr("artifact.manual.title", provider="Modrinth"), tr("curseforge.mod.no_instance"))
            return
        started = self.modrinth_controller.install_manual_files(
            self._modrinth_manual_instance_name,
            self.modrinth_manual_dialog.remaining_requirements,
            paths,
            launch_lock_token=self._manual_launch_lock_token or None,
        )
        self.modrinth_manual_dialog.set_import_busy(started)

    def _modrinth_manual_files_installed(self, instance_name: str, result: object) -> None:
        imported = tuple(getattr(result, "imported", ()) or ())
        added_mods = tuple(getattr(result, "added_mods", ()) or ())
        rejected = tuple(getattr(result, "rejected", ()) or ())
        for item in imported:
            requirement = getattr(item, "requirement", None)
            if requirement is not None:
                self.modrinth_manual_dialog.mark_installed(requirement)
        if self.mod_controller.current_instance is not None and self.mod_controller.current_instance.name == instance_name:
            self.mod_controller.refresh()
        lines = []
        if imported:
            lines.append(tr("artifact.manual.batch_imported", provider="Modrinth", count=len(imported)))
        if added_mods:
            lines.append(tr("curseforge.manual.batch_added", count=len(added_mods)))
        if rejected:
            lines.append(tr("curseforge.manual.batch_rejected", count=len(rejected)))
            lines.append("\n".join(f"- {message}" for message in rejected[:12]))
        if self.modrinth_manual_dialog.remaining_count == 0:
            lines.append(tr("curseforge.manual.all_imported"))
        elif imported:
            lines.append(tr("curseforge.manual.remaining", count=self.modrinth_manual_dialog.remaining_count))
        message = "\n\n".join(lines) or tr("curseforge.manual.batch_no_files")
        if rejected:
            QMessageBox.warning(self, tr("artifact.manual.title", provider="Modrinth"), message)
        else:
            QMessageBox.information(self, tr("artifact.manual.title", provider="Modrinth"), message)
        self._resume_launch_after_manual_content("modrinth", instance_name, self.modrinth_manual_dialog)

    def _on_launch_manual_content_required(self, error: Exception) -> None:
        if isinstance(error, CurseForgeManagedFilesRequired):
            self._manual_launch_provider = "curseforge"
            self._manual_launch_lock_token = str(getattr(error, "launch_lock_token", "") or "")
            self._curseforge_pending_modpack_install = None
            self._curseforge_manual_instance_name = error.instance_name
            self.curseforge_manual_dialog.set_instance_context(error.instance_name, error.instance_dir)
            self.curseforge_manual_dialog.set_requirements(error.requirements)
            dialog = self.curseforge_manual_dialog
            provider = "CurseForge"
        elif isinstance(error, ModrinthManagedFilesRequired):
            self._manual_launch_provider = "modrinth"
            self._manual_launch_lock_token = str(getattr(error, "launch_lock_token", "") or "")
            self._modrinth_pending_modpack_install = None
            self._modrinth_manual_instance_name = error.instance_name
            self.modrinth_manual_dialog.set_instance_context(error.instance_name, error.instance_dir)
            self.modrinth_manual_dialog.set_requirements(error.requirements)
            dialog = self.modrinth_manual_dialog
            provider = "Modrinth"
        else:
            return

        status = tr("artifact.manual.launch_paused", provider=provider, count=len(error.requirements))
        self.home_page.set_status(status)
        self.right_panel.set_status(status)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _resume_launch_after_manual_content(self, provider: str, instance_name: str, dialog: object) -> None:
        if self._manual_launch_provider != str(provider).strip().casefold():
            return
        if not self.launch_controller.waiting_for_manual_content or getattr(dialog, "remaining_count", 1) != 0:
            return
        expected_instance = self._curseforge_manual_instance_name if provider == "curseforge" else self._modrinth_manual_instance_name
        if expected_instance and expected_instance != instance_name:
            return
        dialog.close()
        self._manual_launch_provider = ""
        self._manual_launch_lock_token = ""
        self.launch_controller.resume_manual_content()

    def _modrinth_modpack_manual_download_required(self, request: object) -> None:
        if not isinstance(request, ModrinthModpackManualDownloadRequired):
            self._show_error(tr("modrinth.modpack.install"), "Invalid Modrinth manual download request.")
            return
        self._modrinth_pending_modpack_install = request
        self._modrinth_manual_instance_name = ""
        self.modrinth_manual_dialog.set_instance_context(request.instance_name, None)
        self.modrinth_manual_dialog.set_requirements([request.requirement])
        self.modrinth_manual_dialog.show()
        self.modrinth_manual_dialog.raise_()
        self.modrinth_manual_dialog.activateWindow()


    def _require_curseforge_gateway(self) -> bool:
        if CurseForgeConfigManager.is_configured():
            return True
        QMessageBox.information(self, tr("curseforge.title"), tr("curseforge.gateway.required"))
        return False

    def _search_curseforge_catalog(self, query: str, sort: str, index: int, loader: str) -> None:
        if not self._require_curseforge_gateway():
            self.mods_page.set_curseforge_search_error(loader, tr("curseforge.gateway.required"))
            return
        self.curseforge_controller.search(
            "mod",
            query,
            sort,
            index,
            loader=loader,
            context=CurseForgeController.CATALOG_CONTEXT,
        )

    def _refresh_curseforge_catalog(self, query: str, sort: str, index: int, loader: str) -> None:
        if not self._require_curseforge_gateway():
            self.mods_page.set_curseforge_search_error(loader, tr("curseforge.gateway.required"))
            return
        self.curseforge_controller.search(
            "mod",
            query,
            sort,
            index,
            loader=loader,
            force_refresh=True,
            manual_refresh=True,
            context=CurseForgeController.CATALOG_CONTEXT,
        )

    def _load_curseforge_catalog_files(self, project_id: int, loader: str, allowed_release_types: object) -> None:
        self.curseforge_controller.load_files(
            "mod",
            int(project_id),
            "",
            loader,
            tuple(allowed_release_types),
            context=CurseForgeController.CATALOG_CONTEXT,
        )

    def _refresh_curseforge_catalog_files(self, project_id: int, loader: str, allowed_release_types: object) -> None:
        self.curseforge_controller.load_files(
            "mod",
            int(project_id),
            "",
            loader,
            tuple(allowed_release_types),
            force_refresh=True,
            context=CurseForgeController.CATALOG_CONTEXT,
        )

    def _on_curseforge_catalog_failed(self, operation: str, loader: str, message: str) -> None:
        if operation == "search":
            self.mods_page.set_curseforge_search_error(loader, message)
            return
        if operation.startswith("files:"):
            try:
                project_id = int(operation.partition(":")[2])
            except ValueError:
                project_id = 0
            self.mods_page.set_curseforge_files_error(project_id, loader, message)
            return
        self._show_error(tr("curseforge.title"), message)

    def _open_curseforge_catalog(self, loader: str) -> None:
        if not self._require_curseforge_gateway():
            return
        try:
            self.curseforge_mod_dialog.set_catalog_loader(loader)
        except Exception as error:
            self._show_error(tr("curseforge.title"), str(error))
            return
        self.curseforge_mod_dialog.show()
        self.curseforge_mod_dialog.raise_()
        self.curseforge_mod_dialog.activateWindow()

    def _open_curseforge_mod_browser(self) -> None:
        if not self._require_curseforge_gateway():
            return
        instance = self.mod_controller.current_instance
        loader = ModLoaderManager.normalize(instance.mod_loader)[0] if instance is not None else ""
        if instance is None or loader not in ModLoaderManager.MODDED_LOADERS:
            QMessageBox.information(self, tr("curseforge.title"), tr("curseforge.mod.no_instance"))
            return
        self.curseforge_mod_dialog.set_instance(instance)
        self.curseforge_mod_dialog.show()
        self.curseforge_mod_dialog.raise_()
        self.curseforge_mod_dialog.activateWindow()

    def _open_curseforge_modpacks(self) -> None:
        if not self._require_curseforge_gateway():
            return
        self.curseforge_modpack_dialog.set_instance(None)
        self.curseforge_modpack_dialog.show()
        self.curseforge_modpack_dialog.raise_()
        self.curseforge_modpack_dialog.activateWindow()

    def _open_ftb_modpacks(self) -> None:
        self.ftb_modpack_dialog.show()
        self.ftb_modpack_dialog.raise_()
        self.ftb_modpack_dialog.activateWindow()
        self.ftb_modpack_dialog.set_searching()
        self.ftb_controller.search("", "popularity", 0)

    def _open_atlauncher_modpacks(self) -> None:
        self.atlauncher_modpack_dialog.show()
        self.atlauncher_modpack_dialog.raise_()
        self.atlauncher_modpack_dialog.activateWindow()
        self.atlauncher_modpack_dialog.set_searching()
        self.atlauncher_controller.search("", "popularity", 0)

    def _search_curseforge_mods(self, project_type: str, query: str, sort: str, index: int) -> None:
        self.curseforge_controller.search(project_type, query, sort, index, game_version=self.curseforge_mod_dialog.game_version, loader=self.curseforge_mod_dialog.loader)

    def _search_curseforge_modpacks(self, project_type: str, query: str, sort: str, index: int) -> None:
        self.curseforge_controller.search(project_type, query, sort, index, loader=self.curseforge_modpack_dialog.loader)

    def _refresh_curseforge_mods(self, project_type: str, query: str, sort: str, index: int) -> None:
        self.curseforge_controller.search(project_type, query, sort, index, game_version=self.curseforge_mod_dialog.game_version, loader=self.curseforge_mod_dialog.loader, force_refresh=True, manual_refresh=True)

    def _refresh_curseforge_modpacks(self, project_type: str, query: str, sort: str, index: int) -> None:
        self.curseforge_controller.search(project_type, query, sort, index, loader=self.curseforge_modpack_dialog.loader, force_refresh=True, manual_refresh=True)

    def _install_curseforge_mod(self, project_id: int, file_id: int, allowed_release_types: object) -> None:
        if self.curseforge_mod_dialog.catalog_mode:
            file = self.curseforge_mod_dialog.selected_file()
            if file is None:
                return
            self._choose_instance_for_curseforge_install(file, self.curseforge_mod_dialog.loader, tuple(allowed_release_types))
            return
        instance = self.mod_controller.current_instance
        if instance is None:
            QMessageBox.information(self, tr("curseforge.title"), tr("curseforge.mod.no_instance"))
            return
        file = self.curseforge_mod_dialog.selected_file()
        allow_unverified = self._confirm_curseforge_unverified_install(file, instance)
        if allow_unverified is None:
            return
        self.curseforge_controller.install_mod(instance.name, int(project_id), int(file_id), tuple(allowed_release_types), allow_unverified=allow_unverified)

    def _choose_instance_for_curseforge_install(self, file: object, loader: str, allowed_release_types: tuple[str, ...]) -> None:
        try:
            instances = list(InstanceManager.list_instances())
            dialog = CompatibleInstanceDialog(file, loader, instances, self)
        except Exception as error:
            self._show_error(tr("mods.instance_dialog.title"), str(error))
            return
        if not dialog.exec():
            return
        if dialog.requested_instance_creation:
            allow_unverified = self._confirm_curseforge_unverified_install(file, str(loader))
            if allow_unverified is None:
                return
            self._pending_mod_install_after_create = {
                "provider": "curseforge",
                "instance_name": dialog.created_instance_name,
                "project_id": int(getattr(file, "project_id", 0) or 0),
                "file_id": int(getattr(file, "file_id", 0) or 0),
                "loader": str(loader).strip().lower(),
                "allowed_version_types": tuple(allowed_release_types),
                "allow_unverified": allow_unverified,
            }
            started = self.instance_controller.create(dialog.created_instance_name, dialog.created_game_version, loader, ModLoaderManager.AUTO)
            if not started:
                self._pending_mod_install_after_create = None
            return
        instance_name = dialog.selected_instance_name
        if not instance_name:
            return
        try:
            target_instance = InstanceManager.load(instance_name)
        except Exception as error:
            self._show_error(tr("mods.instance_dialog.title"), str(error))
            return
        allow_unverified = self._confirm_curseforge_unverified_install(file, target_instance)
        if allow_unverified is None:
            return
        self.mod_controller.set_instance(target_instance, refresh=False)
        self.curseforge_controller.install_mod(
            instance_name,
            int(getattr(file, "project_id", 0) or 0),
            int(getattr(file, "file_id", 0) or 0),
            tuple(allowed_release_types),
            allow_unverified=allow_unverified,
        )

    def _confirm_curseforge_unverified_install(self, file: object | None, instance_or_loader: object) -> bool | None:
        if file is None:
            return False
        if isinstance(instance_or_loader, str):
            loader = CurseForgeClient.normalize_loader(instance_or_loader)
        else:
            loader, _ = ModLoaderManager.normalize(getattr(instance_or_loader, "mod_loader", ""))
        status = CurseForgeClient.loader_compatibility(file, loader)
        if status in {"compatible", "universal"}:
            return False
        answer = QMessageBox.warning(
            self,
            tr("curseforge.mod.unverified_warning.title"),
            tr(
                "curseforge.mod.unverified_warning.message",
                file=str(getattr(file, "file_name", "") or getattr(file, "display_name", "")),
                loader=loader.title(),
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return True if answer == QMessageBox.StandardButton.Yes else None

    def _prompt_modpack_settings(self, instance_name: str, recommended_min_memory_mb: int = 0, recommended_max_memory_mb: int = 0) -> dict | None:
        settings = SettingsManager.normalize_dict(self.gui_settings_controller.current.get("instance_defaults", {}))
        java = settings.setdefault("java", {})
        recommended_minimum = max(0, int(recommended_min_memory_mb or 0))
        recommended_maximum = max(0, int(recommended_max_memory_mb or 0))
        if recommended_maximum > 0:
            java["max_memory"] = recommended_maximum
        if recommended_minimum > 0:
            java["min_memory"] = recommended_minimum
        settings = SettingsManager.normalize_dict(settings)
        dialog = InstanceSettingsEditorDialog(settings, self, title=tr("modpack.settings.title", name=instance_name))
        if recommended_maximum > 0:
            dialog.description_label.setText(tr("modpack.settings.description_recommended", memory=recommended_maximum))
        else:
            dialog.description_label.setText(tr("modpack.settings.description_defaults"))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.settings_data

    def _install_modrinth_modpack(self, project_id: str, version_id: str, instance_name: str, install_optional_files: bool, allowed_version_types: object, loader: str) -> None:
        settings = self._prompt_modpack_settings(str(instance_name))
        if settings is None:
            self.modrinth_modpack_dialog.set_busy(False)
            return
        self.modrinth_controller.install_modpack(
            str(project_id),
            str(version_id),
            str(instance_name),
            bool(install_optional_files),
            tuple(allowed_version_types) if isinstance(allowed_version_types, (list, tuple, set)) else ("release",),
            str(loader),
            settings,
        )

    def _install_ftb_modpack(self, project_id: int, version_id: int, instance_name: str, install_optional_files: bool, allowed_release_types: object) -> None:
        version = self.ftb_modpack_dialog.selected_version
        recommended_minimum = int(getattr(version, "minimum_memory_mb", 0) or 0)
        recommended_maximum = int(getattr(version, "recommended_memory_mb", 0) or 0)
        settings = self._prompt_modpack_settings(str(instance_name), recommended_minimum, recommended_maximum)
        if settings is None:
            self.ftb_modpack_dialog.set_busy(False)
            return
        self.ftb_controller.install_modpack(
            int(project_id),
            int(version_id),
            str(instance_name),
            bool(install_optional_files),
            tuple(allowed_release_types) if isinstance(allowed_release_types, (list, tuple, set)) else ("release",),
            settings,
        )

    def _install_atlauncher_modpack(self, safe_name: str, version_name: str, instance_name: str, install_optional_files: bool, allowed_release_types: object) -> None:
        version = self.atlauncher_modpack_dialog.selected_version
        recommended_minimum = int(getattr(version, "minimum_memory_mb", 0) or 0)
        recommended_maximum = int(getattr(version, "recommended_memory_mb", 0) or 0)
        settings = self._prompt_modpack_settings(str(instance_name), recommended_minimum, recommended_maximum)
        if settings is None:
            self.atlauncher_modpack_dialog.set_busy(False)
            return
        self.atlauncher_controller.install_modpack(
            str(safe_name),
            str(version_name),
            str(instance_name),
            bool(install_optional_files),
            tuple(allowed_release_types) if isinstance(allowed_release_types, (list, tuple, set)) else ("release",),
            settings,
        )

    def _install_curseforge_modpack(self, project_id: int, file_id: int, instance_name: str, install_optional_files: bool, allowed_release_types: object, expected_loader: str) -> None:
        self._curseforge_pending_modpack_install = None
        settings = self._prompt_modpack_settings(str(instance_name))
        if settings is None:
            self.curseforge_modpack_dialog.set_busy(False)
            return
        self.curseforge_controller.install_modpack(
            int(project_id),
            int(file_id),
            str(instance_name),
            bool(install_optional_files),
            tuple(allowed_release_types) if isinstance(allowed_release_types, (list, tuple, set)) else ("release",),
            str(expected_loader),
            settings,
        )

    def _set_curseforge_results(self, project_type: str, loader: str, result: object) -> None:
        dialog = self.curseforge_mod_dialog if project_type == "mod" else self.curseforge_modpack_dialog
        dialog.set_search_result(result, loader)

    def _set_curseforge_files(self, project_type: str, project_id: int, loader: str, files: list) -> None:
        dialog = self.curseforge_mod_dialog if project_type == "mod" else self.curseforge_modpack_dialog
        dialog.set_files(project_id, files, loader)

    def _set_curseforge_project_details(self, project_type: str, project_id: int, loader: str, project: object) -> None:
        dialog = self.curseforge_mod_dialog if project_type == "mod" else self.curseforge_modpack_dialog
        dialog.set_project_details(project_type, project_id, loader, project)
        if project_type == "mod":
            self.mods_page.set_curseforge_project_details(project_id, loader, project)

    def _set_curseforge_cache_info(self, project_type: str, info: object) -> None:
        dialog = self.curseforge_mod_dialog if project_type == "mod" else self.curseforge_modpack_dialog
        dialog.set_cache_info(info)

    def _curseforge_mod_installed(self, result: object) -> None:
        self.mod_controller.refresh()
        count = len(getattr(result, "installed_files", ()) or ())
        warnings = tuple(getattr(result, "warnings", ()) or ())
        manual_downloads = tuple(getattr(result, "manual_downloads", ()) or ())
        message = tr("curseforge.mod.installed", count=count)
        if warnings:
            message += "\n\n" + "\n".join(str(item) for item in warnings)
        if manual_downloads:
            message += "\n\n" + tr("artifact.manual.pending", provider="CurseForge", count=len(manual_downloads))
        QMessageBox.information(self, tr("curseforge.mod.install"), message)
        if manual_downloads:
            self._curseforge_pending_modpack_install = None
            self._curseforge_manual_instance_name = str(getattr(result, "instance_name", ""))
            try:
                manual_instance = InstanceManager.load(self._curseforge_manual_instance_name)
                self.curseforge_manual_dialog.set_instance_context(manual_instance.name, manual_instance.instance_dir)
            except Exception:
                self.curseforge_manual_dialog.set_instance_context(self._curseforge_manual_instance_name, None)
            self.curseforge_manual_dialog.set_requirements(manual_downloads)
            self.curseforge_manual_dialog.show()
            self.curseforge_manual_dialog.raise_()
            self.curseforge_manual_dialog.activateWindow()

    def _install_manual_curseforge_file(self, requirement: object, source: object) -> None:
        if not self._curseforge_manual_instance_name:
            QMessageBox.warning(self, tr("curseforge.manual.title"), tr("curseforge.mod.no_instance"))
            return
        self.curseforge_controller.install_manual_file(
            self._curseforge_manual_instance_name,
            requirement,
            Path(source),
            launch_lock_token=self._manual_launch_lock_token or None,
        )

    def _install_manual_curseforge_files(self, sources: object) -> None:
        paths = [Path(source) for source in sources] if isinstance(sources, (list, tuple)) else []
        if not paths:
            return
        if self._curseforge_pending_modpack_install is not None:
            if len(paths) != 1:
                QMessageBox.warning(self, tr("curseforge.manual.modpack_archive_title"), tr("curseforge.manual.modpack_single_file"))
                return
            self.curseforge_controller.install_manual_modpack(self._curseforge_pending_modpack_install, paths[0])
            return
        if not self._curseforge_manual_instance_name:
            QMessageBox.warning(self, tr("curseforge.manual.title"), tr("curseforge.mod.no_instance"))
            return
        started = self.curseforge_controller.install_manual_files(
            self._curseforge_manual_instance_name,
            self.curseforge_manual_dialog.remaining_requirements,
            paths,
            launch_lock_token=self._manual_launch_lock_token or None,
        )
        self.curseforge_manual_dialog.set_import_busy(started)

    def _curseforge_manual_file_installed(self, instance_name: str, requirement: object, installed_name: str) -> None:
        self.curseforge_manual_dialog.mark_installed(requirement)
        if self.mod_controller.current_instance is not None and self.mod_controller.current_instance.name == instance_name:
            self.mod_controller.refresh()
        message = tr("curseforge.manual.imported", name=installed_name)
        if self.curseforge_manual_dialog.remaining_count == 0:
            message += "\n\n" + tr("curseforge.manual.all_imported")
        QMessageBox.information(self, tr("curseforge.manual.title"), message)
        self._resume_launch_after_manual_content("curseforge", instance_name, self.curseforge_manual_dialog)

    def _curseforge_manual_files_installed(self, instance_name: str, result: object) -> None:
        imported = tuple(getattr(result, "imported", ()) or ())
        added_mods = tuple(getattr(result, "added_mods", ()) or ())
        rejected = tuple(getattr(result, "rejected", ()) or ())
        for item in imported:
            requirement = getattr(item, "requirement", None)
            if requirement is not None:
                self.curseforge_manual_dialog.mark_installed(requirement)
        if self.mod_controller.current_instance is not None and self.mod_controller.current_instance.name == instance_name:
            self.mod_controller.refresh()

        lines: list[str] = []
        if imported:
            lines.append(tr("curseforge.manual.batch_imported", count=len(imported)))
        if added_mods:
            lines.append(tr("curseforge.manual.batch_added", count=len(added_mods)))
        if rejected:
            lines.append(tr("curseforge.manual.batch_rejected", count=len(rejected)))
            lines.append("\n".join(f"- {message}" for message in rejected[:12]))
            if len(rejected) > 12:
                lines.append(tr("curseforge.manual.batch_more_rejected", count=len(rejected) - 12))
        if self.curseforge_manual_dialog.remaining_count == 0:
            lines.append(tr("curseforge.manual.all_imported"))
        elif imported:
            lines.append(tr("curseforge.manual.remaining", count=self.curseforge_manual_dialog.remaining_count))
        if not lines:
            lines.append(tr("curseforge.manual.batch_no_files"))

        message = "\n\n".join(lines)
        if rejected:
            QMessageBox.warning(self, tr("curseforge.manual.title"), message)
        else:
            QMessageBox.information(self, tr("curseforge.manual.title"), message)
        self._resume_launch_after_manual_content("curseforge", instance_name, self.curseforge_manual_dialog)

    def _curseforge_modpack_manual_download_required(self, request: object) -> None:
        if not isinstance(request, CurseForgeModpackManualDownloadRequired):
            self._show_error(tr("curseforge.modpack.install"), tr("curseforge.manual.modpack_request_invalid"))
            return
        self._curseforge_pending_modpack_install = request
        self._curseforge_manual_instance_name = ""
        self.curseforge_manual_dialog.set_instance_context(request.instance_name, None)
        self.curseforge_manual_dialog.set_requirements([request.requirement])
        self.curseforge_manual_dialog.show()
        self.curseforge_manual_dialog.raise_()
        self.curseforge_manual_dialog.activateWindow()

    def _curseforge_modpack_installed(self, result: object) -> None:
        instance = getattr(result, "instance", None)
        selected_name = str(getattr(instance, "name", ""))
        if self._curseforge_pending_modpack_install is not None:
            self.curseforge_manual_dialog.mark_installed(self._curseforge_pending_modpack_install.requirement)
            self.curseforge_manual_dialog.close()
            self._curseforge_pending_modpack_install = None
        self.instance_controller.refresh(selected_name=selected_name)
        self.curseforge_modpack_dialog.close()
        QMessageBox.information(self, tr("curseforge.modpack.install"), tr("curseforge.modpack.installed", name=selected_name))


    def _ftb_modpack_installed(self, result: object) -> None:
        instance = getattr(result, "instance", None)
        selected_name = str(getattr(instance, "name", ""))
        self.instance_controller.refresh(selected_name=selected_name)
        self.ftb_modpack_dialog.close()
        QMessageBox.information(self, tr("ftb.modpack.install"), tr("ftb.modpack.installed", name=selected_name))



    def _atlauncher_modpack_installed(self, result: object) -> None:
        instance = getattr(result, "instance", None)
        selected_name = str(getattr(instance, "name", ""))
        self.instance_controller.refresh(selected_name=selected_name)
        self.atlauncher_modpack_dialog.close()
        QMessageBox.information(self, tr("atlauncher.modpack.install"), tr("atlauncher.modpack.installed", name=selected_name))


    def _request_lan_hosting_prepare(self, instance_name: str, auth_mode: str, connection_provider: str) -> None:
        if self.instance_settings_page.is_dirty:
            self.instance_settings_page.request_save()
            if self.instance_settings_page.is_dirty:
                return

        if str(auth_mode) in {"private_offline", "friends"}:
            answer = QMessageBox.warning(
                self,
                tr("lan.hosting.warning.title"),
                tr("lan.hosting.warning.message"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.instance_settings_page.set_lan_prepare_status(tr("lan.hosting.preparing"))
        self.lan_hosting_controller.prepare(instance_name, auth_mode, connection_provider)

    def _open_lan_agent_log(self, instance_name: str) -> None:
        name = str(instance_name).strip()
        if not name:
            QMessageBox.information(self, tr("lan.agent.log.title"), tr("lan.agent.log.select_instance"))
            return
        try:
            instance = InstanceManager.load(name)
            log_path = LanAgentManager.log_path(instance)
        except Exception as error:
            self._show_error(tr("lan.agent.log.title"), str(error))
            return
        LanAgentLogDialog(log_path, self).exec()

    def _on_lan_hosting_prepared(self, result: object) -> None:
        installed = tuple(getattr(result, "installed_projects", ()) or ())
        reused = tuple(getattr(result, "reused_projects", ()) or ())
        disabled = tuple(getattr(result, "disabled_projects", ()) or ())
        warnings = tuple(getattr(result, "warnings", ()) or ())
        auth_mode = str(getattr(result, "auth_mode", "microsoft_only"))
        connection_provider = str(getattr(result, "connection_provider", "manual"))

        lines = [tr("lan.hosting.prepared.summary")]
        if installed:
            lines.append(tr("lan.hosting.prepared.installed", projects=", ".join(installed)))
        if reused:
            lines.append(tr("lan.hosting.prepared.reused", projects=", ".join(reused)))
        if disabled:
            lines.append(tr("lan.hosting.prepared.disabled", projects=", ".join(disabled)))
        if auth_mode == "private_offline":
            lines.append(tr("lan.hosting.prepared.private_offline_steps"))
        else:
            lines.append(tr("lan.hosting.prepared.microsoft_steps"))
        if connection_provider == "e4mc":
            lines.append(tr("lan.hosting.prepared.e4mc_steps"))
        else:
            lines.append(tr("lan.hosting.prepared.manual_steps"))
        if warnings:
            lines.append(tr("common.warning") + "\n" + "\n".join(str(item) for item in warnings))

        message = "\n\n".join(lines)
        self.instance_settings_page.set_lan_prepare_status(tr("lan.hosting.ready"))
        current = self.mod_controller.current_instance
        if current is not None and current.name == str(getattr(result, "instance_name", "")):
            self.mod_controller.refresh()
        QMessageBox.information(self, tr("lan.hosting.title"), message)

    def _open_java_folder(self, installation: object) -> None:
        if installation is None:
            return
        executable = Path(getattr(installation, "executable", ""))
        directory = executable.parent.parent if executable.parent.name.casefold() == "bin" else executable.parent
        if not directory.exists():
            self._show_error(tr("Java installations"), tr("The selected Java directory no longer exists."))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory.resolve())))

    def _open_optifine(self, name: str) -> None:
        normalized = str(name or "").strip()
        if not normalized:
            return
        try:
            instance = InstanceManager.load(normalized)
        except Exception as error:
            self._show_error(tr("optifine.title"), str(error))
            return
        self.optifine_dialog.open_for_instance(instance)

    def _open_instance_folder(self, instance_name: str) -> None:
        name = str(instance_name).strip()
        if not name:
            QMessageBox.information(self, tr("Instances"), tr("Select an instance first."))
            return
        try:
            instance = InstanceManager.load(name)
            directory = Path(instance.instance_dir)
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as error:
            self._show_error(tr("Instances"), str(error))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory.resolve())))

    def _open_backups_folder(self, instance_name: str) -> None:
        name = str(instance_name).strip()
        if not name:
            return
        try:
            directory = Paths.instance_backups_dir(InstanceManager.load(name))
        except Exception as error:
            self._show_error(tr("Instance backups"), str(error))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory.resolve())))

    def _on_backup_created(self, result: object) -> None:
        backup = getattr(result, "backup", None)
        path = getattr(backup, "path", "")
        self.instance_controller.refresh(selected_name=str(getattr(self._selected_instance, "name", "")))
        self.toast_manager.show(
            tr("Backup created successfully:\n{path}", path=path),
            "success",
            tr("Instance backup"),
        )

    def _on_backup_restored(self, result: object) -> None:
        name = str(getattr(result, "instance_name", ""))
        safety = getattr(result, "safety_backup", None)
        self.instance_controller.refresh(selected_name=name)
        message = tr("Backup restored successfully for '{name}'.", name=name)
        if safety:
            message += tr("\nSafety backup: {path}", path=safety)
        self.toast_manager.show(message, "success", tr("Restore backup"))

    def _on_modpack_update_checked(self, info: object) -> None:
        self.instances_page.set_modpack_update_info(info)
        if info is not None and getattr(info, "available", False):
            self.logs_page.append(tr("Modpack update available: {current} → {target}", current=getattr(info, "current_version_number", "?"), target=getattr(info, "target_version_number", "?")))

    def _on_modpack_update_previewed(self, plan: object) -> None:
        blockers = tuple(getattr(plan, "blockers", ()) or ())
        if blockers:
            QMessageBox.warning(
                self,
                tr("modpack.preview.title"),
                tr("modpack.preview.blocked", reasons="\n".join(f"• {reason}" for reason in blockers)),
            )
            return
        download_mib = float(getattr(plan, "estimated_download_bytes", 0) or 0) / (1024 * 1024)
        message = tr(
            "modpack.preview.confirm",
            name=getattr(plan, "instance_name", "?"),
            current=getattr(plan, "current_version", "?"),
            target=getattr(plan, "target_version", "?"),
            added=getattr(plan, "added_files", 0),
            replaced=getattr(plan, "replaced_files", 0),
            removed=getattr(plan, "removed_files", 0),
            preserved=len(tuple(getattr(plan, "preserved_files", ()) or ())),
            unchanged=getattr(plan, "unchanged_files", 0),
            download=download_mib,
        )
        answer = QMessageBox.question(
            self,
            tr("modpack.preview.title"),
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.modpack_lifecycle_controller.update(
                str(getattr(plan, "instance_name", "")),
                self.modrinth_modpack_dialog.allowed_version_types,
                target_version_id=str(getattr(plan, "target_version_id", "")),
            )

    def _on_modpack_updated(self, result: object) -> None:
        name = str(getattr(result, "instance_name", ""))
        self.instance_controller.refresh(selected_name=name)
        preserved = tuple(getattr(result, "preserved_files", ()) or ())
        message = tr("Updated '{name}' to modpack version {version}.", name=name, version=getattr(result, "target_version", "?"))
        if preserved:
            message += tr("\n{count} user-modified file(s) were preserved.", count=len(preserved))
        message += tr("\nSafety backup: {path}", path=getattr(result, "backup_path", ""))
        self.toast_manager.show(message, "success", tr("Update Modrinth modpack"))

    def _on_modpack_repaired(self, result: object) -> None:
        name = str(getattr(result, "instance_name", ""))
        self.instance_controller.refresh(selected_name=name)
        repaired = int(getattr(result, "repaired_files", 0))
        message = tr("Repaired '{name}' using modpack version {version}. Restored {count} managed file(s).", name=name, version=getattr(result, "pack_version", "?"), count=repaired)
        backup_path = getattr(result, "backup_path", None)
        if backup_path:
            message += tr("\nSafety backup: {path}", path=backup_path)
        else:
            message += tr("\nNo damaged managed files were found, so no backup was needed.")
        self.toast_manager.show(message, "success", tr("Repair Modrinth modpack"))

    def _on_game_exited(self, result: object) -> None:
        selected_name = str(getattr(self._selected_instance, "name", ""))
        result_name = str(getattr(result, "instance_name", ""))
        if not selected_name or selected_name == result_name:
            self.launch_control.set_exit_result(result)
        self.instance_controller.refresh_running(force=True)
        self.instance_controller.refresh(selected_name=result_name or selected_name)
        crashed = bool(getattr(result, "crashed", False))
        instance_name = str(getattr(result, "instance_name", "Minecraft"))
        exit_code = int(getattr(result, "exit_code", -1))
        duration = int(getattr(result, "duration_seconds", 0))
        if crashed:
            message = tr("Minecraft crashed: {name} (exit code {code})", name=instance_name, code=exit_code)
            self.home_page.set_status(message)
            self.right_panel.set_status(message)
            self.logs_page.append(tr("Crash detected after {seconds} second(s).", seconds=duration))
            crash_report = getattr(result, "crash_report_path", None)
            if crash_report:
                self.logs_page.append(tr("Crash report: {path}", path=crash_report))
        else:
            message = tr("Minecraft closed normally: {name}", name=instance_name)
            self.home_page.set_status(message)
            self.right_panel.set_status(message)
            self.logs_page.append(tr("Game session completed in {seconds} second(s).", seconds=duration))

    def _on_repair_finished(self, result: object) -> None:
        instance_name = str(getattr(result, "instance_name", ""))
        libraries = int(getattr(result, "libraries_checked", 0))
        self.launch_control.reset_progress()
        self.logs_page.append(tr("Repair completed for '{name}'. Libraries checked: {count}.", name=instance_name, count=libraries))
        self.toast_manager.show(
            tr("Repair completed for '{name}'. Client, libraries, assets, natives, mod loader, and Java were verified.", name=instance_name),
            "success",
            tr("Repair instance"),
        )

    def _on_update_available(self, info: UpdateInfo, manual: bool) -> None:
        if not manual and info.version in self._prompted_update_versions:
            return
        self._prompted_update_versions.add(info.version)
        self.launcher_settings_page.set_update_status(tr("update.status.available", version=info.version))

        decision = UpdateDialog.ask(info, self)
        if decision == UpdateDialog.DONT_ASK_AGAIN:
            self.gui_settings_controller.set_auto_check_updates(False)
            self.launcher_settings_page.set_update_status(tr("update.status.auto_disabled"))
            return
        if decision == UpdateDialog.UPDATE_NOW:
            if not WindowsUpdateInstaller.is_supported():
                QMessageBox.information(self, tr("update.error.title"), tr("update.error.packaged_only"))
                return
            blocked_reason = self._update_install_block_reason()
            if blocked_reason:
                QMessageBox.warning(self, tr("update.error.title"), blocked_reason)
                self.launcher_settings_page.set_update_status(tr("update.status.waiting"))
                return
            self.update_controller.prepare(info)

    def _on_no_update_available(self, manual: bool) -> None:
        self.launcher_settings_page.set_update_status(tr("update.status.latest"))
        if manual:
            QMessageBox.information(self, tr("update.latest.title"), tr("update.latest.message"))

    def _on_update_check_failed(self, error: Exception, manual: bool) -> None:
        self.launcher_settings_page.set_update_status(tr("update.status.failed"))
        if manual:
            QMessageBox.warning(self, tr("update.error.title"), tr("update.error.check_failed", error=error))

    def _on_update_prepared(self, prepared: PreparedUpdate) -> None:
        blocked_reason = self._update_install_block_reason()
        if blocked_reason:
            self.launcher_settings_page.set_update_status(tr("update.status.waiting"))
            QMessageBox.warning(self, tr("update.error.title"), blocked_reason)
            return
        self.launcher_settings_page.set_update_status(tr("update.status.installing"))
        QTimer.singleShot(0, lambda: self._launch_prepared_update(prepared))

    def _update_install_block_reason(self) -> str | None:
        active_tasks = [task_id for task_id in self.task_runner.active_task_ids if not task_id.startswith("update.")]
        if active_tasks:
            return tr("update.error.tasks_running", count=len(active_tasks))
        running_instances = InstanceRunLock.list_active()
        if running_instances:
            names = ", ".join(item.name for item in running_instances[:4])
            if len(running_instances) > 4:
                names += f" (+{len(running_instances) - 4})"
            return tr("update.error.instances_running", names=names)
        return None

    def _launch_prepared_update(self, prepared: PreparedUpdate) -> None:
        try:
            WindowsUpdateInstaller.launch(prepared)
        except (AutomaticUpdateUnsupportedError, OSError, RuntimeError) as error:
            self._show_error(tr("update.error.title"), str(error))
            self.launcher_settings_page.set_update_status(tr("update.status.failed"))
            return
        self.close()

    def _account_selected(self, account: object | None) -> None:
        self.home_page.set_account(account)
        self.right_panel.set_account(account)
        self.instances_page.set_account(account)
        self.launch_controller.set_account(account)

    def _instance_selected(self, instance: object | None) -> None:
        previous_instance = self._selected_instance
        previous_name = str(getattr(previous_instance, "name", ""))
        next_name = str(getattr(instance, "name", ""))

        if self._restoring_instance_selection:
            self._restoring_instance_selection = False
        elif previous_name != next_name and self.instance_settings_page.is_dirty:
            scope = tr("navigation.instance_settings")
            decision = prompt_unsaved_changes(self, scope)
            if decision is UnsavedChangesDecision.CANCEL:
                self._restore_selected_instance(previous_name)
                return
            if decision is UnsavedChangesDecision.DISCARD:
                self.instance_settings_page.discard_changes()
            else:
                self.instance_settings_page.request_save()
                if self.instance_settings_page.is_dirty:
                    self._restore_selected_instance(previous_name)
                    return

        self._selected_instance = instance
        self.home_page.set_instance(instance)
        self.right_panel.set_instance(instance)
        self.launch_control.set_selected_instance(instance)
        self.launch_controller.set_instance(instance)

        if instance is not None:
            self.instances_page.select_instance(instance.name)
            self.instance_settings_page.select_instance(instance.name)
            self.instance_settings_controller.load(instance.name)
            if (Path(instance.instance_dir) / ".mcw" / "modrinth-pack.json").is_file():
                QTimer.singleShot(0, lambda name=instance.name: self.modpack_lifecycle_controller.scan(name))

    def _restore_selected_instance(self, instance_name: str) -> None:
        self._restoring_instance_selection = True
        self.instances_page.select_instance(instance_name)
        self.instance_settings_page.revert_instance_selection()
        QTimer.singleShot(0, lambda: self.instance_controller.select(instance_name))

    def _apply_gui_settings(self, settings: dict) -> None:
        requested_locale = str(settings.get("language", "en-US"))
        language_manager.reload()
        # Language changes are committed to settings but applied only after a
        # clean process restart. Keeping the active session locale unchanged
        # prevents a partially translated widget tree and mixed-language dialogs.
        language_manager.set_language(self._session_locale, notify=False)
        self.launcher_settings_page.set_settings(settings, preserve_unsaved=self.launcher_settings_page.is_dirty)
        self.instances_page.set_show_snapshots(bool(settings.get("show_snapshots", False)))
        self.launch_controller.set_debug_mode(bool(settings.get("debug_mode", False)))
        self.update_controller.set_channel(str(settings.get("update_channel", "stable")))
        include_beta = bool(settings.get("modrinth_include_beta", False))
        include_alpha = bool(settings.get("modrinth_include_alpha", False))
        self.mods_page.set_channel_preferences(include_beta, include_alpha)
        self.modrinth_mod_dialog.set_channel_preferences(include_beta, include_alpha)
        self.modrinth_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.curseforge_mod_dialog.set_channel_preferences(include_beta, include_alpha)
        self.curseforge_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.ftb_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.atlauncher_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.resource_pack_browser_dialog.set_channel_preferences(include_beta, include_alpha)
        self.shader_pack_browser_dialog.set_channel_preferences(include_beta, include_alpha)
        self.mod_manager_dialog.set_channel_preferences(include_beta, include_alpha)
        show_content_descriptions = bool(settings.get("show_content_descriptions", False))
        self.mods_page.set_show_project_descriptions(show_content_descriptions)
        self.modrinth_mod_dialog.set_show_project_descriptions(show_content_descriptions)
        self.modrinth_modpack_dialog.set_show_project_descriptions(show_content_descriptions)
        self.curseforge_mod_dialog.set_show_project_descriptions(show_content_descriptions)
        self.curseforge_modpack_dialog.set_show_project_descriptions(show_content_descriptions)
        self.ftb_modpack_dialog.set_show_project_descriptions(show_content_descriptions)
        self.atlauncher_modpack_dialog.set_show_project_descriptions(show_content_descriptions)
        self.resource_pack_browser_dialog.set_show_project_descriptions(show_content_descriptions)
        self.shader_pack_browser_dialog.set_show_project_descriptions(show_content_descriptions)
        curseforge_available = bool(settings.get("curseforge_gateway_urls", ()))
        self.instances_page.browse_curseforge_modpacks_button.setVisible(curseforge_available)
        self.mod_manager_dialog.curseforge_button.setVisible(curseforge_available)
        self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, str(settings.get("theme", "mcw-default")), bool(settings.get("show_static_text", False)), str(settings.get("accent_mode", "theme")), str(settings.get("accent_color", "#8ed35b")), str(settings.get("text_color_mode", "theme")), str(settings.get("text_color", "#f4f4f4")))
        self.motion_runtime.apply(settings.get("motion_mode", "full"))
        self._retranslate_ui()

        if requested_locale == self._session_locale:
            self._pending_restart_locale = ""
            self._dismissed_restart_locale = ""
        else:
            self._schedule_language_restart_prompt(requested_locale)

    def _preview_theme(self, theme_id: str) -> None:
        selected = self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, theme_id, self.launcher_settings_page.show_static_text.isChecked(), self.launcher_settings_page.current_accent_mode(), self.launcher_settings_page.current_accent_color(), self.launcher_settings_page.current_text_color_mode(), self.launcher_settings_page.current_text_color())
        self.motion_runtime.apply(self.launcher_settings_page.current_motion_mode())
        self.logs_page.append(f"Theme preview: {selected}")
        self.toast_manager.show(
            tr("motion.preview.theme_reloaded", theme=selected),
            "success",
            tr("motion.preview.toast.title"),
        )

    def _reload_theme_silently(self, theme_id: str) -> None:
        selected = self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, theme_id, self.launcher_settings_page.show_static_text.isChecked(), self.launcher_settings_page.current_accent_mode(), self.launcher_settings_page.current_accent_color(), self.launcher_settings_page.current_text_color_mode(), self.launcher_settings_page.current_text_color())
        self.motion_runtime.apply(self.launcher_settings_page.current_motion_mode())
        self.logs_page.append(f"Theme live reload: {selected}")

    def _preview_motion(self, mode: str) -> None:
        self.motion_runtime.apply(mode)

    def _preview_accent(self, mode: str, color: str) -> None:
        theme_id = str(self.launcher_settings_page.theme_combo.currentData() or "mcw-default")
        self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, theme_id, self.launcher_settings_page.show_static_text.isChecked(), mode, color, self.launcher_settings_page.current_text_color_mode(), self.launcher_settings_page.current_text_color())

    def _preview_text_color(self, mode: str, color: str) -> None:
        theme_id = str(self.launcher_settings_page.theme_combo.currentData() or "mcw-default")
        self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, theme_id, self.launcher_settings_page.show_static_text.isChecked(), self.launcher_settings_page.current_accent_mode(), self.launcher_settings_page.current_accent_color(), mode, color)

    def _set_modrinth_channel_preferences(self, include_beta: bool, include_alpha: bool) -> None:
        self.mods_page.set_channel_preferences(include_beta, include_alpha)
        self.modrinth_mod_dialog.set_channel_preferences(include_beta, include_alpha)
        self.modrinth_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.curseforge_mod_dialog.set_channel_preferences(include_beta, include_alpha)
        self.curseforge_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.ftb_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.atlauncher_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.resource_pack_browser_dialog.set_channel_preferences(include_beta, include_alpha)
        self.shader_pack_browser_dialog.set_channel_preferences(include_beta, include_alpha)
        self.mod_manager_dialog.set_channel_preferences(include_beta, include_alpha)
        self.gui_settings_controller.set_modrinth_channels(include_beta, include_alpha)

    def _run_first_run_setup(self) -> None:
        if self.launcher_settings_page.is_dirty:
            decision = prompt_unsaved_changes(self, tr("launcher_settings.page.title"))
            if decision is UnsavedChangesDecision.CANCEL:
                return
            if decision is UnsavedChangesDecision.DISCARD:
                self.launcher_settings_page.discard_changes()
            else:
                self.launcher_settings_page.request_save()
                if self.launcher_settings_page.is_dirty:
                    return

        from mcw_core.api.config.launcher_settings_manager import LauncherSettingsManager
        from mcw_core.api.hardware.first_run_recommendation_service import FirstRunRecommendationService
        from src.gui.dialogs.first_run_setup_dialog import FirstRunSetupDialog

        self.launcher_settings_page.first_run_setup_button.setEnabled(False)
        try:
            try:
                recommendation = FirstRunRecommendationService.inspect()
            except Exception:
                recommendation = FirstRunRecommendationService.fallback()
            manager = LauncherSettingsManager()
            dialog = FirstRunSetupDialog(manager.load(), self._gpu_detection, recommendation, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                self._retranslate_ui()
                self.toast_manager.show(tr("launcher_settings.first_run.cancelled"), "warning", tr("launcher_settings.first_run.title"))
                return
            manager.save(dialog.selected_settings())
            self.gui_settings_controller.load()
            self.launcher_settings_page.set_gpu_detection(self._gpu_detection)
            self.toast_manager.show(tr("launcher_settings.first_run.completed"), "success", tr("launcher_settings.first_run.title"))
        except Exception as error:
            QMessageBox.warning(self, tr("launcher_settings.first_run.title"), tr("launcher_settings.first_run.failed", error=error))
        finally:
            self.launcher_settings_page.first_run_setup_button.setEnabled(True)

    def _schedule_language_restart_prompt(self, locale: str) -> None:
        requested = str(locale or "en-US")
        if requested == self._session_locale or requested == self._dismissed_restart_locale:
            return
        self._pending_restart_locale = requested
        if self._language_restart_prompt_scheduled:
            return
        self._language_restart_prompt_scheduled = True
        QTimer.singleShot(0, self._prompt_language_restart)

    def _prompt_language_restart(self) -> None:
        self._language_restart_prompt_scheduled = False
        self._legacy_storage_notice_shown = False
        self._legacy_storage_notice = None
        self._legacy_cleanup_dialog = None
        locale = self._pending_restart_locale
        if not locale or locale == self._session_locale:
            return

        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setWindowTitle(tr("language.restart.title"))
        message_box.setText(tr("language.restart.message"))
        message_box.setInformativeText(tr("language.restart.detail"))
        restart_button = message_box.addButton(tr("language.restart.now"), QMessageBox.ButtonRole.AcceptRole)
        later_button = message_box.addButton(tr("language.restart.later"), QMessageBox.ButtonRole.RejectRole)
        message_box.setDefaultButton(restart_button)
        message_box.setEscapeButton(later_button)
        message_box.exec()

        if message_box.clickedButton() is restart_button:
            self._restart_for_language_change()
            return

        self._dismissed_restart_locale = locale
        self.toast_manager.show(tr("language.restart.saved_for_later"), "warning", tr("language.restart.title"))

    def _restart_for_language_change(self) -> None:
        if self.task_runner.has_active_tasks:
            QMessageBox.information(self, tr("language.restart.title"), tr("language.restart.active_task"))
            return
        if not self._confirm_all_unsaved_settings():
            return
        if self.gui_settings_controller.current.get("remember_window_size", True):
            self.gui_settings_controller.save_geometry(self.saveGeometry())
        if not start_restarted_process():
            QMessageBox.critical(self, tr("language.restart.title"), tr("language.restart.failed"))
            return
        self.task_runner.close()
        application = QGuiApplication.instance()
        if application is not None:
            application.quit()

    def _retranslate_ui(self) -> None:
        retranslate_widget_tree(self)
        self.setWindowTitle(tr(LAUNCHER_NAME))
        self._update_page_navigation()

        for widget in (
            self.sidebar,
            self.home_page,
            self.account_page,
            self.instances_page,
            self.mods_page,
            self.instance_settings_page,
            self.launcher_settings_page,
            self.launch_control,
            self.right_panel,
            self.mod_manager_dialog,
            self.modrinth_mod_dialog,
            self.modrinth_modpack_dialog,
            self.curseforge_mod_dialog,
            self.curseforge_modpack_dialog,
            self.ftb_modpack_dialog,
            self.atlauncher_modpack_dialog,
            self.content_pack_manager_dialog,
            self.content_library_dialog,
            self.resource_pack_browser_dialog,
            self.shader_pack_browser_dialog,
            self.curseforge_manual_dialog,
            self.portable_manual_dialog,
            self.repair_center_dialog,
        ):
            retranslate_dynamic = getattr(widget, "retranslate_dynamic", None)
            if callable(retranslate_dynamic):
                retranslate_dynamic()
        self.theme_runtime.reapply_assets(self)

    def _on_task_started(self, task_id: str, message: str, blocking: bool) -> None:
        if blocking:
            self._suppress_loader_progress = False
        if task_id == self.launch_controller.TASK_ID:
            self._set_launch_active(True)

        profile = task_progress_profile(task_id)
        if profile is not None:
            self._on_progress(ProgressEvent(stage=profile.stage, message=message))

        if task_id == "mods.update.check":
            self.mod_manager_dialog.set_update_checking(True)
        if task_id.startswith("modpack."):
            self.instances_page.set_modpack_busy(True)
        if task_id.startswith("update."):
            self.launcher_settings_page.set_update_busy(True)
            self.launcher_settings_page.set_update_status(message)
        if task_id.startswith("modrinth."):
            self._modrinth_tasks.add(task_id)
            self.modrinth_mod_dialog.set_busy(True)
            self.modrinth_modpack_dialog.set_busy(True)
        if task_id.startswith("mod_catalog."):
            self._mod_catalog_tasks.add(task_id)
            self.mods_page.set_busy(True)
        if task_id.startswith("ftb."):
            self._ftb_tasks.add(task_id)
            self.ftb_modpack_dialog.set_busy(True)
        if task_id.startswith("atlauncher."):
            self._atlauncher_tasks.add(task_id)
            self.atlauncher_modpack_dialog.set_busy(True)
        if task_id.startswith("content."):
            self._content_tasks.add(task_id)
            self.content_pack_manager_dialog.set_busy(True)
            self.content_library_dialog.set_busy(True)
            self.resource_pack_browser_dialog.set_busy(True)
            self.shader_pack_browser_dialog.set_busy(True)
        if task_id.startswith("curseforge."):
            self._curseforge_tasks.add(task_id)
            self.curseforge_mod_dialog.set_busy(True)
            self.curseforge_modpack_dialog.set_busy(True)
            if ".catalog." in task_id or task_id.endswith(".catalog"):
                self._curseforge_catalog_tasks.add(task_id)
                self.mods_page.set_busy(True)
        if profile is None and (blocking or not self.task_runner.is_busy):
            self._set_status(message)

    def _on_task_succeeded(self, task_id: str, _result: object) -> None:
        completion_messages = {
            self.instance_controller.CREATE_TASK_ID: ("loader.progress.instance_ready", "loader.progress.instance_ready_detail"),
            self.instance_controller.LOADER_CHANGE_TASK_ID: ("loader.progress.ready", "loader.progress.ready_detail"),
            self.instance_controller.LOADER_REPAIR_TASK_ID: ("loader.progress.repaired", "loader.progress.repaired_detail"),
            self.instance_controller.FORGE_RESTORE_TASK_ID: ("loader.progress.restored", "loader.progress.restored_detail"),
        }
        completion = completion_messages.get(task_id)
        if completion is not None:
            self._suppress_loader_progress = True
            status, detail = completion
            QTimer.singleShot(0, lambda: self.launch_control.set_operation_completed(status, detail))
            return

        profile = task_progress_profile(task_id)
        if profile is None or task_id == self.launch_controller.TASK_ID:
            return
        event = ProgressEvent(stage=profile.stage, message=profile.success_message, state=ProgressState.SUCCEEDED, detail=profile.success_detail)
        QTimer.singleShot(0, lambda event=event: self._on_progress(event))

    def _on_task_completed(self, task_id: str, _result: object) -> None:
        if task_id == "curseforge.install.manual.batch":
            self.curseforge_manual_dialog.set_import_busy(False)
        elif task_id == "modrinth.install.manual.batch":
            self.modrinth_manual_dialog.set_import_busy(False)
        if task_id == self.launch_controller.TASK_ID:
            self._set_launch_active(False)
            if self._manual_launch_provider:
                dialog = self.curseforge_manual_dialog if self._manual_launch_provider == "curseforge" else self.modrinth_manual_dialog
                dialog.close()
                self._manual_launch_provider = ""
                self._manual_launch_lock_token = ""
        if task_id == "mods.update.check":
            self.mod_manager_dialog.set_update_checking(False)
        if task_id.startswith("modpack."):
            self.instances_page.set_modpack_busy(False)
        if task_id.startswith("update."):
            self.launcher_settings_page.set_update_busy(False)
        if task_id.startswith("modrinth."):
            self._modrinth_tasks.discard(task_id)
            busy = bool(self._modrinth_tasks)
            self.modrinth_mod_dialog.set_busy(busy)
            self.modrinth_modpack_dialog.set_busy(busy)
        if task_id.startswith("mod_catalog."):
            self._mod_catalog_tasks.discard(task_id)
            self.mods_page.set_busy(self.task_runner.is_busy or bool(self._mod_catalog_tasks) or bool(self._curseforge_catalog_tasks))
        if task_id.startswith("ftb."):
            self._ftb_tasks.discard(task_id)
            self.ftb_modpack_dialog.set_busy(bool(self._ftb_tasks))
        if task_id.startswith("atlauncher."):
            self._atlauncher_tasks.discard(task_id)
            self.atlauncher_modpack_dialog.set_busy(bool(self._atlauncher_tasks))
        if task_id.startswith("content."):
            self._content_tasks.discard(task_id)
            busy = bool(self._content_tasks)
            self.content_pack_manager_dialog.set_busy(busy)
            self.content_library_dialog.set_busy(busy)
            self.resource_pack_browser_dialog.set_busy(busy)
            self.shader_pack_browser_dialog.set_busy(busy)
        if task_id.startswith("curseforge."):
            self._curseforge_tasks.discard(task_id)
            busy = bool(self._curseforge_tasks)
            self.curseforge_mod_dialog.set_busy(busy)
            self.curseforge_modpack_dialog.set_busy(busy)
            if ".catalog." in task_id or task_id.endswith(".catalog"):
                self._curseforge_catalog_tasks.discard(task_id)
                self.mods_page.set_busy(self.task_runner.is_busy or bool(self._mod_catalog_tasks) or bool(self._curseforge_catalog_tasks))

    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == self.instance_controller.CREATE_TASK_ID:
            self._pending_mod_install_after_create = None
        if task_id == "mods.update.check":
            self.mod_manager_dialog.set_update_error(str(error))
        if task_id == self.launch_controller.TASK_ID:
            if isinstance(error, CompatibilityConfirmationRequired):
                self.instance_controller.refresh_running(force=True)
                return
            if is_download_cancelled(error):
                self._on_launch_cancelled()
                self.instance_controller.refresh_running(force=True)
                return
            if is_download_paused(error):
                self._on_launch_paused()
                self.instance_controller.refresh_running(force=True)
                return
            if isinstance(error, CurseForgeManagedFilesRequired):
                self._curseforge_pending_modpack_install = None
                self._curseforge_manual_instance_name = error.instance_name
                self.curseforge_manual_dialog.set_instance_context(error.instance_name, error.instance_dir)
                self.curseforge_manual_dialog.set_requirements(error.requirements)
                status = tr("artifact.manual.launch_blocked", provider="CurseForge", count=len(error.requirements))
                self.launch_control.set_failed(status, tr("artifact.manual.launch_blocked_detail", provider="CurseForge"))
                self.home_page.set_status(status)
                self.right_panel.set_status(status)
                self.curseforge_manual_dialog.show()
                self.curseforge_manual_dialog.raise_()
                self.curseforge_manual_dialog.activateWindow()
                self.instance_controller.refresh_running(force=True)
                return
            if isinstance(error, ModrinthManagedFilesRequired):
                self._modrinth_pending_modpack_install = None
                self._modrinth_manual_instance_name = error.instance_name
                self.modrinth_manual_dialog.set_instance_context(error.instance_name, error.instance_dir)
                self.modrinth_manual_dialog.set_requirements(error.requirements)
                status = tr("artifact.manual.launch_blocked", provider="Modrinth", count=len(error.requirements))
                self.launch_control.set_failed(status, tr("artifact.manual.launch_blocked_detail", provider="Modrinth"))
                self.home_page.set_status(status)
                self.right_panel.set_status(status)
                self.modrinth_manual_dialog.show()
                self.modrinth_manual_dialog.raise_()
                self.modrinth_manual_dialog.activateWindow()
                self.instance_controller.refresh_running(force=True)
                return
            view = LaunchErrorPresenter.present(error)
            self.launch_control.set_failed(view.status, view.progress_detail)
            self.home_page.set_status(view.status)
            self.right_panel.set_status(view.status)
            self.instance_controller.refresh_running(force=True)
            return
        if task_id in {
            self.instance_controller.CREATE_TASK_ID,
            self.instance_controller.REPAIR_TASK_ID,
            self.instance_controller.LOADER_CHANGE_TASK_ID,
            self.instance_controller.LOADER_REPAIR_TASK_ID,
            self.instance_controller.FORGE_RESTORE_TASK_ID,
        }:
            if task_id != self.instance_controller.REPAIR_TASK_ID:
                self._suppress_loader_progress = True
            status = tr("loader.progress.failed" if task_id != self.instance_controller.REPAIR_TASK_ID else "Repair failed")
            self.launch_control.set_failed(status, tr("launch.error.logs_hint"))
            self.home_page.set_status(status)
            self.right_panel.set_status(status)
            return

        profile = task_progress_profile(task_id)
        if profile is None:
            return
        self._on_progress(ProgressEvent(stage=profile.stage, message=profile.failure_message, state=ProgressState.FAILED, detail=str(error)))

    def _on_launch_paused(self) -> None:
        self.launch_control.set_paused()
        message = tr("launch.paused")
        self.home_page.set_status(message)
        self.right_panel.set_status(message)

    def _on_launch_resumed(self) -> None:
        self.launch_control.set_resumed()
        message = tr("launch.resumed")
        self.home_page.set_status(message)
        self.right_panel.set_status(message)

    def _on_launch_cancel_requested(self) -> None:
        self.launch_control.set_cancel_pending()
        message = tr("launch.cancel_requested")
        self.home_page.set_status(message)
        self.right_panel.set_status(message)

    def _on_launch_cancelled(self) -> None:
        self.launch_control.set_cancelled("launch.cancelled", "launch.cancelled_detail")
        message = tr("launch.cancelled")
        self.home_page.set_status(message)
        self.right_panel.set_status(message)

    def _set_launch_active(self, active: bool) -> None:
        self.launch_control.set_launch_active(active)
        self.theme_runtime.reapply_assets(self.launch_control)

    def _on_progress(self, event: object) -> None:
        stage = getattr(event, "stage", None)
        stage_value = str(getattr(stage, "value", stage or ""))
        if self._suppress_loader_progress and stage_value in {"downloading_mod_loader", "installing_mod_loader"}:
            return

        self.launch_control.set_progress_event(event)

        message = tr(str(getattr(event, "message", "Working...")))
        self.home_page.set_status(message)
        self.right_panel.set_status(message)

    def _set_status(self, message: str) -> None:
        self.home_page.set_status(message)
        self.right_panel.set_status(message)
        self.launch_control.set_status(message)

    def _set_busy(self, busy: bool) -> None:
        self.account_page.set_busy(busy)
        self.instances_page.set_busy(busy)
        self.mods_page.set_busy(bool(busy) or bool(self._mod_catalog_tasks) or bool(self._curseforge_catalog_tasks))
        self.instance_settings_page.set_busy(busy)
        self.launcher_settings_page.set_busy(busy)
        self.launch_control.set_busy(busy)
        self.right_panel.set_busy(busy)
        if not self._content_tasks:
            self.content_pack_manager_dialog.set_busy(busy)
            self.content_library_dialog.set_busy(busy)

    def _export_diagnostics(self) -> None:
        suggested = Paths.diagnostics_default_path()
        selected, _ = QFileDialog.getSaveFileName(self, tr("diagnostics.export.title"), str(suggested), tr("diagnostics.file_filter"))
        if not selected:
            return
        try:
            path = DiagnosticsManager.write_bundle(Path(selected), launcher_version=VERSION_ID, settings=self.gui_settings_controller.raw_settings(), activity_log=self.logs_page.activity_text())
        except Exception as error:
            self._show_error(tr("diagnostics.export.title"), str(error))
            return
        self.logs_page.append(tr("diagnostics.export.success", path=path))
        QMessageBox.information(self, tr("diagnostics.export.title"), tr("diagnostics.export.success", path=path))

    def _open_forge_logs(self, name: str) -> None:
        try:
            instance = InstanceManager.load(name)
        except Exception as error:
            self._show_error(tr("forge.logs.title"), str(error))
            return
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        instance_logs = Paths.forge_instance_root(instance) / "logs"
        global_logs = (Paths.neoforge_root() if loader_name == ModLoaderManager.NEOFORGE else Paths.forge_root()) / "logs"
        target = instance_logs if instance_logs.exists() and any(instance_logs.iterdir()) else global_logs
        target.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target.resolve())))

    def _export_forge_diagnostics(self, name: str) -> None:
        try:
            instance = InstanceManager.load(name)
        except Exception as error:
            self._show_error(tr("forge.diagnostics.title"), str(error))
            return
        suggested = Paths.forge_diagnostics_default_path(instance)
        selected, _ = QFileDialog.getSaveFileName(
            self,
            tr("forge.export_diagnostics"),
            str(suggested),
            tr("forge.diagnostics.filter"),
        )
        if selected:
            self.instance_controller.export_forge_diagnostics(name, Path(selected))

    def _forge_diagnostics_finished(self, path: object) -> None:
        self.logs_page.append(tr("forge.diagnostics.success", path=path))
        QMessageBox.information(
            self,
            tr("forge.diagnostics.title"),
            tr("forge.diagnostics.success", path=path),
        )

    def _open_logs_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Paths.logs_root().resolve())))


    def _open_latest_game_log(self) -> None:
        instance = self._selected_instance
        if instance is None:
            QMessageBox.information(self, tr("Game log"), tr("Select an instance first."))
            return
        path = GameRuntimeManager.latest_game_log(instance)
        if path is None:
            QMessageBox.information(self, tr("Game log"), tr("No Minecraft log was found for this instance."))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def _open_latest_crash_report(self) -> None:
        instance = self._selected_instance
        if instance is None:
            QMessageBox.information(self, tr("Crash report"), tr("Select an instance first."))
            return
        path = GameRuntimeManager.latest_crash_report(instance)
        if path is None:
            QMessageBox.information(self, tr("Crash report"), tr("No crash report was found for this instance."))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _show_network_retry(self, controller: object, task_id: str, title: str, message: str) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(title or tr("network.retry.manual.title"))
        box.setText(tr("network.retry.manual.message", attempts=3))
        box.setInformativeText(message)
        box.setStandardButtons(QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(QMessageBox.StandardButton.Retry)
        box.setEscapeButton(QMessageBox.StandardButton.Cancel)

        retry_button = box.button(QMessageBox.StandardButton.Retry)
        cancel_button = box.button(QMessageBox.StandardButton.Cancel)
        if retry_button is not None:
            retry_button.setText(tr("network.retry.manual.button"))
        if cancel_button is not None:
            cancel_button.setText(tr("common.cancel"))

        result = box.exec()
        retry_value = int(QMessageBox.StandardButton.Retry.value)
        if result != retry_value:
            self._set_status(tr("network.retry.manual.cancelled"))
            return

        retry = getattr(controller, "retry_network_task", None)
        if not callable(retry) or not retry(task_id):
            self._show_error(tr("network.retry.manual.title"), tr("network.retry.manual.could_not_start"))

    def _show_export_finished(self, path: Path) -> None:
        self.toast_manager.show(tr("Saved to:\n{path}", path=path), "success", tr("Export complete"))

    def _show_instance_import_settings(self, preview: object) -> None:
        launcher_defaults = self.gui_settings_controller.current.get("instance_defaults", {})
        dialog = InstanceImportSettingsDialog(preview, launcher_defaults, self)
        if not dialog.exec():
            self._set_status(tr("instance_import.settings.cancelled"))
            return
        self.instance_controller.import_package(
            preview.package_path,
            dialog.selected_settings_override,
        )

    def _show_modpack_import_settings(self, preview: object) -> None:
        launcher_defaults = self.gui_settings_controller.current.get("instance_defaults", {})
        dialog = ModpackImportSettingsDialog(preview, launcher_defaults, self)
        if not dialog.exec():
            self._set_status(tr("modpack_package.import.cancelled"))
            return
        self.instance_controller.import_modpack_package(
            preview.package_path,
            dialog.selected_settings_override,
            dialog.install_optional_files,
            dialog.instance_name,
        )

    def _open_modpack_export(self, instance_name: str) -> None:
        name = str(instance_name or "").strip()
        if not name:
            return
        dialog = ModpackExportDialog(name, self)
        if not dialog.exec() or dialog.output_path is None:
            return
        options = dialog.options
        self.instance_controller.export_modpack(
            name,
            dialog.output_path,
            options.mode,
            options.portable_mode,
            options.include_saves,
        )

    def _show_modpack_export_finished(self, result: object) -> None:
        path = Path(getattr(result, "output_path", ""))
        referenced = int(getattr(result, "referenced_files", 0) or 0)
        embedded = int(getattr(result, "embedded_files", 0) or 0)
        manual = int(getattr(result, "manual_files", 0) or 0)
        native = bool(getattr(result, "native_package_included", False))
        if native:
            detail = tr("modpack_package.export.result.provider")
        else:
            detail = tr(
                "modpack_package.export.result.portable",
                referenced=referenced,
                embedded=embedded,
                manual=manual,
            )
        self.toast_manager.show(
            tr("modpack_package.export.result.saved", path=path, detail=detail),
            "success",
            tr("modpack_package.export.result.title"),
        )

    def _confirm_compatibility_launch(self, request: CompatibilityConfirmationRequired) -> None:
        issues = tuple(getattr(request, "issues", ()) or ())
        details = "\n".join(f"• {getattr(issue, 'message', issue)}" for issue in issues[:8])
        if len(issues) > 8:
            details += tr("compatibility.confirmation.more", count=len(issues) - 8)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("compatibility.confirmation.title"))
        box.setText(tr("compatibility.confirmation.message", count=len(issues)))
        box.setInformativeText(tr("compatibility.confirmation.detail", issues=details))
        launch_once = box.addButton(tr("compatibility.confirmation.launch_once"), QMessageBox.ButtonRole.AcceptRole)
        always_allow = box.addButton(tr("compatibility.confirmation.always_allow"), QMessageBox.ButtonRole.ActionRole)
        cancel = box.addButton(tr("common.cancel"), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(cancel)
        box.setEscapeButton(cancel)
        box.exec()
        clicked = box.clickedButton()
        if clicked is cancel or clicked is None:
            self.launch_control.set_failed(tr("compatibility.confirmation.cancelled"), tr("compatibility.confirmation.settings_hint"))
            return
        instance = self._selected_instance
        if clicked is always_allow and instance is not None:
            settings = SettingsManager.load(instance)
            settings.forge_preflight_failure_policy = ManagedContentPolicy.ALLOW
            SettingsManager.save(instance, settings)
            self.instance_settings_page.set_settings(instance.name, settings)
        if clicked in {launch_once, always_allow}:
            QTimer.singleShot(0, lambda: self.launch_controller.launch(True))

    def _portable_manual_download_required(self, request: object) -> None:
        requirements = tuple(getattr(request, "requirements", ()) or ())
        instance = getattr(request, "instance", None)
        if not requirements or instance is None:
            self._show_error(tr("portable.manual.title"), tr("portable.manual.invalid"))
            return
        self._portable_manual_request = request
        self.portable_manual_dialog.set_instance_context(str(getattr(instance, "name", "")), getattr(instance, "instance_dir", None))
        self.portable_manual_dialog.set_requirements(requirements)
        self.portable_manual_dialog.show()
        self.portable_manual_dialog.raise_()
        self.portable_manual_dialog.activateWindow()

    def _install_portable_manual_files(self, sources: object) -> None:
        request = self._portable_manual_request
        paths = tuple(Path(source) for source in (sources or ())) if isinstance(sources, (list, tuple)) else ()
        requirements = tuple(getattr(request, "requirements", ()) or ()) if request is not None else ()
        instance = getattr(request, "instance", None) if request is not None else None
        if instance is None or not requirements or not paths:
            return
        self.instance_controller.install_portable_manual_files(str(getattr(instance, "name", "")), requirements, paths)

    def _portable_manual_files_installed(self, result: object) -> None:
        count = len(result.get("installed", ())) if isinstance(result, dict) else 0
        instance_name = str(result.get("instanceName", "")) if isinstance(result, dict) else ""
        self.portable_manual_dialog.close()
        self._portable_manual_request = None
        self.instance_controller.refresh(selected_name=instance_name)
        QMessageBox.information(
            self,
            tr("portable.manual.title"),
            tr("portable.manual.installed", count=count),
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.task_runner.has_active_tasks:
            QMessageBox.information(
                self,
                tr("MCW Launcher"),
                tr("A launcher task is still running.\nClose the window after it finishes."),
            )
            event.ignore()
            return

        if not self._confirm_all_unsaved_settings():
            event.ignore()
            return

        if self.gui_settings_controller.current.get("remember_window_size", True):
            self.gui_settings_controller.save_geometry(self.saveGeometry())

        self.task_runner.close()
        super().closeEvent(event)


def run() -> None:
    app = create_application(sys.argv)
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    run()
