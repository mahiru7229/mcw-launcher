from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton

from src.core.language.language_manager import tr
from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class InstancesPage(BasePage):
    refresh_requested = Signal()
    selected_instance_changed = Signal(str)
    create_requested = Signal(str, str, str)
    rename_requested = Signal(str, str)
    clone_requested = Signal(str, str, bool)
    delete_requested = Signal(str)
    import_requested = Signal(object)
    export_requested = Signal(str, object, bool)
    fabric_versions_requested = Signal(str)
    loader_change_requested = Signal(str, str, str)
    repair_loader_requested = Signal(str)
    manage_mods_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("Instances", "Create and manage isolated Minecraft instances, including Fabric Loader and per-instance mods.")
        self._instances: dict[str, object] = {}
        self._versions: list[object] = []
        self._fabric_versions: dict[str, list[object]] = {}
        self._pending_manage_loader_version = ""
        self._synchronizing = False
        self._build_ui()

    def _build_ui(self) -> None:
        selected_card = CardWidget("Active instance")
        self.instance_combo = QComboBox()
        self.instance_combo.currentTextChanged.connect(self._instance_selected)
        self.instance_info = QLabel("No instance selected")
        self.instance_info.setObjectName("MutedLabel")
        refresh_button = QPushButton("Refresh instances")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        selected_card.layout.addWidget(self.instance_combo)
        selected_card.layout.addWidget(self.instance_info)
        selected_card.layout.addWidget(refresh_button)
        self.root_layout.addWidget(selected_card)

        create_card = CardWidget("Create instance", "Choose Vanilla or Fabric. Fabric automatically uses the recommended stable Loader version.")
        self.create_name_input = QLineEdit()
        self.create_name_input.setPlaceholderText("New instance name")
        self.version_combo = QComboBox()
        self.snapshot_checkbox = QCheckBox("Show snapshots, old alpha, and old beta")
        self.snapshot_checkbox.toggled.connect(self._apply_version_filter)
        self.create_loader_combo = QComboBox()
        self.create_loader_combo.addItem("Vanilla", "vanilla")
        self.create_loader_combo.addItem("Fabric", "fabric")
        self.create_loader_status = QLabel("Fabric Loader versions can be changed later under Manage selected instance.")
        self.create_loader_status.setObjectName("MutedLabel")
        self.create_loader_status.setWordWrap(True)
        create_button = QPushButton("Create instance")
        create_button.setObjectName("PrimaryButton")
        create_button.clicked.connect(self._request_create)
        create_card.layout.addWidget(QLabel("Name"))
        create_card.layout.addWidget(self.create_name_input)
        create_card.layout.addWidget(QLabel("Minecraft version"))
        create_card.layout.addWidget(self.version_combo)
        create_card.layout.addWidget(self.snapshot_checkbox)
        create_card.layout.addWidget(QLabel("Mod loader"))
        create_card.layout.addWidget(self.create_loader_combo)
        create_card.layout.addWidget(self.create_loader_status)
        create_card.layout.addWidget(create_button)
        self.root_layout.addWidget(create_card)

        manage_card = CardWidget("Manage selected instance", "Change the selected instance's Fabric Loader version without recreating it.")
        self.manage_loader_combo = QComboBox()
        self.manage_loader_combo.addItem("Vanilla", "vanilla")
        self.manage_loader_combo.addItem("Fabric", "fabric")
        self.manage_loader_combo.currentTextChanged.connect(self._manage_loader_selected)
        self.manage_loader_version_combo = QComboBox()
        self.manage_loader_version_combo.setEnabled(False)
        self.manage_loader_status = QLabel("Select an instance to manage its mod loader.")
        self.manage_loader_status.setObjectName("MutedLabel")
        self.manage_loader_status.setWordWrap(True)
        self.apply_loader_button = QPushButton("Apply mod loader")
        self.apply_loader_button.clicked.connect(self._request_loader_change)
        self.apply_loader_button.setEnabled(False)
        self.repair_loader_button = QPushButton("Repair Fabric")
        self.repair_loader_button.setToolTip("Rebuild Fabric metadata and verify Loader libraries without changing mods or saves.")
        self.repair_loader_button.clicked.connect(self._request_loader_repair)
        self.repair_loader_button.setEnabled(False)

        self.target_name_input = QLineEdit()
        self.target_name_input.setPlaceholderText("New name or clone name")
        self.include_saves_checkbox = QCheckBox("Include saves when cloning or exporting")
        action_grid = QGridLayout()
        rename_button = QPushButton("Rename")
        clone_button = QPushButton("Clone")
        delete_button = QPushButton("Delete")
        delete_button.setObjectName("DangerButton")
        import_button = QPushButton("Import .mcwpack")
        export_button = QPushButton("Export .mcwpack")
        self.manage_mods_button = QPushButton("Manage mods")
        self.manage_mods_button.setObjectName("PrimaryButton")
        self.manage_mods_button.setEnabled(False)
        rename_button.clicked.connect(lambda: self.rename_requested.emit(self.current_instance_name(), self.target_name_input.text()))
        clone_button.clicked.connect(lambda: self.clone_requested.emit(self.current_instance_name(), self.target_name_input.text(), self.include_saves_checkbox.isChecked()))
        delete_button.clicked.connect(self._confirm_delete)
        import_button.clicked.connect(self._choose_import)
        export_button.clicked.connect(self._choose_export)
        self.manage_mods_button.clicked.connect(lambda: self.manage_mods_requested.emit(self.current_instance_name()))
        action_grid.addWidget(rename_button, 0, 0)
        action_grid.addWidget(clone_button, 0, 1)
        action_grid.addWidget(delete_button, 0, 2)
        action_grid.addWidget(import_button, 1, 0)
        action_grid.addWidget(export_button, 1, 1)
        action_grid.addWidget(self.manage_mods_button, 1, 2)

        manage_card.layout.addWidget(QLabel("Mod loader"))
        manage_card.layout.addWidget(self.manage_loader_combo)
        manage_card.layout.addWidget(QLabel("Fabric Loader version"))
        manage_card.layout.addWidget(self.manage_loader_version_combo)
        manage_card.layout.addWidget(self.manage_loader_status)
        manage_card.layout.addWidget(self.apply_loader_button)
        manage_card.layout.addWidget(self.repair_loader_button)
        manage_card.layout.addWidget(QLabel("Target name"))
        manage_card.layout.addWidget(self.target_name_input)
        manage_card.layout.addWidget(self.include_saves_checkbox)
        manage_card.layout.addLayout(action_grid)
        self.root_layout.addWidget(manage_card)
        self.root_layout.addStretch()

    def set_versions(self, versions: list) -> None:
        self._versions = list(versions)
        self._apply_version_filter()

    def set_fabric_versions(self, game_version: str, versions: list) -> None:
        self._fabric_versions[game_version] = list(versions)
        instance = self._instances.get(self.current_instance_name())

        if instance is None or instance.version_id != game_version:
            return
        if self.manage_loader_combo.currentData() != "fabric":
            return

        self._populate_manage_fabric_versions(instance, versions)

    def set_instances(self, instances: list, selected_name: str) -> None:
        self._instances = {instance.name: instance for instance in instances}
        self._synchronizing = True
        self.instance_combo.blockSignals(True)
        self.instance_combo.clear()
        self.instance_combo.addItems([instance.name for instance in instances])
        if selected_name:
            self.instance_combo.setCurrentText(selected_name)
        self.instance_combo.blockSignals(False)
        self._synchronizing = False
        self._render_instance(self.instance_combo.currentText())

    def set_show_snapshots(self, enabled: bool) -> None:
        self.snapshot_checkbox.setChecked(enabled)

    def current_instance_name(self) -> str:
        return self.instance_combo.currentText().strip()

    def selected_create_loader(self) -> str:
        return str(self.create_loader_combo.currentData() or "vanilla")

    def selected_manage_loader(self) -> tuple[str, str]:
        loader_name = str(self.manage_loader_combo.currentData() or "vanilla")
        loader_version = str(self.manage_loader_version_combo.currentData() or "").strip() if loader_name == "fabric" else "-1"
        return loader_name, loader_version

    def selected_loader(self) -> tuple[str, str]:
        return self.selected_manage_loader()

    def set_busy(self, busy: bool) -> None:
        self.setEnabled(not busy)

    def _apply_version_filter(self) -> None:
        selected = self.version_combo.currentText()
        include_all = self.snapshot_checkbox.isChecked()
        version_ids = [version.id for version in self._versions if include_all or getattr(version, "type", "") == "release"]
        self.version_combo.clear()
        self.version_combo.addItems(version_ids)
        if selected in version_ids:
            self.version_combo.setCurrentText(selected)

    def _instance_selected(self, name: str) -> None:
        self._render_instance(name)
        if not self._synchronizing:
            self.selected_instance_changed.emit(name if name in self._instances else "")

    def _render_instance(self, name: str) -> None:
        instance = self._instances.get(name)
        if instance is None:
            self.instance_info.setText(tr("No instance selected"))
            self.target_name_input.clear()
            self._set_manage_loader_available(False)
            self.manage_loader_status.setText(tr("Select an instance to manage its mod loader."))
            self.manage_mods_button.setEnabled(False)
            self.repair_loader_button.setEnabled(False)
            return

        loader_name, loader_version = self._instance_loader(instance)
        loader_text = loader_name if loader_name == "vanilla" else f"{loader_name} {loader_version}"
        self.instance_info.setText(f"{tr('Minecraft {version}', version=instance.version_id)} • {loader_text} • {instance.instance_dir}")
        self.target_name_input.setText(instance.name)
        self._set_manage_loader_available(True)
        self._pending_manage_loader_version = loader_version if loader_name == "fabric" else ""

        self.manage_loader_combo.blockSignals(True)
        self.manage_loader_combo.setCurrentIndex(max(0, self.manage_loader_combo.findData(loader_name)))
        self.manage_loader_combo.blockSignals(False)
        self.manage_mods_button.setEnabled(loader_name == "fabric")
        self.repair_loader_button.setEnabled(loader_name == "fabric")
        self._manage_loader_selected()

    def _set_manage_loader_available(self, available: bool) -> None:
        self.manage_loader_combo.setEnabled(available)
        self.manage_loader_version_combo.setEnabled(False)
        self.manage_loader_version_combo.clear()
        self.apply_loader_button.setEnabled(available)
        if not available:
            self.repair_loader_button.setEnabled(False)

    def _manage_loader_selected(self, _loader_text: str = "") -> None:
        instance = self._instances.get(self.current_instance_name())
        if instance is None:
            self._set_manage_loader_available(False)
            return

        is_fabric = self.manage_loader_combo.currentData() == "fabric"
        self.manage_loader_version_combo.clear()
        self.manage_loader_version_combo.setEnabled(is_fabric)
        current_is_fabric = self._instance_loader(instance)[0] == "fabric"
        self.manage_mods_button.setEnabled(current_is_fabric)
        self.repair_loader_button.setEnabled(current_is_fabric)

        if not is_fabric:
            self.manage_loader_status.setText(tr("Apply Vanilla to remove Fabric Loader from this instance. Mod files are kept in its mods folder."))
            self.apply_loader_button.setEnabled(True)
            return

        current_loader_name, current_loader_version = self._instance_loader(instance)
        self._pending_manage_loader_version = current_loader_version if current_loader_name == "fabric" else ""
        versions = self._fabric_versions.get(instance.version_id)
        if versions is None:
            self.manage_loader_status.setText(tr("Loading compatible Fabric Loader versions..."))
            self.apply_loader_button.setEnabled(False)
            self.fabric_versions_requested.emit(instance.version_id)
            return

        self._populate_manage_fabric_versions(instance, versions)

    def _populate_manage_fabric_versions(self, instance: object, versions: list) -> None:
        current_loader_name, current_loader_version = self._instance_loader(instance)
        preferred = self._pending_manage_loader_version
        self._pending_manage_loader_version = ""

        self.manage_loader_version_combo.blockSignals(True)
        self.manage_loader_version_combo.clear()
        for version in versions:
            label = version.version + (tr(" (stable)") if getattr(version, "stable", False) else "")
            self.manage_loader_version_combo.addItem(label, version.version)

        selected_version = preferred or (current_loader_version if current_loader_name == "fabric" else "")
        selected_index = self.manage_loader_version_combo.findData(selected_version) if selected_version else -1
        if selected_version and selected_index < 0:
            self.manage_loader_version_combo.insertItem(0, f"{selected_version}{tr(' (current)')}", selected_version)
            selected_index = 0
        if selected_index >= 0:
            self.manage_loader_version_combo.setCurrentIndex(selected_index)
        elif versions:
            stable_index = next((index for index, version in enumerate(versions) if getattr(version, "stable", False)), 0)
            self.manage_loader_version_combo.setCurrentIndex(stable_index)
        self.manage_loader_version_combo.blockSignals(False)

        has_version = self.manage_loader_version_combo.count() > 0
        self.manage_loader_version_combo.setEnabled(has_version)
        self.apply_loader_button.setEnabled(has_version)

        if versions:
            selected = str(self.manage_loader_version_combo.currentData() or "")
            current_text = tr(" Current: {version}.", version=current_loader_version) if current_loader_name == "fabric" else ""
            self.manage_loader_status.setText(tr("{count} compatible Fabric Loader version(s) found.{current} Selected: {selected}.", count=len(versions), current=current_text, selected=selected))
        elif current_loader_name == "fabric" and current_loader_version:
            self.manage_loader_status.setText(tr("Compatible versions could not be loaded. The current Loader {version} remains available.", version=current_loader_version))
        else:
            self.manage_loader_status.setText(tr("Fabric Loader is unavailable for this Minecraft version, or Fabric Meta could not be reached."))

    @staticmethod
    def _instance_loader(instance: object) -> tuple[str, str]:
        loader = tuple(getattr(instance, "mod_loader", ("vanilla", "-1")))
        loader_name = str(loader[0] if loader else "vanilla").strip().lower() or "vanilla"
        loader_version = str(loader[1] if len(loader) > 1 else "-1").strip()
        if loader_name == "vanilla":
            loader_version = "-1"
        return loader_name, loader_version

    def _request_create(self) -> None:
        self.create_requested.emit(self.create_name_input.text(), self.version_combo.currentText(), self.selected_create_loader())

    def _request_loader_change(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        loader_name, loader_version = self.selected_manage_loader()
        if loader_name == "fabric" and not loader_version:
            QMessageBox.information(self, tr("Fabric Loader"), tr("Select a Fabric Loader version first."))
            return
        self.loader_change_requested.emit(name, loader_name, loader_version)

    def _request_loader_repair(self) -> None:
        name = self.current_instance_name()
        instance = self._instances.get(name)
        if instance is None or self._instance_loader(instance)[0] != "fabric":
            return
        self.repair_loader_requested.emit(name)

    def _confirm_delete(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        answer = QMessageBox.question(self, tr("Delete instance"), tr("Delete '{name}' and its entire folder?", name=name), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(name)

    def _choose_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("Import MCW instance"), "", tr("MCW Package (*.mcwpack *.zip)"))
        if path:
            self.import_requested.emit(Path(path))

    def _choose_export(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        path, _ = QFileDialog.getSaveFileName(self, tr("Export MCW instance"), f"{name}.mcwpack", tr("MCW Package (*.mcwpack)"))
        if path:
            output_path = Path(path)
            if output_path.suffix.lower() != ".mcwpack":
                output_path = output_path.with_suffix(".mcwpack")
            self.export_requested.emit(name, output_path, self.include_saves_checkbox.isChecked())

    def retranslate_dynamic(self) -> None:
        self._render_instance(self.current_instance_name())
