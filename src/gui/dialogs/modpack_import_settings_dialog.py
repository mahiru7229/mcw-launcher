from __future__ import annotations

import copy

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QLabel, QLineEdit, QPushButton, QVBoxLayout

from mcw_core.api.instance.settings_manager import SettingsManager
from mcw_core.api.language.language_manager import tr
from src.gui.dialogs.instance_settings_editor_dialog import InstanceSettingsEditorDialog
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.package.provider_modpack_preview import ProviderModpackPreview


class ModpackImportSettingsDialog(QDialog):
    def __init__(self, preview: ProviderModpackPreview, launcher_defaults: dict, parent=None) -> None:
        super().__init__(parent)
        self._preview = preview
        base = preview.settings if preview.has_package_settings else launcher_defaults
        self._settings = SettingsManager.normalize_dict(base)
        self._reviewed = False
        self._build_ui()

    @property
    def instance_name(self) -> str:
        return self.name_input.text().strip()

    @property
    def selected_settings_override(self) -> dict:
        return copy.deepcopy(self._settings)

    @property
    def install_optional_files(self) -> bool:
        return self.optional_checkbox.isChecked()

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 680, 600, 560, 480)
        self.setWindowTitle(tr("modpack_package.import.title"))
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        title = QLabel(tr("modpack_package.import.heading"))
        title.setObjectName("PageTitle")
        root.addWidget(title)
        provider = self._preview.provider.title() if self._preview.provider != "mcw" else "MCW"
        loader_name, loader_version = self._preview.mod_loader
        details = QLabel(
            tr(
                "modpack_package.import.details",
                provider=provider,
                name=self._preview.name,
                version=self._preview.version_label,
                minecraft=self._preview.minecraft_version,
                loader=loader_name.title(),
                loader_version=loader_version,
                files=self._preview.file_count,
            )
        )
        details.setObjectName("ValueLabel")
        details.setWordWrap(True)
        root.addWidget(details)

        self.name_input = QLineEdit(self._preview.name)
        self.name_input.setPlaceholderText(tr("workspace.create.name_placeholder"))
        root.addWidget(QLabel(tr("workspace.create.name")))
        root.addWidget(self.name_input)

        self.optional_checkbox = QCheckBox(tr("modpack_package.import.optional"))
        self.optional_checkbox.setChecked(bool(self._preview.install_optional_files))
        root.addWidget(self.optional_checkbox)

        self.settings_summary = QLabel(InstanceSettingsEditorDialog.summary(self._settings))
        self.settings_summary.setObjectName("MutedLabel")
        self.settings_summary.setWordWrap(True)
        root.addWidget(self.settings_summary)
        self.review_button = QPushButton(tr("modpack_package.import.review_settings"))
        self.review_button.clicked.connect(self._review_settings)
        root.addWidget(self.review_button)

        note = QLabel(tr("modpack_package.import.deferred_note"))
        note.setObjectName("MutedLabel")
        note.setWordWrap(True)
        root.addWidget(note)
        root.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel is not None:
            cancel.setText(tr("common.cancel"))
        import_button = buttons.addButton(tr("modpack_package.import.action"), QDialogButtonBox.ButtonRole.AcceptRole)
        import_button.setObjectName("PrimaryButton")
        import_button.clicked.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _review_settings(self) -> bool:
        editor = InstanceSettingsEditorDialog(self._settings, self, title=tr("instance_import.settings.editor_title", name=self.instance_name or self._preview.name))
        if not editor.exec():
            return False
        self._settings = editor.settings_data
        self._reviewed = True
        self.settings_summary.setText(InstanceSettingsEditorDialog.summary(self._settings))
        return True

    def _accept(self) -> None:
        if not self.instance_name:
            return
        if not self._reviewed and not self._review_settings():
            return
        self.accept()
