from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider, QSpinBox, QTextEdit, QVBoxLayout

from src.core.config.managed_content_policy import ManagedContentPolicy
from src.core.language.language_manager import tr
from src.core.system.memory import MemoryAllocationPolicy, SystemMemory
from src.gui.pages.base_page import BasePage
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget
from src.gui.widget.settings_section import SettingsSection


class InstanceSettingsPage(BasePage):
    load_requested = Signal(str)
    save_requested = Signal(str, dict)
    lan_prepare_requested = Signal(str, str, str)
    lan_agent_log_requested = Signal(str)
    dirty_changed = Signal(bool)

    def __init__(self, total_memory_mb: int | None = None) -> None:
        super().__init__("Instance Settings", "Settings are loaded and saved through the public SettingsManager API.", "instance_settings")
        detected_memory_mb = int(total_memory_mb) if total_memory_mb is not None else SystemMemory.total_physical_memory_mb()
        self._memory_detection_failed = detected_memory_mb <= 0
        self._physical_memory_mb = detected_memory_mb if detected_memory_mb > 0 else MemoryAllocationPolicy.FALLBACK_PHYSICAL_LIMIT_MB
        self._memory_limit_mb = max(MemoryAllocationPolicy.MIN_MEMORY_MB, self._physical_memory_mb)
        self._tracking_suspended = True
        self._dirty = False
        self._saved_data: dict = {}
        self._loaded_instance_name = ""
        self._build_ui()
        self._connect_dirty_tracking()
        self._tracking_suspended = False
        self._set_dirty(False)

    def _build_ui(self) -> None:
        self.unsaved_label = QLabel()
        self.unsaved_label.setObjectName("UnsavedChangesBanner")
        self.unsaved_label.setWordWrap(True)
        self.unsaved_label.setVisible(False)
        self.root_layout.addWidget(self.unsaved_label)

        target_section = SettingsSection("instance.settings.section.target", "instance.settings.section.target_detail")
        runtime_section = SettingsSection("instance.settings.section.runtime", "instance.settings.section.runtime_detail")
        multiplayer_section = SettingsSection("instance.settings.section.multiplayer", "instance.settings.section.multiplayer_detail")
        advanced_section = SettingsSection("instance.settings.section.advanced", "instance.settings.section.advanced_detail")
        for section in (target_section, runtime_section, multiplayer_section, advanced_section):
            self.root_layout.addWidget(section)

        selector_card = CardWidget("Target instance")
        self.instance_combo = QComboBox()
        self.instance_combo.currentTextChanged.connect(self.load_requested.emit)
        reload_button = set_theme_icon(QPushButton("Reload settings"), "icon.action.refresh")
        reload_button.clicked.connect(lambda: self.load_requested.emit(self.current_instance_name()))
        selector_card.layout.addWidget(self.instance_combo)
        selector_card.layout.addWidget(reload_button)
        target_section.add_card(selector_card, span=2)

        java_card = CardWidget("Java and memory")
        self.java_path_input = QLineEdit()
        self.java_path_input.setPlaceholderText("Leave empty for automatic Java selection")
        browse_button = set_theme_icon(QPushButton("Browse Java executable"), "icon.action.folder")
        browse_button.clicked.connect(self._browse_java)
        self.memory_info_label = QLabel()
        self.memory_info_label.setObjectName("CardSubtitle")
        self.memory_info_label.setWordWrap(True)
        self.min_memory = self._create_memory_slider()
        self.max_memory = self._create_memory_slider()
        self.min_memory_input = self._create_memory_input()
        self.max_memory_input = self._create_memory_input()
        self.max_memory.setRange(MemoryAllocationPolicy.MIN_MEMORY_MB, self._memory_limit_mb)
        self.max_memory_input.setRange(MemoryAllocationPolicy.MIN_MEMORY_MB, self._memory_limit_mb)
        self.min_memory_value = QLabel()
        self.max_memory_value = QLabel()
        self.min_memory_value.setObjectName("MemoryValueLabel")
        self.max_memory_value.setObjectName("MemoryValueLabel")
        minimum_tooltip = "Minimum memory cannot be higher than maximum memory."
        maximum_tooltip = "Maximum memory cannot be higher than detected physical memory."
        self.min_memory.setToolTip(minimum_tooltip)
        self.min_memory_input.setToolTip(minimum_tooltip)
        self.max_memory.setToolTip(maximum_tooltip)
        self.max_memory_input.setToolTip(maximum_tooltip)
        self.max_memory.valueChanged.connect(self._on_max_memory_slider_changed)
        self.min_memory.valueChanged.connect(self._on_min_memory_slider_changed)
        self.max_memory_input.valueChanged.connect(self._on_max_memory_input_changed)
        self.min_memory_input.valueChanged.connect(self._on_min_memory_input_changed)

        memory_grid = QGridLayout()
        memory_grid.setHorizontalSpacing(14)
        memory_grid.setVerticalSpacing(8)
        memory_grid.setColumnStretch(0, 1)
        memory_grid.addWidget(self.memory_info_label, 0, 0, 1, 3)
        memory_grid.addWidget(QLabel("Minimum memory"), 1, 0)
        memory_grid.addWidget(self.min_memory_value, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        memory_grid.addWidget(self.min_memory_input, 1, 2)
        memory_grid.addWidget(self.min_memory, 2, 0, 1, 3)
        memory_grid.addWidget(QLabel("Maximum memory"), 3, 0)
        memory_grid.addWidget(self.max_memory_value, 3, 1, alignment=Qt.AlignmentFlag.AlignRight)
        memory_grid.addWidget(self.max_memory_input, 3, 2)
        memory_grid.addWidget(self.max_memory, 4, 0, 1, 3)
        java_card.layout.addWidget(self.java_path_input)
        java_card.layout.addWidget(browse_button)
        java_card.layout.addLayout(memory_grid)
        runtime_section.add_card(java_card)
        self._apply_memory_values(MemoryAllocationPolicy.DEFAULT_MIN_MEMORY_MB, MemoryAllocationPolicy.DEFAULT_MAX_MEMORY_MB)

        window_card = CardWidget("Game window")
        self.window_width = QSpinBox()
        self.window_height = QSpinBox()
        for spin_box in (self.window_width, self.window_height):
            spin_box.setRange(320, 7680)

        self.window_width_label = QLabel("Width")
        self.window_height_label = QLabel("Height")
        width_field = QVBoxLayout()
        width_field.setContentsMargins(0, 0, 0, 0)
        width_field.setSpacing(6)
        width_field.addWidget(self.window_width_label)
        width_field.addWidget(self.window_width)
        height_field = QVBoxLayout()
        height_field.setContentsMargins(0, 0, 0, 0)
        height_field.setSpacing(6)
        height_field.addWidget(self.window_height_label)
        height_field.addWidget(self.window_height)

        self.window_size_row = QHBoxLayout()
        self.window_size_row.setContentsMargins(0, 0, 0, 0)
        self.window_size_row.setSpacing(10)
        self.window_size_row.addLayout(width_field, 1)
        self.window_size_row.addLayout(height_field, 1)

        self.fullscreen = QCheckBox("Launch in fullscreen")
        window_card.layout.addLayout(self.window_size_row)
        window_card.layout.addWidget(self.fullscreen)
        window_card.layout.addStretch(1)
        runtime_section.add_card(window_card)

        hosting_card = CardWidget(
            "LAN hosting",
            "Authentication policy and connection transport are configured separately. Private LAN uses the bundled MCW LAN Agent; no custom authentication service is used.",
        )
        self.lan_auth_mode = QComboBox()
        self.lan_auth_mode.addItem("Microsoft accounts only", "microsoft_only")
        self.lan_auth_mode.addItem("Private group — Microsoft and Offline accounts", "private_offline")
        self.lan_connection_provider = QComboBox()
        self.lan_connection_provider.addItem("Manual connection — LAN, VPN, direct port, or custom relay", "manual")
        self.lan_connection_provider.addItem("e4mc tunnel", "e4mc")
        self.lan_security_label = QLabel()
        self.lan_security_label.setObjectName("CardSubtitle")
        self.lan_security_label.setWordWrap(True)
        self.lan_prepare_status = QLabel("Hosting support has not been prepared for the current selection.")
        self.lan_prepare_status.setObjectName("CardSubtitle")
        self.lan_prepare_status.setWordWrap(True)
        self.lan_prepare_button = set_theme_icon(QPushButton("Prepare hosting support"), "icon.action.download")
        self.lan_agent_log_button = set_theme_icon(QPushButton("View MCW Agent log"), "icon.action.folder")
        self.lan_prepare_button.clicked.connect(self.request_lan_prepare)
        self.lan_agent_log_button.clicked.connect(self.request_lan_agent_log)
        hosting_card.layout.addWidget(QLabel("Authentication policy"))
        hosting_card.layout.addWidget(self.lan_auth_mode)
        hosting_card.layout.addWidget(QLabel("Connection provider"))
        hosting_card.layout.addWidget(self.lan_connection_provider)
        hosting_card.layout.addWidget(self.lan_security_label)
        hosting_card.layout.addWidget(self.lan_prepare_status)
        hosting_card.layout.addWidget(self.lan_prepare_button)
        hosting_card.layout.addWidget(self.lan_agent_log_button)
        multiplayer_section.add_card(hosting_card, span=2)
        self.lan_auth_mode.currentIndexChanged.connect(self._update_lan_help)
        self.lan_connection_provider.currentIndexChanged.connect(self._update_lan_help)
        self._update_lan_help()

        managed_checks_card = CardWidget(
            tr("managed_content.instance.title"),
            tr("managed_content.instance.detail"),
        )
        self.modrinth_failure_label = QLabel(tr("managed_content.modrinth.label"))
        self.modrinth_failure_policy = QComboBox()
        self.curseforge_failure_label = QLabel(tr("managed_content.curseforge.label"))
        self.curseforge_failure_policy = QComboBox()
        self._populate_failure_policy_combo(self.modrinth_failure_policy)
        self._populate_failure_policy_combo(self.curseforge_failure_policy)
        managed_checks_card.layout.addWidget(self.modrinth_failure_label)
        managed_checks_card.layout.addWidget(self.modrinth_failure_policy)
        managed_checks_card.layout.addWidget(self.curseforge_failure_label)
        managed_checks_card.layout.addWidget(self.curseforge_failure_policy)
        multiplayer_section.add_card(managed_checks_card, span=2)

        arguments_card = CardWidget("Custom arguments", "Enter one argument per line.")
        self.jvm_arguments = QTextEdit()
        self.jvm_arguments.setObjectName("ArgumentEditor")
        self.jvm_arguments.setPlaceholderText("JVM arguments")
        self.jvm_arguments.setFixedHeight(90)
        self.game_arguments = QTextEdit()
        self.game_arguments.setObjectName("ArgumentEditor")
        self.game_arguments.setPlaceholderText("Game arguments")
        self.game_arguments.setFixedHeight(90)
        arguments_card.layout.addWidget(QLabel("JVM arguments"))
        arguments_card.layout.addWidget(self.jvm_arguments)
        arguments_card.layout.addWidget(QLabel("Game arguments"))
        arguments_card.layout.addWidget(self.game_arguments)
        advanced_section.add_card(arguments_card, span=2)

        self.save_button = set_theme_icon(QPushButton("Save instance settings"), "icon.action.save")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setMinimumHeight(48)
        self.save_button.clicked.connect(self.request_save)
        self.root_layout.addWidget(self.save_button)
        self.root_layout.addStretch()

    @property
    def physical_memory_mb(self) -> int:
        return self._physical_memory_mb

    @property
    def memory_limit_mb(self) -> int:
        return self._memory_limit_mb

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def loaded_instance_name(self) -> str:
        return self._loaded_instance_name

    def set_instances(self, instances: list, selected_name: str) -> None:
        names = [instance.name for instance in instances]
        preferred = self._loaded_instance_name if self._dirty and self._loaded_instance_name in names else selected_name
        self.instance_combo.blockSignals(True)
        self.instance_combo.clear()
        self.instance_combo.addItems(names)
        if preferred:
            self.instance_combo.setCurrentText(preferred)
        self.instance_combo.blockSignals(False)

    def select_instance(self, name: str) -> None:
        self.instance_combo.blockSignals(True)
        self.instance_combo.setCurrentText(name)
        self.instance_combo.blockSignals(False)

    def revert_instance_selection(self) -> None:
        self.select_instance(self._loaded_instance_name)

    def current_instance_name(self) -> str:
        return self.instance_combo.currentText().strip()

    def set_settings(self, instance_name: str, settings: object | None) -> None:
        self._tracking_suspended = True
        try:
            if settings is None:
                self._loaded_instance_name = ""
                self._clear_form()
            else:
                self._loaded_instance_name = instance_name.strip()
                if instance_name and self.instance_combo.currentText() != instance_name:
                    self.select_instance(instance_name)
                self._apply_form_data({
                    "java_path": str(getattr(settings, "java_path", "") or ""),
                    "min_memory": getattr(settings, "min_memory", 1024),
                    "max_memory": getattr(settings, "max_memory", 2048),
                    "width": int(getattr(settings, "width", 1280)),
                    "height": int(getattr(settings, "height", 720)),
                    "fullscreen": bool(getattr(settings, "fullscreen", False)),
                    "lan_auth_mode": str(getattr(settings, "lan_auth_mode", "microsoft_only") or "microsoft_only"),
                    "lan_connection_provider": str(getattr(settings, "lan_connection_provider", "manual") or "manual"),
                    "modrinth_failure_policy": self._settings_failure_policy(settings, "modrinth"),
                    "curseforge_failure_policy": self._settings_failure_policy(settings, "curseforge"),
                    "jvm_arguments": list(getattr(settings, "jvm_arguments", [])),
                    "game_arguments": list(getattr(settings, "game_arguments", [])),
                })
            self._saved_data = self.form_data()
        finally:
            self._tracking_suspended = False
        self._set_dirty(False)

    def form_data(self) -> dict:
        return {
            "java_path": self.java_path_input.text(),
            "min_memory": self.min_memory_input.value(),
            "max_memory": self.max_memory_input.value(),
            "width": self.window_width.value(),
            "height": self.window_height.value(),
            "fullscreen": self.fullscreen.isChecked(),
            "lan_auth_mode": str(self.lan_auth_mode.currentData() or "microsoft_only"),
            "lan_connection_provider": str(self.lan_connection_provider.currentData() or "manual"),
            "modrinth_failure_policy": str(self.modrinth_failure_policy.currentData() or ManagedContentPolicy.INHERIT),
            "curseforge_failure_policy": str(self.curseforge_failure_policy.currentData() or ManagedContentPolicy.INHERIT),
            "jvm_arguments": self._lines(self.jvm_arguments.toPlainText()),
            "game_arguments": self._lines(self.game_arguments.toPlainText()),
        }

    def request_save(self) -> None:
        self.save_requested.emit(self._loaded_instance_name or self.current_instance_name(), self.form_data())

    def request_lan_prepare(self) -> None:
        instance_name = self._loaded_instance_name or self.current_instance_name()
        self.lan_prepare_requested.emit(
            instance_name,
            str(self.lan_auth_mode.currentData() or "microsoft_only"),
            str(self.lan_connection_provider.currentData() or "manual"),
        )

    def request_lan_agent_log(self) -> None:
        instance_name = self._loaded_instance_name or self.current_instance_name()
        self.lan_agent_log_requested.emit(instance_name)

    def set_lan_prepare_status(self, message: str) -> None:
        self.lan_prepare_status.setText(str(message))

    def discard_changes(self) -> None:
        if not self._saved_data:
            return
        self._tracking_suspended = True
        try:
            self._apply_form_data(self._saved_data)
        finally:
            self._tracking_suspended = False
        self._set_dirty(False)

    def set_busy(self, busy: bool) -> None:
        enabled = not busy
        self.instance_combo.setEnabled(enabled)
        self.lan_auth_mode.setEnabled(enabled)
        self.lan_connection_provider.setEnabled(enabled)
        self.modrinth_failure_policy.setEnabled(enabled)
        self.curseforge_failure_policy.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.lan_prepare_button.setEnabled(enabled)
        self.lan_agent_log_button.setEnabled(enabled)

    def retranslate_dynamic(self) -> None:
        self._update_memory_labels()
        self.unsaved_label.setText(tr("settings.unsaved.banner"))
        self._update_save_button_text()
        self._update_lan_help()
        self.modrinth_failure_label.setText(tr("managed_content.modrinth.label"))
        self.curseforge_failure_label.setText(tr("managed_content.curseforge.label"))
        self._retranslate_failure_policy_combo(self.modrinth_failure_policy)
        self._retranslate_failure_policy_combo(self.curseforge_failure_policy)

    def _connect_dirty_tracking(self) -> None:
        self.java_path_input.textChanged.connect(self._refresh_dirty_state)
        self.min_memory.valueChanged.connect(self._refresh_dirty_state)
        self.max_memory.valueChanged.connect(self._refresh_dirty_state)
        self.min_memory_input.valueChanged.connect(self._refresh_dirty_state)
        self.max_memory_input.valueChanged.connect(self._refresh_dirty_state)
        self.window_width.valueChanged.connect(self._refresh_dirty_state)
        self.window_height.valueChanged.connect(self._refresh_dirty_state)
        self.fullscreen.toggled.connect(self._refresh_dirty_state)
        self.lan_auth_mode.currentIndexChanged.connect(self._refresh_dirty_state)
        self.lan_connection_provider.currentIndexChanged.connect(self._refresh_dirty_state)
        self.modrinth_failure_policy.currentIndexChanged.connect(self._refresh_dirty_state)
        self.curseforge_failure_policy.currentIndexChanged.connect(self._refresh_dirty_state)
        self.jvm_arguments.textChanged.connect(self._refresh_dirty_state)
        self.game_arguments.textChanged.connect(self._refresh_dirty_state)

    def _refresh_dirty_state(self, *_args) -> None:
        if self._tracking_suspended:
            return
        self._set_dirty(bool(self._loaded_instance_name) and self.form_data() != self._saved_data)

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
        label = tr("Save instance settings")
        self.save_button.setText(f"● {label}" if self._dirty else label)

    def _browse_java(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose Java executable", "", "Java executable (java.exe javaw.exe);;All files (*)")
        if path:
            self.java_path_input.setText(path)

    def _clear_form(self) -> None:
        self._apply_form_data({
            "java_path": "",
            "min_memory": MemoryAllocationPolicy.DEFAULT_MIN_MEMORY_MB,
            "max_memory": MemoryAllocationPolicy.DEFAULT_MAX_MEMORY_MB,
            "width": 1280,
            "height": 720,
            "fullscreen": False,
            "lan_auth_mode": "microsoft_only",
            "lan_connection_provider": "manual",
            "modrinth_failure_policy": ManagedContentPolicy.INHERIT,
            "curseforge_failure_policy": ManagedContentPolicy.INHERIT,
            "jvm_arguments": [],
            "game_arguments": [],
        })

    def _apply_form_data(self, data: dict) -> None:
        self.java_path_input.setText(str(data.get("java_path", "") or ""))
        self._apply_memory_values(data.get("min_memory", 1024), data.get("max_memory", 2048))
        self.window_width.setValue(int(data.get("width", 1280)))
        self.window_height.setValue(int(data.get("height", 720)))
        self.fullscreen.setChecked(bool(data.get("fullscreen", False)))
        self._set_combo_data(self.lan_auth_mode, str(data.get("lan_auth_mode", "microsoft_only")))
        self._set_combo_data(self.lan_connection_provider, str(data.get("lan_connection_provider", "manual")))
        self._set_combo_data(self.modrinth_failure_policy, ManagedContentPolicy.normalize_instance(data.get("modrinth_failure_policy")))
        self._set_combo_data(self.curseforge_failure_policy, ManagedContentPolicy.normalize_instance(data.get("curseforge_failure_policy")))
        self._update_lan_help()
        self.jvm_arguments.setPlainText("\n".join(data.get("jvm_arguments", [])))
        self.game_arguments.setPlainText("\n".join(data.get("game_arguments", [])))

    @staticmethod
    def _settings_failure_policy(settings: object, provider: str) -> str:
        value = getattr(settings, f"{provider}_failure_policy", None)
        if value is not None:
            return ManagedContentPolicy.normalize_instance(value)
        legacy = getattr(settings, f"block_launch_on_{provider}_failure", None)
        if legacy is None and provider == "curseforge":
            legacy = getattr(settings, "block_launch_on_modrinth_failure", None)
        if legacy is not None:
            return ManagedContentPolicy.from_legacy_bool(legacy)
        return ManagedContentPolicy.INHERIT

    @staticmethod
    def _populate_failure_policy_combo(combo: QComboBox) -> None:
        combo.clear()
        combo.addItem(tr("managed_content.policy.inherit"), ManagedContentPolicy.INHERIT)
        combo.addItem(tr("managed_content.policy.block"), ManagedContentPolicy.BLOCK)
        combo.addItem(tr("managed_content.policy.allow"), ManagedContentPolicy.ALLOW)

    @staticmethod
    def _retranslate_failure_policy_combo(combo: QComboBox) -> None:
        current = str(combo.currentData() or ManagedContentPolicy.INHERIT)
        with QSignalBlocker(combo):
            InstanceSettingsPage._populate_failure_policy_combo(combo)
            index = combo.findData(current)
            combo.setCurrentIndex(max(0, index))

    def _apply_memory_values(self, min_memory_mb: object, max_memory_mb: object) -> None:
        minimum, maximum = MemoryAllocationPolicy.normalize(min_memory_mb, max_memory_mb, self._memory_limit_mb)
        self._set_memory_controls(minimum, maximum)

    def _on_max_memory_slider_changed(self, maximum: int) -> None:
        snapped = MemoryAllocationPolicy.snap_mb(maximum, self._memory_limit_mb)
        minimum = min(self.min_memory_input.value(), snapped)
        self._set_memory_controls(minimum, snapped)

    def _on_min_memory_slider_changed(self, minimum: int) -> None:
        snapped = MemoryAllocationPolicy.snap_mb(minimum, self.max_memory_input.value())
        self._set_memory_controls(snapped, self.max_memory_input.value())

    def _on_max_memory_input_changed(self, maximum: int) -> None:
        maximum = min(max(int(maximum), MemoryAllocationPolicy.MIN_MEMORY_MB), self._memory_limit_mb)
        minimum = min(self.min_memory_input.value(), maximum)
        self._set_memory_controls(minimum, maximum)

    def _on_min_memory_input_changed(self, minimum: int) -> None:
        maximum = self.max_memory_input.value()
        minimum = min(max(int(minimum), MemoryAllocationPolicy.MIN_MEMORY_MB), maximum)
        self._set_memory_controls(minimum, maximum)

    def _set_memory_controls(self, minimum: int, maximum: int) -> None:
        minimum, maximum = MemoryAllocationPolicy.normalize(minimum, maximum, self._memory_limit_mb)
        blockers = [QSignalBlocker(widget) for widget in (self.min_memory, self.max_memory, self.min_memory_input, self.max_memory_input)]
        self.max_memory.setValue(maximum)
        self.max_memory_input.setValue(maximum)
        self.min_memory.setMaximum(maximum)
        self.min_memory_input.setMaximum(maximum)
        self.min_memory.setValue(minimum)
        self.min_memory_input.setValue(minimum)
        del blockers
        self._update_memory_labels()
        self._refresh_dirty_state()

    def _update_memory_labels(self) -> None:
        physical = MemoryAllocationPolicy.format_mb(self._physical_memory_mb)
        limit = MemoryAllocationPolicy.format_mb(self._memory_limit_mb)
        if self._memory_detection_failed:
            self.memory_info_label.setText(tr("Physical memory could not be detected. Java maximum uses the safe limit: {limit}.", limit=limit))
        else:
            self.memory_info_label.setText(tr("Detected physical memory: {memory}. Java maximum is limited to {limit}.", memory=physical, limit=limit))
        self.min_memory_value.setText(MemoryAllocationPolicy.format_mb(self.min_memory_input.value()))
        self.max_memory_value.setText(MemoryAllocationPolicy.format_mb(self.max_memory_input.value()))

    @staticmethod
    def _create_memory_input() -> QSpinBox:
        spin_box = QSpinBox()
        spin_box.setMinimum(MemoryAllocationPolicy.MIN_MEMORY_MB)
        spin_box.setSingleStep(MemoryAllocationPolicy.SLIDER_STEP_MB)
        spin_box.setSuffix(" MB")
        spin_box.setAlignment(Qt.AlignmentFlag.AlignLeft)
        spin_box.setKeyboardTracking(False)
        spin_box.setAccelerated(True)
        spin_box.setMinimumWidth(132)
        return spin_box

    @staticmethod
    def _create_memory_slider() -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(MemoryAllocationPolicy.MIN_MEMORY_MB)
        slider.setSingleStep(MemoryAllocationPolicy.SLIDER_STEP_MB)
        slider.setPageStep(1024)
        slider.setTickInterval(1024)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setMinimumHeight(34)
        return slider


    def _update_lan_help(self, *_args) -> None:
        auth_mode = str(self.lan_auth_mode.currentData() or "microsoft_only")
        provider = str(self.lan_connection_provider.currentData() or "manual")
        if auth_mode == "private_offline":
            auth_text = tr("lan.hosting.private_offline.warning")
        else:
            auth_text = tr("lan.hosting.microsoft_only.help")
        if provider == "e4mc":
            provider_text = tr("lan.hosting.connection.e4mc.help")
        else:
            provider_text = tr("lan.hosting.connection.manual.help")
        self.lan_security_label.setText(f"{auth_text}\n\n{provider_text}")

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(str(value))
        combo.setCurrentIndex(index if index >= 0 else 0)

    @staticmethod
    def _lines(text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]
