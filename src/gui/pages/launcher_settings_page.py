from __future__ import annotations

import copy
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QSizePolicy

from mcw_core.api.hardware.gpu_preference_manager import GraphicsDetectionResult
from mcw_core.api.instance.settings_manager import SettingsManager, default_instance_settings
from mcw_core.api.java.java_major_policy import JavaMajorPolicy
from mcw_core.api.language.language_manager import language_manager, tr
from mcw_core.api.theme.theme_authoring import ThemeAuthoringError, ThemeAuthoringService
from mcw_core.api.theme.theme_manager import theme_manager
from mcw_core.api.theme.theme_palette import normalize_hex_color
from src.gui.config import NAVIGATION_ITEMS, VERSION
from src.gui.dialogs.instance_settings_editor_dialog import InstanceSettingsEditorDialog
from src.gui.dialogs.protected_value_reveal_dialog import confirm_reveal_protected_values
from src.gui.dialogs.theme_issues_dialog import ThemeIssuesDialog
from src.gui.pages.base_page import BasePage
from src.gui.theme.live_reload import ThemeLiveReload
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget
from src.gui.widget.settings_section import SettingsSection
from src.gui.widget.themed_animated_label import ThemedAnimatedLabel
from src.gui.widget.themed_progress_bar import ThemedProgressBar


