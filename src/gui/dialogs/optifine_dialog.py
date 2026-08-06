from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from mcw_core.api.language.language_manager import tr
from src.gui.window_sizing import resize_dialog_to_screen


class OptiFineDialog(QDialog):
    OFFICIAL_DOWNLOADS_URL = "https://optifine.net/downloads"
    versions_requested = Signal(str, bool, bool)
    state_requested = Signal(str)
    install_requested = Signal(str, object, object, str)
    repair_requested = Signal(str)
    uninstall_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setModal(False)
        self._instance = None
        self._versions: list[object] = []
        self._state = None
        self._source_path: Path | None = None
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 660, 520, 540, 440)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.description_label = QLabel()
        self.description_label.setObjectName("MutedLabel")
        self.description_label.setWordWrap(True)
        root.addWidget(self.description_label)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.instance_value = QLabel()
        self.mode_value = QLabel()
        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self._update_state)
        self.preview_checkbox = QCheckBox()
        self.preview_checkbox.toggled.connect(lambda _checked: self.refresh_versions())
        self.source_value = QLabel()
        self.source_value.setWordWrap(True)
        self.instance_label = QLabel()
        self.mode_label = QLabel()
        self.version_label = QLabel()
        self.source_label = QLabel()
        form.addRow(self.instance_label, self.instance_value)
        form.addRow(self.mode_label, self.mode_value)
        form.addRow(self.version_label, self.version_combo)
        form.addRow("", self.preview_checkbox)
        form.addRow(self.source_label, self.source_value)
        root.addLayout(form)

        source_row = QHBoxLayout()
        self.open_official_button = QPushButton()
        self.choose_file_button = QPushButton()
        self.refresh_button = QPushButton()
        self.open_official_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.OFFICIAL_DOWNLOADS_URL)))
        self.choose_file_button.clicked.connect(self._choose_file)
        self.refresh_button.clicked.connect(lambda: self.refresh_versions(force=True))
        source_row.addWidget(self.open_official_button)
        source_row.addWidget(self.choose_file_button)
        source_row.addWidget(self.refresh_button)
        root.addLayout(source_row)

        self.status_label = QLabel()
        self.status_label.setObjectName("MutedLabel")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)
        root.addStretch(1)

        actions = QHBoxLayout()
        self.install_button = QPushButton()
        self.install_button.setObjectName("PrimaryButton")
        self.repair_button = QPushButton()
        self.uninstall_button = QPushButton()
        self.close_button = QPushButton()
        self.install_button.clicked.connect(self._install)
        self.repair_button.clicked.connect(self._repair)
        self.uninstall_button.clicked.connect(self._uninstall)
        self.close_button.clicked.connect(self.close)
        actions.addWidget(self.install_button)
        actions.addWidget(self.repair_button)
        actions.addWidget(self.uninstall_button)
        actions.addStretch(1)
        actions.addWidget(self.close_button)
        root.addLayout(actions)

    def open_for_instance(self, instance: object) -> None:
        self._instance = instance
        self._source_path = None
        self.source_value.setText(tr("optifine.file.not_selected"))
        self.instance_value.setText(str(getattr(instance, "name", "")))
        loader = str((getattr(instance, "mod_loader", ("vanilla", "-1")) or ("vanilla", "-1"))[0]).casefold()
        self.mode_value.setText(tr("optifine.mode.standalone") if loader == "vanilla" else tr("optifine.mode.forge_mod") if loader == "forge" else tr("optifine.mode.unsupported"))
        self.state_requested.emit(str(getattr(instance, "name", "")))
        self.refresh_versions()
        self._update_state()
        self.show()
        self.raise_()
        self.activateWindow()

    def refresh_versions(self, force: bool = False) -> None:
        if self._instance is None:
            return
        game = str(getattr(self._instance, "version_id", ""))
        self.status_label.setText(tr("optifine.metadata.loading"))
        self.versions_requested.emit(game, self.preview_checkbox.isChecked(), bool(force))

    def set_versions(self, game_version: str, versions: list[object], include_preview: bool = False) -> None:
        if self._instance is None or str(getattr(self._instance, "version_id", "")) != str(game_version):
            return
        self._versions = list(versions)
        selected_id = str(getattr(self.version_combo.currentData(), "version_id", ""))
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for item in self._versions:
            details = str(getattr(item, "display_name", getattr(item, "version_id", "OptiFine")))
            forge = str(getattr(item, "forge_version", ""))
            if forge:
                details += f" · Forge {forge}"
            self.version_combo.addItem(details, item)
        if selected_id:
            for index in range(self.version_combo.count()):
                if str(getattr(self.version_combo.itemData(index), "version_id", "")) == selected_id:
                    self.version_combo.setCurrentIndex(index)
                    break
        self.version_combo.blockSignals(False)
        self.status_label.setText(tr("optifine.metadata.available", count=len(self._versions)) if self._versions else tr("optifine.metadata.none"))
        self._update_state()

    def set_state(self, instance_name: str, state: object) -> None:
        if self._instance is None or str(getattr(self._instance, "name", "")) != str(instance_name):
            return
        self._state = state
        installed = bool(getattr(state, "installed", False))
        if installed:
            self.status_label.setText(tr("optifine.state.installed", version=getattr(state, "version_id", ""), mode=getattr(state, "mode", "")))
        self._update_state()

    def _choose_file(self) -> None:
        selected = self.version_combo.currentData()
        expected = str(getattr(selected, "filename", "OptiFine_*.jar"))
        path, _filter = QFileDialog.getOpenFileName(self, tr("optifine.file.choose_title"), "", f"{expected} (*.jar);;Java Archive (*.jar)")
        if path:
            self._source_path = Path(path)
            self.source_value.setText(str(self._source_path))
            self._update_state()

    def _install(self) -> None:
        if self._instance is None or self.version_combo.currentData() is None or self._source_path is None:
            QMessageBox.information(self, tr("optifine.title"), tr("optifine.file.required"))
            return
        name = str(getattr(self._instance, "name", ""))
        self.install_requested.emit(name, self.version_combo.currentData(), self._source_path, "auto")

    def _repair(self) -> None:
        if self._instance is not None:
            self.repair_requested.emit(str(getattr(self._instance, "name", "")))

    def _uninstall(self) -> None:
        if self._instance is None:
            return
        if QMessageBox.question(self, tr("optifine.title"), tr("optifine.uninstall.confirm")) == QMessageBox.StandardButton.Yes:
            self.uninstall_requested.emit(str(getattr(self._instance, "name", "")))

    def _update_state(self, *_args) -> None:
        loader = str((getattr(self._instance, "mod_loader", ("", "")) or ("", ""))[0]).casefold() if self._instance is not None else ""
        supported = loader in {"vanilla", "forge"}
        selected = self.version_combo.currentData()
        forge_unavailable = loader == "forge" and bool(getattr(selected, "forge_unavailable", False))
        installed = bool(getattr(self._state, "installed", False))
        self.install_button.setEnabled(supported and selected is not None and self._source_path is not None and not forge_unavailable)
        self.repair_button.setEnabled(installed and bool(getattr(self._state, "managed", False)))
        self.uninstall_button.setEnabled(installed and bool(getattr(self._state, "managed", False)))
        if not supported:
            self.status_label.setText(tr("optifine.mode.unsupported_detail"))
        elif forge_unavailable:
            self.status_label.setText(tr("optifine.compatibility.forge_unavailable"))

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("optifine.title"))
        self.description_label.setText(tr("optifine.description"))
        self.instance_label.setText(tr("optifine.instance"))
        self.mode_label.setText(tr("optifine.install_mode"))
        self.version_label.setText(tr("optifine.version"))
        self.source_label.setText(tr("optifine.file"))
        self.preview_checkbox.setText(tr("optifine.show_previews"))
        self.open_official_button.setText(tr("optifine.open_official"))
        self.choose_file_button.setText(tr("optifine.choose_file"))
        self.refresh_button.setText(tr("common.refresh"))
        self.install_button.setText(tr("optifine.install"))
        self.repair_button.setText(tr("workspace.action.repair"))
        self.uninstall_button.setText(tr("common.uninstall"))
        self.close_button.setText(tr("common.close"))
