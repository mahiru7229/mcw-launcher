from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.config.managed_content_policy import ManagedContentPolicy
from src.core.instance.settings_manager import SettingsManager
from src.core.language.language_manager import tr
from src.core.system.memory import MemoryAllocationPolicy, SystemMemory
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.instance.settings import InstanceSettings


class InstanceSettingsEditorDialog(QDialog):
    def __init__(
        self,
        settings: dict | InstanceSettings | None,
        parent=None,
        *,
        title: str = "",
        total_memory_mb: int | None = None,
    ) -> None:
        super().__init__(parent)
        detected_memory = int(total_memory_mb) if total_memory_mb is not None else SystemMemory.total_physical_memory_mb()
        self._memory_limit_mb = MemoryAllocationPolicy.physical_limit_mb(detected_memory)
        self._build_ui()
        self._apply_settings(settings)
        self.setWindowTitle(title or tr("instance_defaults.editor.title"))

    @property
    def settings_data(self) -> dict:
        return SettingsManager.to_dict(
            InstanceSettings(
                java_path=self.java_path_input.text().strip(),
                min_memory=self.min_memory.value(),
                max_memory=self.max_memory.value(),
                jvm_arguments=self._lines(self.jvm_arguments.toPlainText()),
                game_arguments=self._lines(self.game_arguments.toPlainText()),
                offline_multiplayer_enabled=False,
                lan_auth_mode=str(self.lan_auth_mode.currentData() or "microsoft_only"),
                lan_connection_provider=str(self.lan_connection_provider.currentData() or "manual"),
                modrinth_failure_policy=str(self.modrinth_failure_policy.currentData() or ManagedContentPolicy.INHERIT),
                curseforge_failure_policy=str(self.curseforge_failure_policy.currentData() or ManagedContentPolicy.INHERIT),
                forge_preflight_failure_policy=str(self.forge_preflight_failure_policy.currentData() or ManagedContentPolicy.INHERIT),
                width=self.window_width.value(),
                height=self.window_height.value(),
                fullscreen=self.fullscreen.isChecked(),
            )
        )

    @staticmethod
    def summary(settings: dict | InstanceSettings | None) -> str:
        normalized = SettingsManager.from_dict(settings)
        java = str(normalized.java_path or "").strip() or tr("instance_defaults.java.auto")
        fullscreen = tr("instance_defaults.window.fullscreen_suffix") if normalized.fullscreen else ""
        return tr(
            "instance_defaults.summary",
            minimum=MemoryAllocationPolicy.format_mb(normalized.min_memory),
            maximum=MemoryAllocationPolicy.format_mb(normalized.max_memory),
            java=java,
            width=normalized.width,
            height=normalized.height,
            fullscreen=fullscreen,
        )

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 760, 680, 620, 520)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.description_label = QLabel(tr("instance_defaults.editor.description"))
        self.description_label.setObjectName("MutedLabel")
        self.description_label.setWordWrap(True)
        root.addWidget(self.description_label)

        tabs = QTabWidget()
        tabs.addTab(self._runtime_tab(), tr("instance_defaults.tab.runtime"))
        tabs.addTab(self._policies_tab(), tr("instance_defaults.tab.policies"))
        tabs.addTab(self._arguments_tab(), tr("instance_defaults.tab.arguments"))
        root.addWidget(tabs, 1)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if self.cancel_button is not None:
            self.cancel_button.setText(tr("common.cancel"))
        self.save_button = self.buttons.addButton(tr("instance_defaults.editor.apply"), QDialogButtonBox.ButtonRole.AcceptRole)
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

    def _runtime_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(12)

        java_group = QGroupBox(tr("instance_defaults.group.java"))
        java_form = QFormLayout(java_group)
        java_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        java_row = QWidget()
        java_row_layout = QHBoxLayout(java_row)
        java_row_layout.setContentsMargins(0, 0, 0, 0)
        java_row_layout.setSpacing(8)
        self.java_path_input = QLineEdit()
        self.java_path_input.setPlaceholderText(tr("instance_defaults.java.placeholder"))
        browse_button = QPushButton(tr("instance_defaults.java.browse"))
        browse_button.clicked.connect(self._browse_java)
        java_row_layout.addWidget(self.java_path_input, 1)
        java_row_layout.addWidget(browse_button)
        java_form.addRow(tr("instance_defaults.java.path"), java_row)

        self.min_memory = QSpinBox()
        self.max_memory = QSpinBox()
        for field in (self.min_memory, self.max_memory):
            field.setRange(MemoryAllocationPolicy.MIN_MEMORY_MB, self._memory_limit_mb)
            field.setSingleStep(MemoryAllocationPolicy.SLIDER_STEP_MB)
            field.setSuffix(" MB")
        self.min_memory.valueChanged.connect(self._minimum_changed)
        self.max_memory.valueChanged.connect(self._maximum_changed)
        java_form.addRow(tr("instance_defaults.memory.minimum"), self.min_memory)
        java_form.addRow(tr("instance_defaults.memory.maximum"), self.max_memory)
        memory_limit = QLabel(
            tr(
                "instance_defaults.memory.limit",
                limit=MemoryAllocationPolicy.format_mb(self._memory_limit_mb),
            )
        )
        memory_limit.setObjectName("MutedLabel")
        memory_limit.setWordWrap(True)
        java_form.addRow("", memory_limit)
        layout.addWidget(java_group)

        window_group = QGroupBox(tr("instance_defaults.group.window"))
        window_form = QFormLayout(window_group)
        self.window_width = QSpinBox()
        self.window_height = QSpinBox()
        for field in (self.window_width, self.window_height):
            field.setRange(320, 7680)
        self.fullscreen = QCheckBox(tr("instance_defaults.window.fullscreen"))
        window_form.addRow(tr("instance_defaults.window.width"), self.window_width)
        window_form.addRow(tr("instance_defaults.window.height"), self.window_height)
        window_form.addRow("", self.fullscreen)
        layout.addWidget(window_group)
        layout.addStretch(1)
        return tab

    def _policies_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(12)

        lan_group = QGroupBox(tr("instance_defaults.group.lan"))
        lan_form = QFormLayout(lan_group)
        self.lan_auth_mode = QComboBox()
        self.lan_auth_mode.addItem(tr("instance_defaults.lan.microsoft_only"), "microsoft_only")
        self.lan_auth_mode.addItem(tr("instance_defaults.lan.private_offline"), "private_offline")
        self.lan_connection_provider = QComboBox()
        self.lan_connection_provider.addItem(tr("instance_defaults.lan.manual"), "manual")
        self.lan_connection_provider.addItem(tr("instance_defaults.lan.e4mc"), "e4mc")
        lan_form.addRow(tr("instance_defaults.lan.authentication"), self.lan_auth_mode)
        lan_form.addRow(tr("instance_defaults.lan.connection"), self.lan_connection_provider)
        layout.addWidget(lan_group)

        managed_group = QGroupBox(tr("instance_defaults.group.managed"))
        managed_form = QFormLayout(managed_group)
        self.modrinth_failure_policy = self._failure_policy_combo()
        self.curseforge_failure_policy = self._failure_policy_combo()
        self.forge_preflight_failure_policy = self._failure_policy_combo()
        managed_form.addRow(tr("instance_defaults.policy.modrinth"), self.modrinth_failure_policy)
        managed_form.addRow(tr("instance_defaults.policy.curseforge"), self.curseforge_failure_policy)
        managed_form.addRow(tr("instance_defaults.policy.forge"), self.forge_preflight_failure_policy)
        layout.addWidget(managed_group)
        layout.addStretch(1)
        return tab

    def _arguments_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(8)
        hint = QLabel(tr("instance_defaults.arguments.hint"))
        hint.setObjectName("MutedLabel")
        hint.setWordWrap(True)
        self.jvm_arguments = QTextEdit()
        self.jvm_arguments.setPlaceholderText(tr("instance_defaults.arguments.jvm"))
        self.game_arguments = QTextEdit()
        self.game_arguments.setPlaceholderText(tr("instance_defaults.arguments.game"))
        layout.addWidget(hint)
        layout.addWidget(QLabel(tr("instance_defaults.arguments.jvm")))
        layout.addWidget(self.jvm_arguments, 1)
        layout.addWidget(QLabel(tr("instance_defaults.arguments.game")))
        layout.addWidget(self.game_arguments, 1)
        return tab

    def _apply_settings(self, data: dict | InstanceSettings | None) -> None:
        settings = SettingsManager.from_dict(data)
        self.java_path_input.setText(str(settings.java_path or ""))
        minimum, maximum = MemoryAllocationPolicy.normalize(
            settings.min_memory,
            settings.max_memory,
            self._memory_limit_mb,
        )
        self.max_memory.setValue(maximum)
        self.min_memory.setMaximum(maximum)
        self.min_memory.setValue(minimum)
        self.window_width.setValue(settings.width)
        self.window_height.setValue(settings.height)
        self.fullscreen.setChecked(settings.fullscreen)
        self._set_combo(self.lan_auth_mode, settings.lan_auth_mode)
        self._set_combo(self.lan_connection_provider, settings.lan_connection_provider)
        self._set_combo(self.modrinth_failure_policy, settings.modrinth_failure_policy)
        self._set_combo(self.curseforge_failure_policy, settings.curseforge_failure_policy)
        self._set_combo(self.forge_preflight_failure_policy, settings.forge_preflight_failure_policy)
        self.jvm_arguments.setPlainText("\n".join(settings.jvm_arguments))
        self.game_arguments.setPlainText("\n".join(settings.game_arguments))

    def _browse_java(self) -> None:
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            tr("instance_defaults.java.choose"),
            self.java_path_input.text().strip(),
            tr("instance_defaults.java.filter"),
        )
        if path:
            self.java_path_input.setText(path)

    def _minimum_changed(self, minimum: int) -> None:
        if minimum > self.max_memory.value():
            self.max_memory.setValue(minimum)

    def _maximum_changed(self, maximum: int) -> None:
        self.min_memory.setMaximum(maximum)
        if self.min_memory.value() > maximum:
            self.min_memory.setValue(maximum)

    @staticmethod
    def _failure_policy_combo() -> QComboBox:
        combo = QComboBox()
        combo.addItem(tr("managed_content.policy.inherit"), ManagedContentPolicy.INHERIT)
        combo.addItem(tr("managed_content.policy.block"), ManagedContentPolicy.BLOCK)
        combo.addItem(tr("managed_content.policy.allow"), ManagedContentPolicy.ALLOW)
        return combo

    @staticmethod
    def _set_combo(combo: QComboBox, value: object) -> None:
        index = combo.findData(str(value))
        combo.setCurrentIndex(max(0, index))

    @staticmethod
    def _lines(value: str) -> list[str]:
        return [line.strip() for line in str(value).splitlines() if line.strip()]