class LauncherSettingsPage(BasePage):
    save_requested = Signal(dict)
    reset_requested = Signal()
    language_changed = Signal(str)
    check_updates_requested = Signal()
    reload_theme_requested = Signal(str)
    live_theme_reload_requested = Signal(str)
    motion_mode_changed = Signal(str)
    accent_changed = Signal(str, str)
    preview_toast_requested = Signal()
    scan_java_requested = Signal()
    install_java_requested = Signal(int)
    open_java_requested = Signal(object)
    dirty_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__("Launcher Settings", "Preferences here belong to the GUI, not to an individual Minecraft instance.", "launcher_settings")
        self._java_installations: list[object] = []
        self._latest_java_major: int | None = None
        self._latest_java_lookup_error = ""
        self._gpu_detection = GraphicsDetectionResult(supported=False)
        self._theme_authoring = ThemeAuthoringService(theme_manager)
        self._theme_live_reload = ThemeLiveReload(self)
        self._theme_live_reload.reload_requested.connect(self._handle_live_theme_reload)
        self._instance_defaults = default_instance_settings()
        self._accent_color = "#8ed35b"
        self._tracking_suspended = True
        self._dirty = False
        self._saved_data: dict = {}
        self._force_replace_on_next_settings = True
        self._theme_preview_timer = QTimer(self)
        self._theme_preview_timer.setSingleShot(True)
        self._theme_preview_timer.setInterval(25)
        self._theme_preview_timer.timeout.connect(self._emit_theme_preview)
        self._build_ui()
        self._connect_dirty_tracking()
        self._tracking_suspended = False
        self._set_dirty(False)

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def _build_ui(self) -> None:
        self.unsaved_label = QLabel()
        self.unsaved_label.setObjectName("UnsavedChangesBanner")
        self.unsaved_label.setWordWrap(True)
        self.unsaved_label.setVisible(False)
        self.root_layout.addWidget(self.unsaved_label)

        general_section = SettingsSection("settings.section.general", "settings.section.general_detail")
        downloads_section = SettingsSection("settings.section.downloads", "settings.section.downloads_detail")
        runtime_section = SettingsSection("settings.section.runtime", "settings.section.runtime_detail")
        appearance_section = SettingsSection("settings.section.appearance", "settings.section.appearance_detail")
        for section in (general_section, downloads_section, runtime_section, appearance_section):
            self.root_layout.addWidget(section)

        behavior_card = CardWidget("Startup and behavior")
        self.start_page_combo = QComboBox()
        for page_id, label in NAVIGATION_ITEMS:
            self.start_page_combo.addItem(label, page_id)
        self.show_snapshots = QCheckBox("Show non-release versions by default")
        self.remember_window_size = QCheckBox("Remember window size and position")
        self.debug_mode = QCheckBox("Enable debug launch information")
        behavior_card.layout.addWidget(QLabel("Startup page"))
        behavior_card.layout.addWidget(self.start_page_combo)
        behavior_card.layout.addWidget(self.show_snapshots)
        behavior_card.layout.addWidget(self.remember_window_size)
        behavior_card.layout.addWidget(self.debug_mode)
        general_section.add_card(behavior_card)

        bandwidth_card = CardWidget("Download bandwidth", "The limit is shared by all simultaneous downloads. Leave it disabled for unlimited speed.")
        self.limit_download_speed = QCheckBox("Limit download speed")
        self.download_limit_mbps = QDoubleSpinBox()
        self.download_limit_mbps.setRange(0.1, 1024.0)
        self.download_limit_mbps.setDecimals(1)
        self.download_limit_mbps.setSingleStep(1.0)
        self.download_limit_mbps.setSuffix(" MB/s")
        self.download_limit_mbps.setValue(10.0)
        self.download_limit_mbps.setEnabled(False)
        self.limit_download_speed.toggled.connect(self.download_limit_mbps.setEnabled)
        self.download_concurrency = QComboBox()
        self.download_concurrency.addItem(tr("network.concurrency.auto"), 0)
        for value in (2, 4, 6, 8, 12, 16):
            self.download_concurrency.addItem(tr("network.concurrency.value", count=value), value)
        bandwidth_card.layout.addWidget(self.limit_download_speed)
        bandwidth_card.layout.addWidget(self.download_limit_mbps)
        bandwidth_card.layout.addWidget(QLabel(tr("network.concurrency.label")))
        bandwidth_card.layout.addWidget(self.download_concurrency)
        downloads_section.add_card(bandwidth_card)

        language_card = CardWidget("Language", "Add another language by placing a compatible JSON file in the lang folder.")
        self.language_combo = QComboBox()
        self.reload_languages()
        self.language_combo.currentIndexChanged.connect(self._emit_language_changed)
        reload_languages_button = set_theme_icon(QPushButton("Reload language packs"), "icon.action.language")
        reload_languages_button.clicked.connect(self.reload_languages)
        language_card.layout.addWidget(QLabel("Launcher language"))
        language_card.layout.addWidget(self.language_combo)
        language_card.layout.addWidget(reload_languages_button)
        general_section.add_card(language_card)

        self.content_browser_card = CardWidget(tr("content.settings.title"), tr("content.settings.detail"))
        self.show_content_descriptions = QCheckBox(tr("content.settings.show_descriptions"))
        self.modrinth_include_beta = QCheckBox("Include Beta mod and modpack versions")
        self.modrinth_include_alpha = QCheckBox("Include Alpha mod and modpack versions")
        self.content_browser_card.layout.addWidget(self.show_content_descriptions)
        self.content_browser_card.layout.addWidget(self.modrinth_include_beta)
        self.content_browser_card.layout.addWidget(self.modrinth_include_alpha)
        downloads_section.add_card(self.content_browser_card)

        managed_checks_card = CardWidget(
            tr("managed_content.launcher.title"),
            tr("managed_content.launcher.detail"),
        )
        self.block_modrinth_failure = QCheckBox(tr("managed_content.modrinth.block"))
        self.block_curseforge_failure = QCheckBox(tr("managed_content.curseforge.block"))
        self.block_modrinth_failure.setChecked(True)
        self.block_curseforge_failure.setChecked(True)
        managed_checks_card.layout.addWidget(self.block_modrinth_failure)
        managed_checks_card.layout.addWidget(self.block_curseforge_failure)
        downloads_section.add_card(managed_checks_card, span=2)

        curseforge_card = CardWidget(
            "Private CurseForge gateways",
            "Configure up to five private HTTPS gateway links. They are stored outside the launcher settings file and protected with Windows DPAPI. Requests try each link in order when an earlier gateway is unavailable.",
        )
        self.curseforge_gateway_labels: list[QLabel] = []
        self.curseforge_gateway_inputs: list[QLineEdit] = []
        for index in range(1, 6):
            label = QLabel(tr("curseforge.gateway.slot", index=index))
            field = QLineEdit()
            field.setPlaceholderText("Paste private HTTPS gateway link")
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setClearButtonEnabled(True)
            self.curseforge_gateway_labels.append(label)
            self.curseforge_gateway_inputs.append(field)
            curseforge_card.layout.addWidget(label)
            curseforge_card.layout.addWidget(field)
        self.reveal_curseforge_gateways = QCheckBox("Reveal protected gateway links")
        self.reveal_curseforge_gateways.toggled.connect(self._set_gateway_links_revealed)
        self.curseforge_gateway_security = QLabel("Gateway links are masked in the interface and encrypted for the current Windows account.")
        self.curseforge_gateway_security.setObjectName("MutedLabel")
        self.curseforge_gateway_security.setWordWrap(True)
        curseforge_card.layout.addWidget(self.reveal_curseforge_gateways)
        curseforge_card.layout.addWidget(self.curseforge_gateway_security)
        downloads_section.add_card(curseforge_card, span=2)

        self.java_card = CardWidget(tr("launcher_settings.java.title"), tr("launcher_settings.java.description"))
        self.java_card.setProperty("themeRole", "java")
        self.java_combo = QComboBox()
        self.java_combo.currentIndexChanged.connect(self._update_java_details)
        self.java_details = QLabel("Java scan has not run yet.")
        self.java_details.setObjectName("MutedLabel")
        self.java_details.setWordWrap(True)
        self.scan_java_button = set_theme_icon(QPushButton("Scan Java installations"), "icon.action.java")
        self.scan_java_button.clicked.connect(self.scan_java_requested.emit)
        self.open_java_button = set_theme_icon(QPushButton("Open selected Java folder"), "icon.action.folder")
        self.open_java_button.setEnabled(False)
        self.open_java_button.clicked.connect(lambda: self.open_java_requested.emit(self.current_java_installation()))

        self.java_install_label = QLabel(tr("launcher_settings.java.install_label"))
        self.java_install_combo = QComboBox()
        self._populate_java_install_combo(17)
        default_index = self.java_install_combo.findData(17)
        self.java_install_combo.setCurrentIndex(max(0, default_index))
        self.java_install_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.java_install_button.clicked.connect(self._request_java_install)
        self.java_install_combo.currentIndexChanged.connect(self._update_java_install_action)
        self.java_install_status = QLabel(tr("launcher_settings.java.install_hint"))
        self.java_install_status.setObjectName("MutedLabel")
        self.java_install_status.setWordWrap(True)

        self.java_card.layout.addWidget(self.java_combo)
        self.java_card.layout.addWidget(self.java_details)
        self.java_card.layout.addWidget(self.scan_java_button)
        self.java_card.layout.addWidget(self.open_java_button)
        self.java_card.layout.addWidget(self.java_install_label)
        self.java_card.layout.addWidget(self.java_install_combo)
        self.java_card.layout.addWidget(self.java_install_button)
        self.java_card.layout.addWidget(self.java_install_status)
        runtime_section.add_card(self.java_card)
        self._update_java_install_action()

        self.gpu_card = CardWidget(tr("gpu.preference.title"), tr("gpu.preference.detail"))
        self.prefer_dedicated_gpu = QCheckBox(tr("gpu.preference.toggle"))
        self.prefer_dedicated_gpu.setChecked(False)
        self.prefer_dedicated_gpu.setEnabled(False)
        self.gpu_status_label = QLabel(tr("gpu.preference.detecting"))
        self.gpu_status_label.setObjectName("MutedLabel")
        self.gpu_status_label.setWordWrap(True)
        self.gpu_card.layout.addWidget(self.prefer_dedicated_gpu)
        self.gpu_card.layout.addWidget(self.gpu_status_label)
        runtime_section.add_card(self.gpu_card)

        self.instance_defaults_card = CardWidget(
            tr("instance_defaults.launcher.title"),
            tr("instance_defaults.launcher.description"),
        )
        self.instance_defaults_summary = QLabel()
        self.instance_defaults_summary.setObjectName("MutedLabel")
        self.instance_defaults_summary.setWordWrap(True)
        self.instance_defaults_summary.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.edit_instance_defaults_button = set_theme_icon(
            QPushButton(tr("instance_defaults.launcher.edit")),
            "icon.action.settings",
        )
        self.edit_instance_defaults_button.clicked.connect(self._edit_instance_defaults)
        self.instance_defaults_card.layout.addWidget(self.instance_defaults_summary)
        self.instance_defaults_card.layout.addStretch(1)
        self.instance_defaults_card.layout.addWidget(self.edit_instance_defaults_button)
        runtime_section.add_card(self.instance_defaults_card)
        self._update_instance_defaults_summary()

        forge_preflight_card = CardWidget(
            tr("forge_preflight.launcher.title"),
            tr("forge_preflight.launcher.detail"),
        )
        self.allow_forge_preflight_failure = QCheckBox(tr("forge_preflight.launcher.allow"))
        self.allow_forge_preflight_failure.setChecked(False)
        self.forge_preflight_warning_label = QLabel(tr("forge_preflight.warning"))
        self.forge_preflight_warning_label.setObjectName("MutedLabel")
        self.forge_preflight_warning_label.setWordWrap(True)
        forge_preflight_card.layout.addWidget(self.allow_forge_preflight_failure)
        forge_preflight_card.layout.addWidget(self.forge_preflight_warning_label)
        runtime_section.add_card(forge_preflight_card)

        update_card = CardWidget("Launcher updates", "Stable updates are used by default. Join the tester program only when you want to receive experimental builds.")
        current_version_label = QLabel(f"Current version: {VERSION}")
        current_version_label.setObjectName("ValueLabel")
        self.auto_check_updates = QCheckBox("Automatically check for updates when the launcher starts")
        self.join_tester_program = QCheckBox("Join tester program and receive experimental updates")
        self.tester_warning_label = QLabel("Experimental updates may contain unfinished features, bugs, crashes, or compatibility issues. Back up important instances and worlds before joining.")
        self.tester_warning_label.setObjectName("WarningLabel")
        self.tester_warning_label.setWordWrap(True)
        self.tester_warning_label.setVisible(False)
        self.join_tester_program.toggled.connect(self.tester_warning_label.setVisible)
        self.update_status_label = QLabel("Update status: Not checked")
        self.update_status_label.setObjectName("ValueLabel")
        self.update_status_label.setWordWrap(True)
        self.check_updates_button = set_theme_icon(QPushButton("Check for updates"), "icon.action.update")
        self.check_updates_button.clicked.connect(self.check_updates_requested.emit)
        update_card.layout.addWidget(current_version_label)
        update_card.layout.addWidget(self.auto_check_updates)
        update_card.layout.addWidget(self.join_tester_program)
        update_card.layout.addWidget(self.tester_warning_label)
        update_card.layout.addWidget(self.update_status_label)
        update_card.layout.addWidget(self.check_updates_button)
        runtime_section.add_card(update_card)

        appearance_card = CardWidget("Appearance", "PNG theme files are optional. Missing or invalid files automatically fall back to the built-in CSS interface.")
        self.theme_combo = QComboBox()
        self.reload_themes()
        self.motion_mode_combo = QComboBox()
        self._reload_motion_modes()
        self.motion_mode_combo.currentIndexChanged.connect(self._emit_motion_mode_changed)
        self.show_static_text = QCheckBox("Show static text over themed controls")
        self.show_static_text.setToolTip("Disabled by default. Enable this only when you want launcher text drawn over themed PNG controls.")
        self.reload_theme_button = set_theme_icon(QPushButton(tr("theme.authoring.reload")), "icon.action.theme")
        self.reload_theme_button.clicked.connect(self._emit_theme_preview)
        self.show_static_text.toggled.connect(self._queue_theme_preview)
        self.live_theme_reload = QCheckBox(tr("theme.authoring.live_reload"))
        self.live_theme_reload.setToolTip(tr("theme.authoring.live_reload.detail"))
        self.live_theme_reload.toggled.connect(self._set_live_theme_reload)
        self.theme_status_label = QLabel()
        self.theme_status_label.setObjectName("MutedLabel")
        self.theme_status_label.setWordWrap(True)
        self.theme_details_button = set_theme_icon(QPushButton(tr("theme.authoring.details")), "icon.action.settings")
        self.theme_open_button = set_theme_icon(QPushButton(tr("theme.authoring.open_folder")), "icon.action.folder")
        self.theme_duplicate_button = set_theme_icon(QPushButton(tr("theme.authoring.duplicate")), "icon.action.clone")
        self.theme_import_button = set_theme_icon(QPushButton(tr("theme.authoring.import")), "icon.action.import")
        self.theme_export_button = set_theme_icon(QPushButton(tr("theme.authoring.export")), "icon.action.export")
        self.theme_details_button.clicked.connect(self._show_theme_details)
        self.theme_open_button.clicked.connect(self._open_theme_folder)
        self.theme_duplicate_button.clicked.connect(self._duplicate_theme)
        self.theme_import_button.clicked.connect(self._import_theme)
        self.theme_export_button.clicked.connect(self._export_theme)
        authoring_row = QHBoxLayout()
        authoring_row.setContentsMargins(0, 0, 0, 0)
        authoring_row.addWidget(self.theme_details_button)
        authoring_row.addWidget(self.theme_open_button)
        authoring_row.addWidget(self.theme_duplicate_button)
        package_row = QHBoxLayout()
        package_row.setContentsMargins(0, 0, 0, 0)
        package_row.addWidget(self.theme_import_button)
        package_row.addWidget(self.theme_export_button)
        package_row.addStretch()
        appearance_card.layout.addWidget(QLabel("Launcher theme"))
        appearance_card.layout.addWidget(self.theme_combo)
        appearance_card.layout.addWidget(self.theme_status_label)
        appearance_card.layout.addLayout(authoring_row)
        appearance_card.layout.addLayout(package_row)
        self.accent_mode_label = QLabel(tr("appearance.accent.mode.label"))
        self.accent_mode_combo = QComboBox()
        self._reload_accent_modes()
        self.accent_mode_combo.currentIndexChanged.connect(self._accent_mode_changed)
        self.accent_color_button = QPushButton()
        self.accent_color_button.setMinimumHeight(36)
        self.accent_color_button.clicked.connect(self._choose_accent_color)
        self.accent_reset_button = QPushButton(tr("appearance.accent.reset"))
        self.accent_reset_button.clicked.connect(self._reset_accent)
        accent_row = QHBoxLayout()
        accent_row.setContentsMargins(0, 0, 0, 0)
        accent_row.addWidget(self.accent_color_button, 1)
        accent_row.addWidget(self.accent_reset_button)
        self.accent_detail_label = QLabel()
        self.accent_detail_label.setObjectName("MutedLabel")
        self.accent_detail_label.setWordWrap(True)
        appearance_card.layout.addWidget(self.accent_mode_label)
        appearance_card.layout.addWidget(self.accent_mode_combo)
        appearance_card.layout.addLayout(accent_row)
        appearance_card.layout.addWidget(self.accent_detail_label)
        self._update_accent_controls()
        self.motion_mode_label = QLabel(tr("motion.mode.label"))
        self.motion_mode_detail = QLabel(tr("motion.mode.detail"))
        self.motion_mode_detail.setObjectName("MutedLabel")
        self.motion_mode_detail.setWordWrap(True)
        appearance_card.layout.addWidget(self.motion_mode_label)
        appearance_card.layout.addWidget(self.motion_mode_combo)
        appearance_card.layout.addWidget(self.motion_mode_detail)
        appearance_card.layout.addWidget(self.show_static_text)
        appearance_card.layout.addWidget(self.live_theme_reload)
        appearance_card.layout.addWidget(self.reload_theme_button)
        appearance_section.add_card(appearance_card, span=2)

        self.motion_preview_card = CardWidget(
            tr("motion.preview.title"),
            tr("motion.preview.description"),
        )
        state_row = QHBoxLayout()
        state_row.setContentsMargins(0, 0, 0, 0)
        state_row.setSpacing(12)
        self.preview_success_icon = ThemedAnimatedLabel("state.success", "icon.state.success", 28, 28)
        self.preview_warning_icon = ThemedAnimatedLabel("state.warning", "icon.state.warning", 28, 28)
        self.preview_error_icon = ThemedAnimatedLabel("state.error", "icon.state.error", 28, 28)
        self.preview_success_label = QLabel(tr("motion.preview.success"))
        self.preview_warning_label = QLabel(tr("motion.preview.warning"))
        self.preview_error_label = QLabel(tr("motion.preview.error"))
        state_row.addWidget(self.preview_success_icon)
        state_row.addWidget(self.preview_success_label)
        state_row.addWidget(self.preview_warning_icon)
        state_row.addWidget(self.preview_warning_label)
        state_row.addWidget(self.preview_error_icon)
        state_row.addWidget(self.preview_error_label)
        state_row.addStretch()
        self.preview_determinate = ThemedProgressBar()
        self.preview_determinate.setRange(0, 100)
        self.preview_determinate.setValue(64)
        self.preview_determinate.setFormat(tr("motion.preview.progress", value=64))
        self.preview_indeterminate = ThemedProgressBar()
        self.preview_indeterminate.setRange(0, 0)
        self.preview_indeterminate.setFormat(tr("motion.preview.indeterminate"))
        self.preview_font_label = QLabel(tr("theme.authoring.preview.font_sample"))
        self.preview_font_label.setObjectName("ValueLabel")
        self.preview_font_label.setWordWrap(True)
        preview_button_row = QHBoxLayout()
        preview_button_row.setContentsMargins(0, 0, 0, 0)
        self.preview_default_button = QPushButton(tr("theme.authoring.preview.default_button"))
        self.preview_primary_button = QPushButton(tr("theme.authoring.preview.primary_button"))
        self.preview_primary_button.setObjectName("PrimaryButton")
        self.preview_disabled_button = QPushButton(tr("theme.authoring.preview.disabled_button"))
        self.preview_disabled_button.setEnabled(False)
        self.preview_dialog_button = QPushButton(tr("theme.authoring.preview.dialog_button"))
        self.preview_dialog_button.clicked.connect(self._show_preview_dialog)
        preview_button_row.addWidget(self.preview_default_button)
        preview_button_row.addWidget(self.preview_primary_button)
        preview_button_row.addWidget(self.preview_disabled_button)
        preview_button_row.addWidget(self.preview_dialog_button)
        self.preview_toast_button = set_theme_icon(
            QPushButton(tr("motion.preview.toast_button")),
            "icon.state.success",
        )
        self.preview_toast_button.clicked.connect(self.preview_toast_requested.emit)
        self.preview_default_button.clicked.connect(self.preview_toast_requested.emit)
        self.preview_primary_button.clicked.connect(self.preview_toast_requested.emit)
        self.motion_preview_card.layout.addWidget(self.preview_font_label)
        self.motion_preview_card.layout.addLayout(preview_button_row)
        self.motion_preview_card.layout.addLayout(state_row)
        self.motion_preview_card.layout.addWidget(self.preview_determinate)
        self.motion_preview_card.layout.addWidget(self.preview_indeterminate)
        self.motion_preview_card.layout.addWidget(self.preview_toast_button)
        appearance_section.add_card(self.motion_preview_card, span=2)

        self.save_button = set_theme_icon(QPushButton("Save launcher settings"), "icon.action.save")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.request_save)
        reset_button = set_theme_icon(QPushButton("Reset to defaults"), "icon.action.reset")
        reset_button.clicked.connect(self.request_reset)
        self.root_layout.addWidget(self.save_button)
        self.root_layout.addWidget(reset_button)
        self.root_layout.addStretch()

    def _connect_dirty_tracking(self) -> None:
        self.start_page_combo.currentIndexChanged.connect(self._refresh_dirty_state)
        self.show_snapshots.toggled.connect(self._refresh_dirty_state)
        self.remember_window_size.toggled.connect(self._refresh_dirty_state)
        self.debug_mode.toggled.connect(self._refresh_dirty_state)
        self.prefer_dedicated_gpu.toggled.connect(self._refresh_dirty_state)
        self.limit_download_speed.toggled.connect(self._refresh_dirty_state)
        self.download_limit_mbps.valueChanged.connect(self._refresh_dirty_state)
        self.download_concurrency.currentIndexChanged.connect(self._refresh_dirty_state)
        self.language_combo.currentIndexChanged.connect(self._refresh_dirty_state)
        self.show_content_descriptions.toggled.connect(self._refresh_dirty_state)
        self.modrinth_include_beta.toggled.connect(self._refresh_dirty_state)
        self.modrinth_include_alpha.toggled.connect(self._refresh_dirty_state)
        self.block_modrinth_failure.toggled.connect(self._refresh_dirty_state)
        self.block_curseforge_failure.toggled.connect(self._refresh_dirty_state)
        self.allow_forge_preflight_failure.toggled.connect(self._refresh_dirty_state)
        for field in self.curseforge_gateway_inputs:
            field.textChanged.connect(self._refresh_dirty_state)
        self.auto_check_updates.toggled.connect(self._refresh_dirty_state)
        self.join_tester_program.toggled.connect(self._refresh_dirty_state)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_selection_changed)
        self.theme_combo.currentIndexChanged.connect(self._refresh_dirty_state)
        self.motion_mode_combo.currentIndexChanged.connect(self._refresh_dirty_state)
        self.accent_mode_combo.currentIndexChanged.connect(self._refresh_dirty_state)
        self.show_static_text.toggled.connect(self._refresh_dirty_state)
        self.live_theme_reload.toggled.connect(self._refresh_dirty_state)

    def set_gpu_detection(self, detection: GraphicsDetectionResult) -> None:
        self._gpu_detection = detection
        available = bool(detection.supported and detection.has_dedicated_gpu)
        self.prefer_dedicated_gpu.setEnabled(available)
        if not available:
            with QSignalBlocker(self.prefer_dedicated_gpu):
                self.prefer_dedicated_gpu.setChecked(False)
        self._update_gpu_status()
        if not self._tracking_suspended:
            self._refresh_dirty_state()

    def _update_gpu_status(self) -> None:
        detection = self._gpu_detection
        if not detection.supported:
            self.gpu_status_label.setText(tr("gpu.preference.unsupported"))
            return
        if detection.error:
            self.gpu_status_label.setText(tr("gpu.preference.detect_failed", error=detection.error))
            return
        dedicated = detection.dedicated_adapters
        if dedicated:
            names = ", ".join(adapter.name for adapter in dedicated)
            self.gpu_status_label.setText(tr("gpu.preference.detected", adapters=names))
        else:
            self.gpu_status_label.setText(tr("gpu.preference.not_detected"))

    def set_java_installations(self, installations: list) -> None:
        self._java_installations = list(installations)
        self.java_combo.blockSignals(True)
        self.java_combo.clear()
        for item in self._java_installations:
            label = getattr(item, "display_name", None) or f"Java {getattr(item, 'major_version', '?')}"
            self.java_combo.addItem(str(label))
        self.java_combo.blockSignals(False)
        self._update_java_details()

    def current_java_installation(self) -> object | None:
        index = self.java_combo.currentIndex()
        if index < 0 or index >= len(self._java_installations):
            return None
        return self._java_installations[index]

    def _update_java_details(self, _index: int = -1) -> None:
        item = self.current_java_installation()
        if item is None:
            self.java_details.setText(tr("launcher_settings.java.none"))
            self.open_java_button.setEnabled(False)
            self._update_java_install_action()
            return
        source = getattr(getattr(item, "source", None), "value", "unknown")
        self.java_details.setText(tr("launcher_settings.java.details", major=getattr(item, "major_version", "?"), vendor=getattr(item, "vendor", "") or tr("common.unknown"), architecture=getattr(item, "architecture", "") or tr("common.unknown"), path=getattr(item, "executable", ""), source=source))
        self.open_java_button.setEnabled(True)
        self._update_java_install_action()

    def set_latest_java_release(self, major: int) -> None:
        try:
            latest_major = int(major)
        except (TypeError, ValueError):
            return
        if latest_major < 8:
            return
        current_major = self.java_install_combo.currentData() if hasattr(self, "java_install_combo") else 17
        self._latest_java_major = latest_major
        self._latest_java_lookup_error = ""
        self._populate_java_install_combo(int(current_major or 17))
        self._update_java_install_action()

    def set_latest_java_release_failed(self, error: str) -> None:
        self._latest_java_lookup_error = str(error or "")
        if self._latest_java_major is None and not self.java_install_status.text().endswith("..."):
            self.java_install_status.setText(tr("launcher_settings.java.latest_unavailable"))

    def _populate_java_install_combo(self, selected_major: int | None = None) -> None:
        current_major = int(selected_major or self.java_install_combo.currentData() or 17)
        with QSignalBlocker(self.java_install_combo):
            self.java_install_combo.clear()
            for major in JavaMajorPolicy.SUPPORTED_MAJORS:
                label_key = "launcher_settings.java.latest_version" if major == self._latest_java_major else "launcher_settings.java.version"
                self.java_install_combo.addItem(tr(label_key, major=major), major)
            if self._latest_java_major is not None and self._latest_java_major not in JavaMajorPolicy.SUPPORTED_MAJORS:
                self.java_install_combo.addItem(tr("launcher_settings.java.latest_version", major=self._latest_java_major), self._latest_java_major)
            index = self.java_install_combo.findData(current_major)
            if index < 0:
                index = self.java_install_combo.findData(self._latest_java_major) if self._latest_java_major is not None else self.java_install_combo.findData(17)
            self.java_install_combo.setCurrentIndex(max(0, index))

    def _request_java_install(self) -> None:
        major = int(self.java_install_combo.currentData() or 17)
        self.java_install_status.setText(tr("launcher_settings.java.install_starting", major=major))
        self.install_java_requested.emit(major)

    def _update_java_install_action(self, _index: int = -1) -> None:
        if not hasattr(self, "java_install_combo"):
            return
        major = int(self.java_install_combo.currentData() or 17)
        managed = any(
            int(getattr(item, "major_version", -1)) == major
            and str(getattr(getattr(item, "source", None), "value", "")) == "MINECRAFT_RUNTIME"
            for item in self._java_installations
        )
        is_latest = major == self._latest_java_major
        if is_latest:
            key = "launcher_settings.java.latest_reinstall" if managed else "launcher_settings.java.latest_install"
        else:
            key = "launcher_settings.java.reinstall" if managed else "launcher_settings.java.install"
        self.java_install_button.setText(tr(key, major=major))
        if managed:
            status_key = "launcher_settings.java.latest_managed_ready" if is_latest else "launcher_settings.java.managed_ready"
            self.java_install_status.setText(tr(status_key, major=major))
        elif not self.java_install_status.text() or "..." not in self.java_install_status.text():
            if is_latest:
                self.java_install_status.setText(tr("launcher_settings.java.latest_hint", major=major))
            elif self._latest_java_major is None and self._latest_java_lookup_error:
                self.java_install_status.setText(tr("launcher_settings.java.latest_unavailable"))
            else:
                self.java_install_status.setText(tr("launcher_settings.java.install_hint"))

    def set_java_installation_result(self, major: int, executable: object) -> None:
        self.java_install_status.setText(tr("launcher_settings.java.install_success", major=major, path=executable))

    def set_java_installation_cancelled(self, major: int) -> None:
        self.java_install_status.setText(tr("launcher_settings.java.install_cancelled", major=major))

    def set_java_installation_failed(self, major: int, error: str) -> None:
        self.java_install_status.setText(tr("launcher_settings.java.install_failed", major=major, error=error))

    def reload_languages(self) -> None:
        current_locale = self.language_combo.currentData() if hasattr(self, "language_combo") else None
        language_manager.reload()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        for language in language_manager.available_languages():
            self.language_combo.addItem(language.name, language.locale)
        locale = current_locale or language_manager.current_locale
        index = self.language_combo.findData(locale)
        self.language_combo.setCurrentIndex(max(0, index))
        self.language_combo.blockSignals(False)

    def reload_themes(self) -> None:
        current_theme = self.theme_combo.currentData() if hasattr(self, "theme_combo") else None
        themes = theme_manager.reload()
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        for theme in themes:
            label = f"{theme.name} — {theme.author}"
            if theme.issues:
                label += " " + tr("theme.authoring.combo.issues", count=len(theme.issues))
            self.theme_combo.addItem(label, theme.theme_id)
        selected = str(current_theme or theme_manager.current.theme_id or "mcw-default")
        index = self.theme_combo.findData(selected)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.theme_combo.blockSignals(False)
        self._update_theme_authoring_state()
        if hasattr(self, "_theme_live_reload"):
            self._watch_selected_theme()

    def _reload_motion_modes(self) -> None:
        current = self.motion_mode_combo.currentData() if hasattr(self, "motion_mode_combo") else "full"
        self.motion_mode_combo.blockSignals(True)
        self.motion_mode_combo.clear()
        self.motion_mode_combo.addItem(tr("motion.mode.full"), "full")
        self.motion_mode_combo.addItem(tr("motion.mode.reduced"), "reduced")
        self.motion_mode_combo.addItem(tr("motion.mode.off"), "off")
        index = self.motion_mode_combo.findData(current or "full")
        self.motion_mode_combo.setCurrentIndex(max(0, index))
        self.motion_mode_combo.blockSignals(False)

    def current_motion_mode(self) -> str:
        value = str(self.motion_mode_combo.currentData() or "full").strip().lower()
        return value if value in {"full", "reduced", "off"} else "full"

    def _reload_accent_modes(self) -> None:
        current = self.accent_mode_combo.currentData() if hasattr(self, "accent_mode_combo") else "theme"
        self.accent_mode_combo.blockSignals(True)
        self.accent_mode_combo.clear()
        self.accent_mode_combo.addItem(tr("appearance.accent.mode.theme"), "theme")
        self.accent_mode_combo.addItem(tr("appearance.accent.mode.custom"), "custom")
        index = self.accent_mode_combo.findData(current or "theme")
        self.accent_mode_combo.setCurrentIndex(max(0, index))
        self.accent_mode_combo.blockSignals(False)

    def current_accent_mode(self) -> str:
        value = str(self.accent_mode_combo.currentData() or "theme").strip().lower()
        return value if value in {"theme", "custom"} else "theme"

    def current_accent_color(self) -> str:
        try:
            return normalize_hex_color(self._accent_color)
        except ValueError:
            return "#8ed35b"

    def _theme_accent_color(self) -> str:
        theme = self._selected_theme()
        return theme.palette.primary if theme is not None else "#63984a"

    def _accent_mode_changed(self, _index: int) -> None:
        self._update_accent_controls()
        self.accent_changed.emit(self.current_accent_mode(), self.current_accent_color())

    def _choose_accent_color(self) -> None:
        selected = QColorDialog.getColor(QColor(self.current_accent_color()), self, tr("appearance.accent.choose"))
        if not selected.isValid():
            return
        self._accent_color = selected.name(QColor.NameFormat.HexRgb).lower()
        custom_index = self.accent_mode_combo.findData("custom")
        with QSignalBlocker(self.accent_mode_combo):
            self.accent_mode_combo.setCurrentIndex(max(0, custom_index))
        self._update_accent_controls()
        self._refresh_dirty_state()
        self.accent_changed.emit("custom", self.current_accent_color())

    def _reset_accent(self) -> None:
        self._accent_color = "#8ed35b"
        theme_index = self.accent_mode_combo.findData("theme")
        with QSignalBlocker(self.accent_mode_combo):
            self.accent_mode_combo.setCurrentIndex(max(0, theme_index))
        self._update_accent_controls()
        self._refresh_dirty_state()
        self.accent_changed.emit("theme", self.current_accent_color())

    def _update_accent_controls(self) -> None:
        if not hasattr(self, "accent_color_button"):
            return
        mode = self.current_accent_mode()
        color = self.current_accent_color() if mode == "custom" else self._theme_accent_color()
        self.accent_color_button.setEnabled(True)
        self.accent_reset_button.setEnabled(mode == "custom")
        self.accent_color_button.setText(tr("appearance.accent.color_value", color=color))
        text_color = "#111111" if QColor(color).lightnessF() > 0.62 else "#ffffff"
        self.accent_color_button.setStyleSheet(f"QPushButton {{ background-color: {color}; color: {text_color}; border: 2px solid {color}; }}")
        key = "appearance.accent.detail.custom" if mode == "custom" else "appearance.accent.detail.theme"
        self.accent_detail_label.setText(tr(key, color=color))

    def _emit_motion_mode_changed(self, _index: int) -> None:
        self.motion_mode_changed.emit(self.current_motion_mode())

    def _emit_language_changed(self, _index: int) -> None:
        locale = self.language_combo.currentData()
        if locale:
            self.language_changed.emit(str(locale))

    def set_settings(self, settings: dict, preserve_unsaved: bool = False) -> None:
        preserve = bool(preserve_unsaved and self._dirty and not self._force_replace_on_next_settings)
        pending_data = self.form_data() if preserve else None
        self._tracking_suspended = True
        try:
            self._apply_form_data(settings)
            self._saved_data = self.form_data()
            if pending_data is not None:
                self._apply_form_data(pending_data)
        finally:
            self._tracking_suspended = False
            self._force_replace_on_next_settings = False
        self._set_dirty(self.form_data() != self._saved_data)
        if pending_data is not None:
            self.language_changed.emit(str(pending_data.get("language", "en-US")))
            self.reload_theme_requested.emit(str(pending_data.get("theme", "mcw-default")))
            self.motion_mode_changed.emit(str(pending_data.get("motion_mode", "full")))
            self.accent_changed.emit(str(pending_data.get("accent_mode", "theme")), str(pending_data.get("accent_color", "#8ed35b")))

    def form_data(self) -> dict:
        return {
            "start_page": self.start_page_combo.currentData(),
            "show_snapshots": self.show_snapshots.isChecked(),
            "debug_mode": self.debug_mode.isChecked(),
            "prefer_dedicated_gpu": self.prefer_dedicated_gpu.isEnabled() and self.prefer_dedicated_gpu.isChecked(),
            "remember_window_size": self.remember_window_size.isChecked(),
            "language": self.language_combo.currentData() or "en-US",
            "show_content_descriptions": self.show_content_descriptions.isChecked(),
            "auto_check_updates": self.auto_check_updates.isChecked(),
            "tester_mode": self.join_tester_program.isChecked(),
            "theme": self.theme_combo.currentData() or "mcw-default",
            "show_static_text": self.show_static_text.isChecked(),
            "motion_mode": self.current_motion_mode(),
            "live_theme_reload": self.live_theme_reload.isChecked(),
            "accent_mode": self.current_accent_mode(),
            "accent_color": self.current_accent_color(),
            "modrinth_include_beta": self.modrinth_include_beta.isChecked(),
            "modrinth_include_alpha": self.modrinth_include_alpha.isChecked(),
            "block_launch_on_modrinth_failure": self.block_modrinth_failure.isChecked(),
            "block_launch_on_curseforge_failure": self.block_curseforge_failure.isChecked(),
            "allow_launch_on_forge_preflight_failure": self.allow_forge_preflight_failure.isChecked(),
            "curseforge_gateway_urls": [field.text().strip() for field in self.curseforge_gateway_inputs],
            "download_limit_mbps": self.download_limit_mbps.value() if self.limit_download_speed.isChecked() else 0.0,
            "download_concurrency": int(self.download_concurrency.currentData() or 0),
            "instance_defaults": copy.deepcopy(self._instance_defaults),
        }

    def request_save(self) -> None:
        self._force_replace_on_next_settings = True
        self.save_requested.emit(self.form_data())

    def request_reset(self) -> None:
        self._force_replace_on_next_settings = True
        self.reset_requested.emit()

    def discard_changes(self) -> None:
        if not self._saved_data:
            return
        self._tracking_suspended = True
        try:
            self._apply_form_data(self._saved_data)
        finally:
            self._tracking_suspended = False
        self._set_dirty(False)
        self.language_changed.emit(str(self._saved_data.get("language", "en-US")))
        self.reload_theme_requested.emit(str(self._saved_data.get("theme", "mcw-default")))
        self.motion_mode_changed.emit(str(self._saved_data.get("motion_mode", "full")))
        self.accent_changed.emit(str(self._saved_data.get("accent_mode", "theme")), str(self._saved_data.get("accent_color", "#8ed35b")))

    def set_update_status(self, message: str) -> None:
        self.update_status_label.setText(message)

    def set_busy(self, busy: bool) -> None:
        self.set_interaction_locked(busy)

    def set_update_busy(self, busy: bool) -> None:
        self.check_updates_button.setEnabled(not busy)

    def retranslate_dynamic(self) -> None:
        self.unsaved_label.setText(tr("settings.unsaved.banner"))
        if self.java_card.title_label is not None:
            self.java_card.title_label.setText(tr("launcher_settings.java.title"))
        if self.java_card.subtitle_label is not None:
            self.java_card.subtitle_label.setText(tr("launcher_settings.java.description"))
        self.scan_java_button.setText(tr("launcher_settings.java.scan"))
        self.open_java_button.setText(tr("launcher_settings.java.open_folder"))
        self.java_install_label.setText(tr("launcher_settings.java.install_label"))
        current_major = int(self.java_install_combo.currentData() or 17)
        self._populate_java_install_combo(current_major)
        self._update_java_details()
        if self.gpu_card.title_label is not None:
            self.gpu_card.title_label.setText(tr("gpu.preference.title"))
        if self.gpu_card.subtitle_label is not None:
            self.gpu_card.subtitle_label.setText(tr("gpu.preference.detail"))
        self.prefer_dedicated_gpu.setText(tr("gpu.preference.toggle"))
        self._update_gpu_status()
        for index, label in enumerate(self.curseforge_gateway_labels, start=1):
            label.setText(tr("curseforge.gateway.slot", index=index))
        self.reveal_curseforge_gateways.setText(tr("curseforge.gateway.reveal.toggle"))
        self.curseforge_gateway_security.setText(tr("curseforge.gateway.security.note"))
        if self.content_browser_card.title_label is not None:
            self.content_browser_card.title_label.setText(tr("content.settings.title"))
        if self.content_browser_card.subtitle_label is not None:
            self.content_browser_card.subtitle_label.setText(tr("content.settings.detail"))
        self.show_content_descriptions.setText(tr("content.settings.show_descriptions"))
        self.block_modrinth_failure.setText(tr("managed_content.modrinth.block"))
        self.block_curseforge_failure.setText(tr("managed_content.curseforge.block"))
        self.allow_forge_preflight_failure.setText(tr("forge_preflight.launcher.allow"))
        self.forge_preflight_warning_label.setText(tr("forge_preflight.warning"))
        if self.instance_defaults_card.title_label is not None:
            self.instance_defaults_card.title_label.setText(tr("instance_defaults.launcher.title"))
        if self.instance_defaults_card.subtitle_label is not None:
            self.instance_defaults_card.subtitle_label.setText(tr("instance_defaults.launcher.description"))
        self.edit_instance_defaults_button.setText(tr("instance_defaults.launcher.edit"))
        self.motion_mode_label.setText(tr("motion.mode.label"))
        self.motion_mode_detail.setText(tr("motion.mode.detail"))
        self.accent_mode_label.setText(tr("appearance.accent.mode.label"))
        self.accent_reset_button.setText(tr("appearance.accent.reset"))
        self._reload_accent_modes()
        self._update_accent_controls()
        self.reload_theme_button.setText(tr("theme.authoring.reload"))
        self.live_theme_reload.setText(tr("theme.authoring.live_reload"))
        self.live_theme_reload.setToolTip(tr("theme.authoring.live_reload.detail"))
        self.theme_details_button.setText(tr("theme.authoring.details"))
        self.theme_open_button.setText(tr("theme.authoring.open_folder"))
        self.theme_duplicate_button.setText(tr("theme.authoring.duplicate"))
        self.theme_import_button.setText(tr("theme.authoring.import"))
        self.theme_export_button.setText(tr("theme.authoring.export"))
        self._update_theme_authoring_state()
        if self.motion_preview_card.title_label is not None:
            self.motion_preview_card.title_label.setText(tr("motion.preview.title"))
        if self.motion_preview_card.subtitle_label is not None:
            self.motion_preview_card.subtitle_label.setText(tr("motion.preview.description"))
        self.preview_success_label.setText(tr("motion.preview.success"))
        self.preview_warning_label.setText(tr("motion.preview.warning"))
        self.preview_error_label.setText(tr("motion.preview.error"))
        self.preview_determinate.setFormat(tr("motion.preview.progress", value=64))
        self.preview_indeterminate.setFormat(tr("motion.preview.indeterminate"))
        self.preview_toast_button.setText(tr("motion.preview.toast_button"))
        self.preview_font_label.setText(tr("theme.authoring.preview.font_sample"))
        self.preview_default_button.setText(tr("theme.authoring.preview.default_button"))
        self.preview_primary_button.setText(tr("theme.authoring.preview.primary_button"))
        self.preview_disabled_button.setText(tr("theme.authoring.preview.disabled_button"))
        self.preview_dialog_button.setText(tr("theme.authoring.preview.dialog_button"))
        self._reload_motion_modes()
        self._update_instance_defaults_summary()
        self._update_save_button_text()

    def _apply_form_data(self, settings: dict) -> None:
        persisted_controls = (
            self.start_page_combo,
            self.show_snapshots,
            self.debug_mode,
            self.prefer_dedicated_gpu,
            self.remember_window_size,
            self.auto_check_updates,
            self.show_content_descriptions,
            self.modrinth_include_beta,
            self.modrinth_include_alpha,
            self.block_modrinth_failure,
            self.block_curseforge_failure,
            self.allow_forge_preflight_failure,
            self.limit_download_speed,
            self.download_limit_mbps,
            self.download_concurrency,
            self.join_tester_program,
            self.language_combo,
            self.theme_combo,
            self.motion_mode_combo,
            self.accent_mode_combo,
            self.show_static_text,
            self.live_theme_reload,
            *self.curseforge_gateway_inputs,
        )
        blockers = [QSignalBlocker(control) for control in persisted_controls]
        index = self.start_page_combo.findData(settings.get("start_page", "instances"))
        self.start_page_combo.setCurrentIndex(max(0, index))
        self.show_snapshots.setChecked(bool(settings.get("show_snapshots", False)))
        self.debug_mode.setChecked(bool(settings.get("debug_mode", False)))
        self.prefer_dedicated_gpu.setChecked(bool(settings.get("prefer_dedicated_gpu", False)) and self._gpu_detection.has_dedicated_gpu)
        self.remember_window_size.setChecked(bool(settings.get("remember_window_size", True)))
        self.auto_check_updates.setChecked(bool(settings.get("auto_check_updates", True)))
        self.show_content_descriptions.setChecked(bool(settings.get("show_content_descriptions", False)))
        self.modrinth_include_beta.setChecked(bool(settings.get("modrinth_include_beta", False)))
        self.modrinth_include_alpha.setChecked(bool(settings.get("modrinth_include_alpha", False)))
        self.block_modrinth_failure.setChecked(bool(settings.get("block_launch_on_modrinth_failure", True)))
        self.block_curseforge_failure.setChecked(bool(settings.get("block_launch_on_curseforge_failure", True)))
        self.allow_forge_preflight_failure.setChecked(bool(settings.get("allow_launch_on_forge_preflight_failure", False)))
        gateway_urls = list(settings.get("curseforge_gateway_urls", ()) or ())[:5]
        gateway_urls.extend([""] * (5 - len(gateway_urls)))
        for field, value in zip(self.curseforge_gateway_inputs, gateway_urls):
            field.setText(str(value or ""))
        self._mask_gateway_links()
        download_limit = max(0.0, float(settings.get("download_limit_mbps", 0.0) or 0.0))
        self.limit_download_speed.setChecked(download_limit > 0)
        self.download_limit_mbps.setValue(download_limit if download_limit > 0 else 10.0)
        self.download_limit_mbps.setEnabled(download_limit > 0)
        concurrency = int(settings.get("download_concurrency", 0) or 0)
        concurrency_index = self.download_concurrency.findData(concurrency)
        self.download_concurrency.setCurrentIndex(max(0, concurrency_index))
        tester_mode = bool(settings.get("tester_mode", str(settings.get("update_channel", "stable")).strip().lower() == "beta"))
        self.join_tester_program.setChecked(tester_mode)
        self.tester_warning_label.setVisible(tester_mode)
        self.reload_languages()
        language_index = self.language_combo.findData(settings.get("language", "en-US"))
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentIndex(max(0, language_index))
        self.language_combo.blockSignals(False)
        self.reload_themes()
        theme_index = self.theme_combo.findData(settings.get("theme", "mcw-default"))
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(max(0, theme_index))
        self.theme_combo.blockSignals(False)
        motion_index = self.motion_mode_combo.findData(str(settings.get("motion_mode", "full")))
        self.motion_mode_combo.setCurrentIndex(max(0, motion_index))
        accent_index = self.accent_mode_combo.findData(str(settings.get("accent_mode", "theme")))
        self.accent_mode_combo.setCurrentIndex(max(0, accent_index))
        try:
            self._accent_color = normalize_hex_color(settings.get("accent_color", "#8ed35b"))
        except ValueError:
            self._accent_color = "#8ed35b"
        self._update_accent_controls()
        self.show_static_text.setChecked(bool(settings.get("show_static_text", False)))
        self.live_theme_reload.setChecked(bool(settings.get("live_theme_reload", False)))
        self._set_live_theme_reload(self.live_theme_reload.isChecked())
        self._instance_defaults = SettingsManager.normalize_dict(settings.get("instance_defaults"))
        self._update_instance_defaults_summary()
        del blockers

    def _edit_instance_defaults(self) -> None:
        dialog = InstanceSettingsEditorDialog(
            self._instance_defaults,
            self,
            title=tr("instance_defaults.editor.title"),
        )
        if not dialog.exec():
            return
        self._instance_defaults = dialog.settings_data
        self._update_instance_defaults_summary()
        self._refresh_dirty_state()

    def _update_instance_defaults_summary(self) -> None:
        self.instance_defaults_summary.setText(InstanceSettingsEditorDialog.summary(self._instance_defaults))


    def _set_gateway_links_revealed(self, revealed: bool) -> None:
        if not revealed:
            self._mask_gateway_links()
            return
        with QSignalBlocker(self.reveal_curseforge_gateways):
            self.reveal_curseforge_gateways.setChecked(False)
        if not any(field.text().strip() for field in self.curseforge_gateway_inputs):
            self._mask_gateway_links()
            return
        if not confirm_reveal_protected_values(self, countdown_seconds=5):
            self._mask_gateway_links()
            return
        for field in self.curseforge_gateway_inputs:
            field.setEchoMode(QLineEdit.EchoMode.Normal)
        with QSignalBlocker(self.reveal_curseforge_gateways):
            self.reveal_curseforge_gateways.setChecked(True)

    def _mask_gateway_links(self) -> None:
        for field in self.curseforge_gateway_inputs:
            field.setEchoMode(QLineEdit.EchoMode.Password)
        with QSignalBlocker(self.reveal_curseforge_gateways):
            self.reveal_curseforge_gateways.setChecked(False)




    def _show_preview_dialog(self) -> None:
        QMessageBox.information(self, tr("theme.authoring.preview.dialog.title"), tr("theme.authoring.preview.dialog.message"))

    def _selected_theme(self):
        theme_id = str(self.theme_combo.currentData() or "mcw-default")
        return next((theme for theme in theme_manager.available_themes() if theme.theme_id == theme_id), None)

    def _on_theme_selection_changed(self, _index: int) -> None:
        self._update_theme_authoring_state()
        self._update_accent_controls()
        self._watch_selected_theme()

    def _update_theme_authoring_state(self) -> None:
        if not hasattr(self, "theme_status_label"):
            return
        theme = self._selected_theme()
        editable = theme is not None and theme.root is not None
        self.theme_open_button.setEnabled(editable)
        self.theme_duplicate_button.setEnabled(editable)
        self.theme_export_button.setEnabled(editable)
        self.theme_details_button.setEnabled(theme is not None)
        if theme is None:
            self.theme_status_label.setText(tr("theme.authoring.status.missing"))
        elif theme.issues:
            self.theme_status_label.setText(tr("theme.authoring.status.issues", count=len(theme.issues)))
        else:
            self.theme_status_label.setText(tr("theme.authoring.status.clean"))

    def _show_theme_details(self) -> None:
        theme_id = str(self.theme_combo.currentData() or "mcw-default")
        ThemeIssuesDialog(self._theme_authoring.validate(theme_id), self).exec()

    def _open_theme_folder(self) -> None:
        theme = self._selected_theme()
        if theme is None or theme.root is None:
            QMessageBox.information(self, tr("theme.authoring.title"), tr("theme.authoring.no_folder"))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(theme.root)))

    def _duplicate_theme(self) -> None:
        theme = self._selected_theme()
        if theme is None or theme.root is None:
            return
        default_id = f"{theme.theme_id}-copy"
        new_id, accepted = QInputDialog.getText(self, tr("theme.authoring.duplicate.title"), tr("theme.authoring.duplicate.id"), QLineEdit.EchoMode.Normal, default_id)
        if not accepted or not new_id.strip():
            return
        new_name, accepted = QInputDialog.getText(self, tr("theme.authoring.duplicate.title"), tr("theme.authoring.duplicate.name"), QLineEdit.EchoMode.Normal, f"{theme.name} Copy")
        if not accepted:
            return
        try:
            created = self._theme_authoring.duplicate(theme.theme_id, new_id, new_name)
        except ThemeAuthoringError as error:
            QMessageBox.warning(self, tr("theme.authoring.title"), str(error))
            return
        self.reload_themes()
        index = self.theme_combo.findData(created.theme_id)
        self.theme_combo.setCurrentIndex(max(0, index))
        self._emit_theme_preview()

    def _import_theme(self) -> None:
        filename, _filter = QFileDialog.getOpenFileName(self, tr("theme.authoring.import.title"), str(theme_manager.root), tr("theme.authoring.zip_filter"))
        if not filename:
            return
        try:
            imported = self._theme_authoring.import_archive(Path(filename))
        except ThemeAuthoringError as error:
            QMessageBox.warning(self, tr("theme.authoring.title"), str(error))
            return
        self.reload_themes()
        index = self.theme_combo.findData(imported.theme_id)
        self.theme_combo.setCurrentIndex(max(0, index))
        self._emit_theme_preview()
        QMessageBox.information(self, tr("theme.authoring.title"), tr("theme.authoring.import.success", theme=imported.name))

    def _export_theme(self) -> None:
        theme = self._selected_theme()
        if theme is None or theme.root is None:
            return
        filename, _filter = QFileDialog.getSaveFileName(self, tr("theme.authoring.export.title"), str(theme_manager.root / f"{theme.theme_id}.zip"), tr("theme.authoring.zip_filter"))
        if not filename:
            return
        try:
            output = self._theme_authoring.export(theme.theme_id, Path(filename))
        except ThemeAuthoringError as error:
            QMessageBox.warning(self, tr("theme.authoring.title"), str(error))
            return
        QMessageBox.information(self, tr("theme.authoring.title"), tr("theme.authoring.export.success", path=str(output)))

    def _set_live_theme_reload(self, enabled: bool) -> None:
        self._theme_live_reload.set_enabled(enabled)
        self._watch_selected_theme()

    def _watch_selected_theme(self) -> None:
        theme = self._selected_theme()
        self._theme_live_reload.watch(theme.theme_id if theme is not None else "", theme.root if theme is not None else None)

    def _handle_live_theme_reload(self, theme_id: str) -> None:
        current = str(self.theme_combo.currentData() or "")
        if theme_id != current:
            return
        report = self._theme_authoring.validate(theme_id)
        if not report.is_valid:
            self.theme_status_label.setText(tr("theme.authoring.live_reload.invalid", count=report.error_count))
            return
        self.reload_themes()
        index = self.theme_combo.findData(theme_id)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.live_theme_reload_requested.emit(theme_id)

    def hideEvent(self, event) -> None:
        self._mask_gateway_links()
        super().hideEvent(event)

    def _refresh_dirty_state(self, *_args) -> None:
        if self._tracking_suspended:
            return
        self._set_dirty(self.form_data() != self._saved_data)

    def _set_dirty(self, dirty: bool) -> None:
        dirty = bool(dirty)
        changed = dirty != self._dirty
        self._dirty = dirty
        self.unsaved_label.setVisible(dirty)
        self.unsaved_label.setText(tr("settings.unsaved.banner"))
        self.save_button.setProperty("unsavedChanges", dirty)
        self.save_button.style().unpolish(self.save_button)
        self.save_button.style().polish(self.save_button)
        self._update_save_button_text()
        if changed:
            self.dirty_changed.emit(dirty)

    def _update_save_button_text(self) -> None:
        label = tr("Save launcher settings")
        self.save_button.setText(f"● {label}" if self._dirty else label)

    def _queue_theme_preview(self, _checked: bool) -> None:
        self._theme_preview_timer.start()

    def _emit_theme_preview(self) -> None:
        theme_id = str(self.theme_combo.currentData() or "mcw-default")
        report = self._theme_authoring.validate(theme_id)
        if not report.is_valid:
            self.theme_status_label.setText(tr("theme.authoring.live_reload.invalid", count=report.error_count))
            ThemeIssuesDialog(report, self).exec()
            return
        self.reload_themes()
        index = self.theme_combo.findData(theme_id)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.reload_theme_requested.emit(theme_id)
