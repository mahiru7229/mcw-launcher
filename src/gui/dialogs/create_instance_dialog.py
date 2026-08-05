from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.config.curseforge_config_manager import CurseForgeConfigManager
from mcw_core.api.language.language_manager import tr
from src.gui.loader_version_options import loader_title, loader_version_entries
from src.gui.theme.runtime import set_theme_icon
from src.gui.window_sizing import resize_dialog_to_screen


class CreateInstanceDialog(QDialog):
    create_requested = Signal(str, str, str, str)
    fabric_versions_requested = Signal(str)
    quilt_versions_requested = Signal(str)
    forge_versions_requested = Signal(str)
    neoforge_versions_requested = Signal(str)
    import_modpack_package_requested = Signal()
    browse_modrinth_requested = Signal()
    browse_curseforge_requested = Signal()
    browse_ftb_requested = Signal()

    MODDED_LOADERS = {"fabric", "quilt", "forge", "neoforge"}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setModal(False)
        self._versions: list[object] = []
        self._loader_versions: dict[tuple[str, str], list[object]] = {}
        self._pending_loader_requests: set[tuple[str, str]] = set()
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 720, 600, 600, 500)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.description_label = QLabel()
        self.description_label.setObjectName("MutedLabel")
        self.description_label.setWordWrap(True)
        root.addWidget(self.description_label)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._minecraft_tab(), "")
        self.tabs.addTab(self._modpack_tab(), "")
        root.addWidget(self.tabs, 1)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self.create_button = self.buttons.addButton("", QDialogButtonBox.ButtonRole.AcceptRole)
        self.create_button.setObjectName("PrimaryButton")
        self.create_button.clicked.connect(self._request_create)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

    def _minecraft_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.name_input = QLineEdit()
        self.version_combo = QComboBox()
        self.version_combo.setEditable(False)
        self.version_combo.currentTextChanged.connect(self._selection_changed)
        self.loader_combo = QComboBox()
        self.loader_combo.addItem("Vanilla", "vanilla")
        self.loader_combo.addItem("Fabric", "fabric")
        self.loader_combo.addItem("Quilt", "quilt")
        self.loader_combo.addItem("Forge", "forge")
        self.loader_combo.addItem("NeoForge", "neoforge")
        self.loader_combo.currentIndexChanged.connect(self._selection_changed)
        self.loader_version_combo = QComboBox()
        self.loader_version_combo.setEnabled(False)
        self.loader_version_combo.currentIndexChanged.connect(self._update_create_state)
        self.name_label = QLabel()
        self.version_label = QLabel()
        self.loader_label = QLabel()
        self.loader_version_label = QLabel()
        form.addRow(self.name_label, self.name_input)
        form.addRow(self.version_label, self.version_combo)
        form.addRow(self.loader_label, self.loader_combo)
        form.addRow(self.loader_version_label, self.loader_version_combo)
        layout.addLayout(form)

        self.snapshots_checkbox = QCheckBox()
        self.snapshots_checkbox.toggled.connect(lambda _checked: self._refresh_versions())
        layout.addWidget(self.snapshots_checkbox)

        self.loader_hint = QLabel()
        self.loader_hint.setObjectName("MutedLabel")
        self.loader_hint.setWordWrap(True)
        layout.addWidget(self.loader_hint)
        self.loader_status = QLabel()
        self.loader_status.setObjectName("MutedLabel")
        self.loader_status.setWordWrap(True)
        layout.addWidget(self.loader_status)
        layout.addStretch(1)
        return tab

    def _modpack_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(10)

        self.modpack_hint = QLabel()
        self.modpack_hint.setObjectName("MutedLabel")
        self.modpack_hint.setWordWrap(True)
        layout.addWidget(self.modpack_hint)

        self.modrinth_button = set_theme_icon(QPushButton(), "icon.action.modrinth")
        self.curseforge_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.ftb_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.import_button = set_theme_icon(QPushButton(), "icon.action.import")
        self.modrinth_button.clicked.connect(self._browse_modrinth)
        self.curseforge_button.clicked.connect(self._browse_curseforge)
        self.ftb_button.clicked.connect(self._browse_ftb)
        self.import_button.clicked.connect(self._import_package)
        layout.addWidget(self.modrinth_button)
        layout.addWidget(self.curseforge_button)
        layout.addWidget(self.ftb_button)
        layout.addWidget(self.import_button)
        layout.addStretch(1)
        return tab

    def set_versions(self, versions: list[object]) -> None:
        self._versions = list(versions)
        self._refresh_versions()

    def set_show_snapshots(self, enabled: bool) -> None:
        self.snapshots_checkbox.setChecked(bool(enabled))

    def selected_loader(self) -> str:
        return str(self.loader_combo.currentData() or "vanilla")

    def selected_loader_version(self) -> str:
        if self.selected_loader() == "vanilla":
            return "-1"
        return str(self.loader_version_combo.currentData() or "").strip()

    def set_fabric_versions(self, game_version: str, versions: list[object]) -> None:
        self._set_loader_versions("fabric", game_version, versions)

    def set_quilt_versions(self, game_version: str, versions: list[object]) -> None:
        self._set_loader_versions("quilt", game_version, versions)

    def set_forge_versions(self, game_version: str, versions: list[object]) -> None:
        self._set_loader_versions("forge", game_version, versions)

    def set_neoforge_versions(self, game_version: str, versions: list[object]) -> None:
        self._set_loader_versions("neoforge", game_version, versions)

    def _set_loader_versions(self, loader: str, game_version: str, versions: list[object]) -> None:
        key = (loader, str(game_version).strip())
        self._loader_versions[key] = list(versions)
        self._pending_loader_requests.discard(key)
        if key == (self.selected_loader(), self.version_combo.currentText().strip()):
            self._render_loader_versions(loader, list(versions))

    def _refresh_versions(self) -> None:
        selected = self.version_combo.currentText()
        include_all = self.snapshots_checkbox.isChecked()
        version_ids = [
            str(getattr(version, "id", ""))
            for version in self._versions
            if getattr(version, "id", "") and (include_all or str(getattr(version, "type", "")) == "release")
        ]
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        self.version_combo.addItems(version_ids)
        if selected in version_ids:
            self.version_combo.setCurrentText(selected)
        self.version_combo.blockSignals(False)
        self._selection_changed()

    def _selection_changed(self, *_args) -> None:
        loader = self.selected_loader()
        game_version = self.version_combo.currentText().strip()
        self.loader_version_combo.blockSignals(True)
        self.loader_version_combo.clear()
        self.loader_version_combo.blockSignals(False)

        if not game_version:
            self.loader_version_combo.setEnabled(False)
            self.loader_status.setText(tr("workspace.create.loader_version.select_minecraft"))
            self._update_create_state()
            return

        if loader == "vanilla":
            self.loader_version_combo.setEnabled(False)
            self.loader_status.setText(tr("workspace.create.loader_version.vanilla"))
            self._update_create_state()
            return

        key = (loader, game_version)
        cached = self._loader_versions.get(key)
        if cached is not None:
            self._render_loader_versions(loader, cached)
            return

        self.loader_version_combo.setEnabled(False)
        self.loader_status.setText(tr("workspace.create.loader_version.loading", loader=loader_title(loader), version=game_version))
        self._update_create_state()
        if key in self._pending_loader_requests:
            return
        self._pending_loader_requests.add(key)
        signal = {
            "fabric": self.fabric_versions_requested,
            "quilt": self.quilt_versions_requested,
            "forge": self.forge_versions_requested,
            "neoforge": self.neoforge_versions_requested,
        }.get(loader)
        if signal is not None:
            signal.emit(game_version)

    def _render_loader_versions(self, loader: str, versions: list[object]) -> None:
        entries = loader_version_entries(loader, versions, tr(" (stable)"))
        self.loader_version_combo.blockSignals(True)
        self.loader_version_combo.clear()
        for value, label, preferred in entries:
            self.loader_version_combo.addItem(label, value)
        preferred_index = next((index for index, (_value, _label, preferred) in enumerate(entries) if preferred), -1)
        if preferred_index >= 0:
            self.loader_version_combo.setCurrentIndex(preferred_index)
        elif entries:
            self.loader_version_combo.setCurrentIndex(0)
        self.loader_version_combo.blockSignals(False)
        has_versions = bool(entries)
        self.loader_version_combo.setEnabled(has_versions)
        if has_versions:
            selected = str(self.loader_version_combo.currentData() or "")
            self.loader_status.setText(tr("workspace.create.loader_version.available", count=len(entries), loader=loader_title(loader), version=self.version_combo.currentText(), selected=selected))
        else:
            self.loader_status.setText(tr("workspace.create.loader_version.unavailable", loader=loader_title(loader), version=self.version_combo.currentText()))
        self._update_create_state()


    def _update_create_state(self, *_args) -> None:
        if not hasattr(self, "create_button"):
            return
        game_version = self.version_combo.currentText().strip()
        loader = self.selected_loader()
        loader_ready = loader == "vanilla" or bool(self.selected_loader_version())
        self.create_button.setEnabled(bool(game_version) and loader_ready)

    def _request_create(self) -> None:
        name = self.name_input.text().strip()
        version_id = self.version_combo.currentText().strip()
        loader = self.selected_loader()
        loader_version = self.selected_loader_version()
        if not name:
            QMessageBox.information(self, tr("workspace.create.title"), tr("workspace.create.name_required"))
            return
        if not version_id:
            QMessageBox.information(self, tr("workspace.create.title"), tr("workspace.create.version_required"))
            return
        if loader in self.MODDED_LOADERS and not loader_version:
            QMessageBox.information(self, tr("workspace.create.title"), tr("workspace.create.loader_version.required", loader=loader_title(loader), version=version_id))
            return
        self.create_requested.emit(name, version_id, loader, loader_version)
        self.accept()

    def _browse_modrinth(self) -> None:
        self.browse_modrinth_requested.emit()
        self.accept()

    def _browse_curseforge(self) -> None:
        self.browse_curseforge_requested.emit()
        self.accept()

    def _browse_ftb(self) -> None:
        self.browse_ftb_requested.emit()
        self.accept()

    def _import_package(self) -> None:
        self.import_modpack_package_requested.emit()
        self.accept()

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("workspace.create.title"))
        self.description_label.setText(tr("workspace.create.description"))
        self.tabs.setTabText(0, tr("workspace.create.minecraft_tab"))
        self.tabs.setTabText(1, tr("workspace.create.modpack_tab"))
        self.name_input.setPlaceholderText(tr("workspace.create.name_placeholder"))
        self.name_label.setText(tr("workspace.create.name"))
        self.version_label.setText(tr("workspace.create.minecraft_version"))
        self.loader_label.setText(tr("workspace.create.loader"))
        self.loader_version_label.setText(tr("workspace.create.loader_version"))
        self.snapshots_checkbox.setText(tr("workspace.create.show_snapshots"))
        self.loader_hint.setText(tr("workspace.create.loader_hint"))
        self.modpack_hint.setText(tr("workspace.create.modpack_hint"))
        self.modrinth_button.setText(tr("workspace.create.browse_modrinth"))
        self.curseforge_button.setText(tr("workspace.create.browse_curseforge"))
        self.ftb_button.setText(tr("workspace.create.browse_ftb"))
        self.curseforge_button.setVisible(CurseForgeConfigManager.is_configured())
        self.import_button.setText(tr("modpack_package.import.local_button"))
        self.create_button.setText(tr("workspace.create.create_button"))
        if self.cancel_button is not None:
            self.cancel_button.setText(tr("common.cancel"))
        self._selection_changed()
