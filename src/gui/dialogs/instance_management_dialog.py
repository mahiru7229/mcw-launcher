from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.language.language_manager import tr
from src.gui.localization import retranslate_widget_tree
from src.gui.theme.runtime import set_theme_icon
from src.gui.window_sizing import resize_dialog_to_screen


class AdvancedInstanceManagerDialog(QDialog):
    def __init__(self, advanced_page: QWidget, parent=None) -> None:
        super().__init__(parent)
        self._advanced_page = advanced_page
        self._instance_name = ""
        self.setModal(False)
        resize_dialog_to_screen(self, 940, 720, 620, 480, lock_maximum=False)
        self.setMinimumSize(520, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 12)
        root.setSpacing(8)
        root.addWidget(self._advanced_page, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        if self.close_button is not None:
            self.close_button.setText(tr("common.close"))
        buttons.rejected.connect(self.close)
        root.addWidget(buttons)
        self.retranslate_dynamic()

    def set_instance_name(self, name: str) -> None:
        self._instance_name = str(name or "")
        self.retranslate_dynamic()

    def retranslate_dynamic(self) -> None:
        retranslate_widget_tree(self)
        self._advanced_page.retranslate_dynamic()
        if self.close_button is not None:
            self.close_button.setText(tr("common.close"))
        self.setWindowTitle(tr("workspace.advanced.title_for", name=self._instance_name) if self._instance_name else tr("workspace.advanced.title"))


class InstanceManagementDialog(QDialog):
    launch_requested = Signal()
    open_folder_requested = Signal(str)
    manage_mods_requested = Signal(str)
    instance_settings_requested = Signal(str)
    repair_requested = Signal(str)
    repair_loader_requested = Signal(str)
    create_backup_requested = Signal(str, str)
    restore_backup_requested = Signal(str)
    open_backups_requested = Signal(str)
    open_logs_requested = Signal(str)
    export_diagnostics_requested = Signal(str)
    advanced_requested = Signal(str)
    runtime_scan_requested = Signal()
    runtime_install_requested = Signal(int)
    runtime_apply_requested = Signal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setModal(False)
        self._instance: object | None = None
        self._instance_name = ""
        self._runtime_profile: object | None = None
        self._java_installations: list[object] = []
        self._nav_items: list[QListWidgetItem] = []
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 900, 620, 720, 500)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 14)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("InsetPanel")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(4)
        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        self.summary_label = QLabel()
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.summary_label)
        root.addWidget(header)

        body = QHBoxLayout()
        body.setSpacing(12)
        self.navigation = QListWidget()
        self.navigation.setObjectName("InstanceEditorNavigation")
        self.navigation.setFixedWidth(210)
        self.navigation.setSpacing(2)
        self.navigation.currentRowChanged.connect(self._select_page)
        body.addWidget(self.navigation)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._overview_page())
        self.stack.addWidget(self._version_page())
        self.stack.addWidget(self._runtime_page())
        self.stack.addWidget(self._mods_page())
        self.stack.addWidget(self._settings_page())
        self.stack.addWidget(self._maintenance_page())
        self.stack.addWidget(self._diagnostics_page())
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = self.buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_button is not None:
            close_button.setText(tr("common.close"))
        self.buttons.rejected.connect(self.close)
        root.addWidget(self.buttons)

        for _index in range(self.stack.count()):
            self._nav_items.append(QListWidgetItem())
            self.navigation.addItem(self._nav_items[-1])
        self.navigation.setCurrentRow(0)

    @staticmethod
    def _page() -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        return page, layout

    def _overview_page(self) -> QWidget:
        page, layout = self._page()
        self.overview_title = QLabel()
        self.overview_title.setObjectName("SectionTitle")
        self.overview_detail = QLabel()
        self.overview_detail.setObjectName("MutedLabel")
        self.overview_detail.setWordWrap(True)
        self.overview_library_detail = QLabel()
        self.overview_library_detail.setObjectName("ValueLabel")
        self.overview_library_detail.setWordWrap(True)
        self.launch_button = set_theme_icon(QPushButton(), "icon.action.launch")
        self.launch_button.setObjectName("PrimaryButton")
        self.open_folder_button = set_theme_icon(QPushButton(), "icon.action.folder")
        self.launch_button.clicked.connect(lambda: self._emit_and_hide(self.launch_requested))
        self.open_folder_button.clicked.connect(lambda: self.open_folder_requested.emit(self._instance_name))
        layout.addWidget(self.overview_title)
        layout.addWidget(self.overview_detail)
        layout.addWidget(self.overview_library_detail)
        layout.addSpacing(6)
        layout.addWidget(self.launch_button)
        layout.addWidget(self.open_folder_button)
        layout.addStretch(1)
        return page

    def _version_page(self) -> QWidget:
        page, layout = self._page()
        self.version_title = QLabel()
        self.version_title.setObjectName("SectionTitle")
        self.version_detail = QLabel()
        self.version_detail.setObjectName("MutedLabel")
        self.version_detail.setWordWrap(True)
        component_frame = QFrame()
        component_frame.setObjectName("InsetPanel")
        component_form = QFormLayout(component_frame)
        component_form.setContentsMargins(14, 12, 14, 12)
        self.minecraft_component_value = QLabel()
        self.loader_component_value = QLabel()
        self.java_component_value = QLabel()
        for label in (self.minecraft_component_value, self.loader_component_value, self.java_component_value):
            label.setObjectName("ValueLabel")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.minecraft_component_label = QLabel()
        self.loader_component_label = QLabel()
        self.java_component_label = QLabel()
        component_form.addRow(self.minecraft_component_label, self.minecraft_component_value)
        component_form.addRow(self.loader_component_label, self.loader_component_value)
        component_form.addRow(self.java_component_label, self.java_component_value)
        self.version_summary = QLabel()
        self.version_summary.setObjectName("MutedLabel")
        self.version_summary.setWordWrap(True)
        self.advanced_button = set_theme_icon(QPushButton(), "icon.action.edit")
        self.advanced_button.setObjectName("PrimaryButton")
        self.repair_loader_button = set_theme_icon(QPushButton(), "icon.action.repair")
        self.advanced_button.clicked.connect(lambda: self._emit_and_hide(self.advanced_requested, self._instance_name))
        self.repair_loader_button.clicked.connect(lambda: self.repair_loader_requested.emit(self._instance_name))
        layout.addWidget(self.version_title)
        layout.addWidget(self.version_detail)
        layout.addWidget(component_frame)
        layout.addWidget(self.version_summary)
        layout.addWidget(self.advanced_button)
        layout.addWidget(self.repair_loader_button)
        layout.addStretch(1)
        return page

    def _runtime_page(self) -> QWidget:
        page, layout = self._page()
        self.runtime_title = QLabel()
        self.runtime_title.setObjectName("SectionTitle")
        self.runtime_detail = QLabel()
        self.runtime_detail.setObjectName("MutedLabel")
        self.runtime_detail.setWordWrap(True)
        self.runtime_required_label = QLabel()
        self.runtime_required_label.setObjectName("ValueLabel")
        self.runtime_current_label = QLabel()
        self.runtime_current_label.setObjectName("MutedLabel")
        self.runtime_current_label.setWordWrap(True)
        self.runtime_java_combo = QComboBox()
        self.runtime_java_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.runtime_scan_button = set_theme_icon(QPushButton(), "icon.action.refresh")
        self.runtime_install_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.runtime_apply_button = set_theme_icon(QPushButton(), "icon.action.save")
        self.runtime_apply_button.setObjectName("PrimaryButton")
        self.runtime_scan_button.clicked.connect(self.runtime_scan_requested.emit)
        self.runtime_install_button.clicked.connect(self._request_runtime_install)
        self.runtime_apply_button.clicked.connect(self._request_runtime_apply)
        layout.addWidget(self.runtime_title)
        layout.addWidget(self.runtime_detail)
        layout.addWidget(self.runtime_required_label)
        layout.addWidget(self.runtime_current_label)
        layout.addWidget(self.runtime_java_combo)
        layout.addWidget(self.runtime_scan_button)
        layout.addWidget(self.runtime_install_button)
        layout.addWidget(self.runtime_apply_button)
        layout.addStretch(1)
        return page

    def _mods_page(self) -> QWidget:
        page, layout = self._page()
        self.mods_title = QLabel()
        self.mods_title.setObjectName("SectionTitle")
        self.mods_detail = QLabel()
        self.mods_detail.setObjectName("MutedLabel")
        self.mods_detail.setWordWrap(True)
        self.manage_mods_button = set_theme_icon(QPushButton(), "icon.action.mods")
        self.manage_mods_button.setObjectName("PrimaryButton")
        self.manage_mods_button.clicked.connect(lambda: self._emit_and_hide(self.manage_mods_requested, self._instance_name))
        layout.addWidget(self.mods_title)
        layout.addWidget(self.mods_detail)
        layout.addWidget(self.manage_mods_button)
        layout.addStretch(1)
        return page

    def _settings_page(self) -> QWidget:
        page, layout = self._page()
        self.settings_title = QLabel()
        self.settings_title.setObjectName("SectionTitle")
        self.settings_detail = QLabel()
        self.settings_detail.setObjectName("MutedLabel")
        self.settings_detail.setWordWrap(True)
        self.settings_button = set_theme_icon(QPushButton(), "icon.action.settings")
        self.settings_button.setObjectName("PrimaryButton")
        self.settings_button.clicked.connect(lambda: self._emit_and_hide(self.instance_settings_requested, self._instance_name))
        layout.addWidget(self.settings_title)
        layout.addWidget(self.settings_detail)
        layout.addWidget(self.settings_button)
        layout.addStretch(1)
        return page

    def _maintenance_page(self) -> QWidget:
        page, layout = self._page()
        self.maintenance_title = QLabel()
        self.maintenance_title.setObjectName("SectionTitle")
        self.maintenance_detail = QLabel()
        self.maintenance_detail.setObjectName("MutedLabel")
        self.maintenance_detail.setWordWrap(True)
        self.repair_button = set_theme_icon(QPushButton(), "icon.action.repair")
        self.backup_button = set_theme_icon(QPushButton(), "icon.action.backup")
        self.world_backup_button = set_theme_icon(QPushButton(), "icon.action.backup")
        self.restore_button = set_theme_icon(QPushButton(), "icon.action.restore")
        self.open_backups_button = set_theme_icon(QPushButton(), "icon.action.folder")
        self.repair_button.clicked.connect(lambda: self._emit_and_hide(self.repair_requested, self._instance_name))
        self.backup_button.clicked.connect(lambda: self.create_backup_requested.emit(self._instance_name, "full"))
        self.world_backup_button.clicked.connect(lambda: self.create_backup_requested.emit(self._instance_name, "worlds"))
        self.restore_button.clicked.connect(lambda: self.restore_backup_requested.emit(self._instance_name))
        self.open_backups_button.clicked.connect(lambda: self.open_backups_requested.emit(self._instance_name))
        layout.addWidget(self.maintenance_title)
        layout.addWidget(self.maintenance_detail)
        layout.addWidget(self.repair_button)
        layout.addWidget(self.backup_button)
        layout.addWidget(self.world_backup_button)
        layout.addWidget(self.restore_button)
        layout.addWidget(self.open_backups_button)
        layout.addStretch(1)
        return page

    def _diagnostics_page(self) -> QWidget:
        page, layout = self._page()
        self.diagnostics_title = QLabel()
        self.diagnostics_title.setObjectName("SectionTitle")
        self.diagnostics_detail = QLabel()
        self.diagnostics_detail.setObjectName("MutedLabel")
        self.diagnostics_detail.setWordWrap(True)
        self.open_logs_button = set_theme_icon(QPushButton(), "icon.action.folder")
        self.export_diagnostics_button = set_theme_icon(QPushButton(), "icon.action.export")
        self.open_logs_button.clicked.connect(lambda: self.open_logs_requested.emit(self._instance_name))
        self.export_diagnostics_button.clicked.connect(lambda: self.export_diagnostics_requested.emit(self._instance_name))
        layout.addWidget(self.diagnostics_title)
        layout.addWidget(self.diagnostics_detail)
        layout.addWidget(self.open_logs_button)
        layout.addWidget(self.export_diagnostics_button)
        layout.addStretch(1)
        return page

    def _emit_and_hide(self, signal, *args) -> None:
        self.hide()
        signal.emit(*args)

    def _select_page(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)

    def _request_runtime_install(self) -> None:
        profile = self._runtime_profile
        if profile is None:
            return
        self.runtime_install_requested.emit(int(getattr(profile, "managed_java_major", 17) or 17))

    def _request_runtime_apply(self) -> None:
        if not self._instance_name:
            return
        self.runtime_apply_requested.emit(self._instance_name, str(self.runtime_java_combo.currentData() or ""))

    def set_instance(self, instance: object | None) -> None:
        previous_name = self._instance_name
        self._instance = instance
        self._instance_name = str(getattr(instance, "name", "")) if instance is not None else ""
        if previous_name != self._instance_name:
            self._runtime_profile = None
        enabled = bool(self._instance_name)
        for button in (
            self.launch_button,
            self.open_folder_button,
            self.advanced_button,
            self.settings_button,
            self.repair_button,
            self.backup_button,
            self.world_backup_button,
            self.restore_button,
            self.open_backups_button,
            self.runtime_scan_button,
            self.runtime_apply_button,
        ):
            button.setEnabled(enabled)

        loader_name = "vanilla"
        loader_version = "-1"
        version_id = "-"
        instance_dir = "-"
        if instance is not None:
            loader = tuple(getattr(instance, "mod_loader", ("vanilla", "-1")) or ("vanilla", "-1"))
            loader_name = str(loader[0] if loader else "vanilla").lower()
            loader_version = str(loader[1] if len(loader) > 1 else "-1")
            version_id = str(getattr(instance, "version_id", "-"))
            instance_dir = str(Path(getattr(instance, "instance_dir", "-")))
        loader_text = loader_name.title() if loader_version in {"", "-1"} else f"{loader_name.title()} {loader_version}"
        is_modded = loader_name in {"fabric", "quilt", "forge", "neoforge"}
        has_loader_diagnostics = loader_name in {"quilt", "forge", "neoforge"}
        self.manage_mods_button.setEnabled(enabled and is_modded)
        self.repair_loader_button.setEnabled(enabled and is_modded)
        self.open_logs_button.setEnabled(enabled and loader_name in {"forge", "neoforge"})
        self.export_diagnostics_button.setEnabled(enabled and has_loader_diagnostics)

        self.setWindowTitle(tr("workspace.editor.title_for", name=self._instance_name) if enabled else tr("workspace.editor.title"))
        self.title_label.setText(self._instance_name or tr("workspace.no_selection"))
        self.summary_label.setText(
            tr("workspace.editor.summary", version=version_id, loader=loader_text, path=instance_dir)
            if enabled
            else tr("workspace.editor.no_selection")
        )
        self.overview_detail.setText(tr("workspace.editor.overview_detail", version=version_id, loader=loader_text))
        if instance is None:
            self.overview_library_detail.setText("")
        else:
            group = str(getattr(instance, "group", "") or "").strip() or tr("workspace.library.ungrouped")
            tags = ", ".join(str(tag) for tag in tuple(getattr(instance, "tags", ()) or ())) or tr("workspace.library.no_tags")
            favorite = tr("workspace.library.favorite_yes") if bool(getattr(instance, "favorite", False)) else tr("workspace.library.favorite_no")
            self.overview_library_detail.setText(tr("workspace.editor.library_summary", favorite=favorite, group=group, tags=tags))
        self.version_summary.setText(tr("workspace.editor.version_summary", version=version_id, loader=loader_text))
        self.minecraft_component_value.setText(version_id)
        self.loader_component_value.setText(loader_text)
        self._render_runtime()

    def set_runtime_profile(self, profile: object | None) -> None:
        if profile is not None and str(getattr(profile, "instance_name", "")) != self._instance_name:
            return
        self._runtime_profile = profile
        self._render_runtime()

    def set_java_installations(self, installations: list[object]) -> None:
        self._java_installations = list(installations)
        self._populate_runtime_java_combo()

    def _render_runtime(self) -> None:
        profile = self._runtime_profile
        if profile is None:
            self.java_component_value.setText(tr("common.unknown"))
            self.runtime_required_label.setText(tr("workspace.editor.runtime.unavailable"))
            self.runtime_current_label.setText("")
            self.runtime_install_button.setEnabled(False)
            self._populate_runtime_java_combo()
            return

        required = int(getattr(profile, "required_java_major", 8) or 8)
        managed = int(getattr(profile, "managed_java_major", required) or required)
        automatic = bool(getattr(profile, "java_automatic", True))
        configured = str(getattr(profile, "configured_java_path", "") or "")
        self.java_component_value.setText(tr("workspace.editor.component.java_value", major=required))
        self.runtime_required_label.setText(tr("workspace.editor.runtime.required", required=required, managed=managed))
        self.runtime_current_label.setText(
            tr("workspace.editor.runtime.current_auto")
            if automatic
            else tr("workspace.editor.runtime.current_custom", path=configured)
        )
        self.runtime_install_button.setEnabled(bool(self._instance_name))
        self._populate_runtime_java_combo()

    def _populate_runtime_java_combo(self) -> None:
        current = str(self.runtime_java_combo.currentData() or "")
        profile = self._runtime_profile
        configured = str(getattr(profile, "configured_java_path", "") or "") if profile is not None else ""
        selected = configured if configured else current
        required = int(getattr(profile, "required_java_major", 0) or 0) if profile is not None else 0
        managed = int(getattr(profile, "managed_java_major", required) or required) if profile is not None else 0
        accepted = {major for major in (required, managed) if major > 0}

        self.runtime_java_combo.blockSignals(True)
        self.runtime_java_combo.clear()
        self.runtime_java_combo.addItem(tr("workspace.editor.runtime.automatic"), "")
        known_paths: set[str] = set()
        for java in self._java_installations:
            major = int(getattr(java, "major_version", getattr(java, "version", 0)) or 0)
            if accepted and major not in accepted:
                continue
            path = str(getattr(java, "executable", "") or "")
            if not path:
                continue
            known_paths.add(path.casefold())
            if configured and configured.casefold() == path.casefold():
                selected = path
            vendor = str(getattr(java, "vendor", "") or "").strip()
            version = str(getattr(java, "version_string", "") or "").strip()
            details = " ".join(part for part in (vendor, version) if part)
            label = f"Java {major}" + (f" • {details}" if details else "")
            self.runtime_java_combo.addItem(label, path)
        if configured and configured.casefold() not in known_paths:
            self.runtime_java_combo.addItem(tr("workspace.editor.runtime.configured_path", path=configured), configured)
        index = self.runtime_java_combo.findData(selected)
        self.runtime_java_combo.setCurrentIndex(max(0, index))
        self.runtime_java_combo.blockSignals(False)
        self.runtime_java_combo.setEnabled(bool(self._instance_name and profile is not None))

    def show_overview(self) -> None:
        self.navigation.setCurrentRow(0)

    def retranslate_dynamic(self) -> None:
        labels = (
            "workspace.editor.nav.overview",
            "workspace.editor.nav.version",
            "workspace.editor.nav.runtime",
            "workspace.editor.nav.mods",
            "workspace.editor.nav.settings",
            "workspace.editor.nav.maintenance",
            "workspace.editor.nav.diagnostics",
        )
        for item, key in zip(self._nav_items, labels):
            item.setText(tr(key))
        self.overview_title.setText(tr("workspace.editor.overview"))
        self.version_title.setText(tr("workspace.editor.version"))
        self.runtime_title.setText(tr("workspace.editor.runtime"))
        self.mods_title.setText(tr("workspace.editor.mods"))
        self.settings_title.setText(tr("workspace.editor.settings"))
        self.maintenance_title.setText(tr("workspace.editor.maintenance"))
        self.diagnostics_title.setText(tr("workspace.editor.diagnostics"))
        self.version_detail.setText(tr("workspace.editor.version_detail"))
        self.runtime_detail.setText(tr("workspace.editor.runtime_detail"))
        self.mods_detail.setText(tr("workspace.editor.mods_detail"))
        self.settings_detail.setText(tr("workspace.editor.settings_detail"))
        self.maintenance_detail.setText(tr("workspace.editor.maintenance_detail"))
        self.diagnostics_detail.setText(tr("workspace.editor.diagnostics_detail"))
        self.minecraft_component_label.setText(tr("workspace.editor.component.minecraft"))
        self.loader_component_label.setText(tr("workspace.editor.component.loader"))
        self.java_component_label.setText(tr("workspace.editor.component.java"))
        self.launch_button.setText(tr("workspace.action.launch"))
        self.open_folder_button.setText(tr("workspace.action.open_folder"))
        self.advanced_button.setText(tr("workspace.action.manage_components"))
        self.repair_loader_button.setText(tr("workspace.action.repair_loader"))
        self.runtime_scan_button.setText(tr("workspace.editor.runtime.scan"))
        self.runtime_install_button.setText(tr("workspace.editor.runtime.install"))
        self.runtime_apply_button.setText(tr("workspace.editor.runtime.apply"))
        self.manage_mods_button.setText(tr("workspace.action.manage_mods"))
        self.settings_button.setText(tr("workspace.action.instance_settings"))
        self.repair_button.setText(tr("workspace.action.repair"))
        self.backup_button.setText(tr("workspace.action.backup_full"))
        self.world_backup_button.setText(tr("workspace.action.backup_worlds"))
        self.restore_button.setText(tr("workspace.action.restore_backup"))
        self.open_backups_button.setText(tr("workspace.action.open_backups"))
        self.open_logs_button.setText(tr("workspace.action.open_loader_logs"))
        self.export_diagnostics_button.setText(tr("workspace.action.export_diagnostics"))
        self.set_instance(self._instance)
        self._render_runtime()
