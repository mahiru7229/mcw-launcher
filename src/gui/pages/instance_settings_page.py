from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QLineEdit, QPushButton, QSlider, QSpinBox, QTextEdit

from src.core.language.language_manager import tr
from src.core.system.memory import MemoryAllocationPolicy, SystemMemory
from src.gui.pages.base_page import BasePage
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget


class InstanceSettingsPage(BasePage):
    load_requested = Signal(str)
    save_requested = Signal(str, dict)
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

        selector_card = CardWidget("Target instance")
        self.instance_combo = QComboBox()
        self.instance_combo.currentTextChanged.connect(self.load_requested.emit)
        reload_button = set_theme_icon(QPushButton("Reload settings"), "icon.action.refresh")
        reload_button.clicked.connect(lambda: self.load_requested.emit(self.current_instance_name()))
        selector_card.layout.addWidget(self.instance_combo)
        selector_card.layout.addWidget(reload_button)
        self.root_layout.addWidget(selector_card)

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
        self.root_layout.addWidget(java_card)
        self._apply_memory_values(MemoryAllocationPolicy.DEFAULT_MIN_MEMORY_MB, MemoryAllocationPolicy.DEFAULT_MAX_MEMORY_MB)

        window_card = CardWidget("Game window")
        window_grid = QGridLayout()
        self.window_width = QSpinBox()
        self.window_height = QSpinBox()
        for spin_box in (self.window_width, self.window_height):
            spin_box.setRange(320, 7680)
        self.fullscreen = QCheckBox("Launch in fullscreen")
        self.offline_multiplayer = QCheckBox("Enable offline multiplayer workaround")
        window_grid.addWidget(QLabel("Width"), 0, 0)
        window_grid.addWidget(self.window_width, 1, 0)
        window_grid.addWidget(QLabel("Height"), 0, 1)
        window_grid.addWidget(self.window_height, 1, 1)
        window_card.layout.addLayout(window_grid)
        window_card.layout.addWidget(self.fullscreen)
        window_card.layout.addWidget(self.offline_multiplayer)
        self.root_layout.addWidget(window_card)

        modrinth_card = CardWidget(
            "Modrinth downloads",
            "Recommended: keep this enabled. Turn it off only when you plan to download failed modpack files manually.",
        )
        self.block_modrinth_failure = QCheckBox("Stop launch when required Modrinth files are missing")
        self.block_modrinth_failure.setChecked(True)
        self.block_modrinth_failure.setToolTip(
            "This option belongs to the selected instance. Disable it to let Minecraft launch after three failed download rounds, then place the missing files manually in the paths shown by the launcher."
        )
        modrinth_card.layout.addWidget(self.block_modrinth_failure)
        self.root_layout.addWidget(modrinth_card)

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
        self.root_layout.addWidget(arguments_card)

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
                    "offline_multiplayer_enabled": bool(getattr(settings, "offline_multiplayer_enabled", False)),
                    "block_launch_on_modrinth_failure": bool(getattr(settings, "block_launch_on_modrinth_failure", True)),
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
            "offline_multiplayer_enabled": self.offline_multiplayer.isChecked(),
            "block_launch_on_modrinth_failure": self.block_modrinth_failure.isChecked(),
            "jvm_arguments": self._lines(self.jvm_arguments.toPlainText()),
            "game_arguments": self._lines(self.game_arguments.toPlainText()),
        }

    def request_save(self) -> None:
        self.save_requested.emit(self._loaded_instance_name or self.current_instance_name(), self.form_data())

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
        self.setEnabled(not busy)

    def retranslate_dynamic(self) -> None:
        self._update_memory_labels()
        self.unsaved_label.setText(tr("settings.unsaved.banner"))
        self._update_save_button_text()

    def _connect_dirty_tracking(self) -> None:
        self.java_path_input.textChanged.connect(self._refresh_dirty_state)
        self.min_memory.valueChanged.connect(self._refresh_dirty_state)
        self.max_memory.valueChanged.connect(self._refresh_dirty_state)
        self.min_memory_input.valueChanged.connect(self._refresh_dirty_state)
        self.max_memory_input.valueChanged.connect(self._refresh_dirty_state)
        self.window_width.valueChanged.connect(self._refresh_dirty_state)
        self.window_height.valueChanged.connect(self._refresh_dirty_state)
        self.fullscreen.toggled.connect(self._refresh_dirty_state)
        self.offline_multiplayer.toggled.connect(self._refresh_dirty_state)
        self.block_modrinth_failure.toggled.connect(self._refresh_dirty_state)
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
            "offline_multiplayer_enabled": False,
            "block_launch_on_modrinth_failure": True,
            "jvm_arguments": [],
            "game_arguments": [],
        })

    def _apply_form_data(self, data: dict) -> None:
        self.java_path_input.setText(str(data.get("java_path", "") or ""))
        self._apply_memory_values(data.get("min_memory", 1024), data.get("max_memory", 2048))
        self.window_width.setValue(int(data.get("width", 1280)))
        self.window_height.setValue(int(data.get("height", 720)))
        self.fullscreen.setChecked(bool(data.get("fullscreen", False)))
        self.offline_multiplayer.setChecked(bool(data.get("offline_multiplayer_enabled", False)))
        self.block_modrinth_failure.setChecked(bool(data.get("block_launch_on_modrinth_failure", True)))
        self.jvm_arguments.setPlainText("\n".join(data.get("jvm_arguments", [])))
        self.game_arguments.setPlainText("\n".join(data.get("game_arguments", [])))

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

    @staticmethod
    def _lines(text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]
