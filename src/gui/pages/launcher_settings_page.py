from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, QTimer, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QLabel, QLineEdit, QPushButton

from src.core.language.language_manager import language_manager, tr
from src.core.theme.theme_manager import theme_manager
from src.gui.config import NAVIGATION_ITEMS, VERSION
from src.gui.dialogs.protected_value_reveal_dialog import confirm_reveal_protected_values
from src.gui.pages.base_page import BasePage
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget


class LauncherSettingsPage(BasePage):
    save_requested = Signal(dict)
    reset_requested = Signal()
    language_changed = Signal(str)
    check_updates_requested = Signal()
    reload_theme_requested = Signal(str)
    scan_java_requested = Signal()
    open_java_requested = Signal(object)
    dirty_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__("Launcher Settings", "Preferences here belong to the GUI, not to an individual Minecraft instance.", "launcher_settings")
        self._java_installations: list[object] = []
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
        self.root_layout.addWidget(behavior_card)

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
        bandwidth_card.layout.addWidget(self.limit_download_speed)
        bandwidth_card.layout.addWidget(self.download_limit_mbps)
        self.root_layout.addWidget(bandwidth_card)

        language_card = CardWidget("Language", "Add another language by placing a compatible JSON file in the lang folder.")
        self.language_combo = QComboBox()
        self.reload_languages()
        self.language_combo.currentIndexChanged.connect(self._emit_language_changed)
        reload_languages_button = set_theme_icon(QPushButton("Reload language packs"), "icon.action.language")
        reload_languages_button.clicked.connect(self.reload_languages)
        language_card.layout.addWidget(QLabel("Launcher language"))
        language_card.layout.addWidget(self.language_combo)
        language_card.layout.addWidget(reload_languages_button)
        self.root_layout.addWidget(language_card)

        modrinth_card = CardWidget("Modrinth release channels", "Release versions are always shown. Enable Beta or Alpha only when you accept less stable project versions.")
        self.modrinth_include_beta = QCheckBox("Include Beta mod and modpack versions")
        self.modrinth_include_alpha = QCheckBox("Include Alpha mod and modpack versions")
        modrinth_card.layout.addWidget(self.modrinth_include_beta)
        modrinth_card.layout.addWidget(self.modrinth_include_alpha)
        self.root_layout.addWidget(modrinth_card)

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
        self.root_layout.addWidget(curseforge_card)

        java_card = CardWidget("Java installations", "Scan Java from JAVA_HOME, PATH, Program Files, the Windows Registry, and managed runtimes.")
        java_card.setProperty("themeRole", "java")
        self.java_combo = QComboBox()
        self.java_combo.currentIndexChanged.connect(self._update_java_details)
        self.java_details = QLabel("Java scan has not run yet.")
        self.java_details.setObjectName("MutedLabel")
        self.java_details.setWordWrap(True)
        scan_java_button = set_theme_icon(QPushButton("Scan Java installations"), "icon.action.java")
        scan_java_button.clicked.connect(self.scan_java_requested.emit)
        self.open_java_button = set_theme_icon(QPushButton("Open selected Java folder"), "icon.action.folder")
        self.open_java_button.setEnabled(False)
        self.open_java_button.clicked.connect(lambda: self.open_java_requested.emit(self.current_java_installation()))
        java_card.layout.addWidget(self.java_combo)
        java_card.layout.addWidget(self.java_details)
        java_card.layout.addWidget(scan_java_button)
        java_card.layout.addWidget(self.open_java_button)
        self.root_layout.addWidget(java_card)

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
        self.root_layout.addWidget(update_card)

        appearance_card = CardWidget("Appearance", "PNG theme files are optional. Missing or invalid files automatically fall back to the built-in CSS interface.")
        self.theme_combo = QComboBox()
        self.reload_themes()
        self.show_static_text = QCheckBox("Show static text over themed controls")
        self.show_static_text.setToolTip("Disabled by default. Enable this only when you want launcher text drawn over themed PNG controls.")
        reload_theme_button = set_theme_icon(QPushButton("Reload and preview theme"), "icon.action.theme")
        reload_theme_button.clicked.connect(self._emit_theme_preview)
        self.show_static_text.toggled.connect(self._queue_theme_preview)
        appearance_card.layout.addWidget(QLabel("Launcher theme"))
        appearance_card.layout.addWidget(self.theme_combo)
        appearance_card.layout.addWidget(self.show_static_text)
        appearance_card.layout.addWidget(reload_theme_button)
        self.root_layout.addWidget(appearance_card)

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
        self.limit_download_speed.toggled.connect(self._refresh_dirty_state)
        self.download_limit_mbps.valueChanged.connect(self._refresh_dirty_state)
        self.language_combo.currentIndexChanged.connect(self._refresh_dirty_state)
        self.modrinth_include_beta.toggled.connect(self._refresh_dirty_state)
        self.modrinth_include_alpha.toggled.connect(self._refresh_dirty_state)
        for field in self.curseforge_gateway_inputs:
            field.textChanged.connect(self._refresh_dirty_state)
        self.auto_check_updates.toggled.connect(self._refresh_dirty_state)
        self.join_tester_program.toggled.connect(self._refresh_dirty_state)
        self.theme_combo.currentIndexChanged.connect(self._refresh_dirty_state)
        self.show_static_text.toggled.connect(self._refresh_dirty_state)

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
            self.java_details.setText("No Java installation detected.")
            self.open_java_button.setEnabled(False)
            return
        source = getattr(getattr(item, "source", None), "value", "unknown")
        self.java_details.setText(tr("launcher_settings.java.details", major=getattr(item, "major_version", "?"), vendor=getattr(item, "vendor", "") or tr("common.unknown"), architecture=getattr(item, "architecture", "") or tr("common.unknown"), path=getattr(item, "executable", ""), source=source))
        self.open_java_button.setEnabled(True)

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
                label += f" ({len(theme.issues)} fallback asset(s))"
            self.theme_combo.addItem(label, theme.theme_id)
        selected = str(current_theme or theme_manager.current.theme_id or "mcw-default")
        index = self.theme_combo.findData(selected)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.theme_combo.blockSignals(False)

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

    def form_data(self) -> dict:
        return {
            "start_page": self.start_page_combo.currentData(),
            "show_snapshots": self.show_snapshots.isChecked(),
            "debug_mode": self.debug_mode.isChecked(),
            "remember_window_size": self.remember_window_size.isChecked(),
            "language": self.language_combo.currentData() or "en-US",
            "auto_check_updates": self.auto_check_updates.isChecked(),
            "tester_mode": self.join_tester_program.isChecked(),
            "theme": self.theme_combo.currentData() or "mcw-default",
            "show_static_text": self.show_static_text.isChecked(),
            "modrinth_include_beta": self.modrinth_include_beta.isChecked(),
            "modrinth_include_alpha": self.modrinth_include_alpha.isChecked(),
            "curseforge_gateway_urls": [field.text().strip() for field in self.curseforge_gateway_inputs],
            "download_limit_mbps": self.download_limit_mbps.value() if self.limit_download_speed.isChecked() else 0.0,
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

    def set_update_status(self, message: str) -> None:
        self.update_status_label.setText(message)

    def set_update_busy(self, busy: bool) -> None:
        self.check_updates_button.setEnabled(not busy)

    def retranslate_dynamic(self) -> None:
        self.unsaved_label.setText(tr("settings.unsaved.banner"))
        for index, label in enumerate(self.curseforge_gateway_labels, start=1):
            label.setText(tr("curseforge.gateway.slot", index=index))
        self.reveal_curseforge_gateways.setText(tr("curseforge.gateway.reveal.toggle"))
        self.curseforge_gateway_security.setText(tr("curseforge.gateway.security.note"))
        self._update_save_button_text()

    def _apply_form_data(self, settings: dict) -> None:
        persisted_controls = (
            self.start_page_combo,
            self.show_snapshots,
            self.debug_mode,
            self.remember_window_size,
            self.auto_check_updates,
            self.modrinth_include_beta,
            self.modrinth_include_alpha,
            self.limit_download_speed,
            self.download_limit_mbps,
            self.join_tester_program,
            self.language_combo,
            self.theme_combo,
            self.show_static_text,
            *self.curseforge_gateway_inputs,
        )
        blockers = [QSignalBlocker(control) for control in persisted_controls]
        index = self.start_page_combo.findData(settings.get("start_page", "home"))
        self.start_page_combo.setCurrentIndex(max(0, index))
        self.show_snapshots.setChecked(bool(settings.get("show_snapshots", False)))
        self.debug_mode.setChecked(bool(settings.get("debug_mode", False)))
        self.remember_window_size.setChecked(bool(settings.get("remember_window_size", True)))
        self.auto_check_updates.setChecked(bool(settings.get("auto_check_updates", True)))
        self.modrinth_include_beta.setChecked(bool(settings.get("modrinth_include_beta", False)))
        self.modrinth_include_alpha.setChecked(bool(settings.get("modrinth_include_alpha", False)))
        gateway_urls = list(settings.get("curseforge_gateway_urls", ()) or ())[:5]
        gateway_urls.extend([""] * (5 - len(gateway_urls)))
        for field, value in zip(self.curseforge_gateway_inputs, gateway_urls):
            field.setText(str(value or ""))
        self._mask_gateway_links()
        download_limit = max(0.0, float(settings.get("download_limit_mbps", 0.0) or 0.0))
        self.limit_download_speed.setChecked(download_limit > 0)
        self.download_limit_mbps.setValue(download_limit if download_limit > 0 else 10.0)
        self.download_limit_mbps.setEnabled(download_limit > 0)
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
        self.show_static_text.setChecked(bool(settings.get("show_static_text", False)))
        del blockers


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
        self.reload_theme_requested.emit(str(self.theme_combo.currentData() or "mcw-default"))
