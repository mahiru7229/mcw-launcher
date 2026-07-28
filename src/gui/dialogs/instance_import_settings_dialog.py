from __future__ import annotations

import copy

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from src.core.instance.settings_manager import SettingsManager
from src.core.language.language_manager import tr
from src.gui.dialogs.instance_settings_editor_dialog import InstanceSettingsEditorDialog
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.package.instance_package_preview import InstancePackagePreview


class InstanceImportSettingsDialog(QDialog):
    MODE_LAUNCHER_DEFAULTS = "launcher_defaults"
    MODE_KEEP_PACKAGE = "keep_package"
    MODE_REVIEW = "review"

    def __init__(self, preview: InstancePackagePreview, launcher_defaults: dict, parent=None) -> None:
        super().__init__(parent)
        self._preview = preview
        self._launcher_defaults = SettingsManager.normalize_dict(launcher_defaults)
        review_source = preview.settings if preview.has_package_settings else self._launcher_defaults
        self._review_settings = SettingsManager.normalize_dict(review_source)
        self._review_confirmed = False
        self._build_ui()
        self._update_review_state()

    @property
    def selected_mode(self) -> str:
        if self.keep_package_radio.isChecked():
            return self.MODE_KEEP_PACKAGE
        if self.review_radio.isChecked():
            return self.MODE_REVIEW
        return self.MODE_LAUNCHER_DEFAULTS

    @property
    def selected_settings_override(self) -> dict | None:
        if self.selected_mode == self.MODE_KEEP_PACKAGE:
            return None
        if self.selected_mode == self.MODE_REVIEW:
            return copy.deepcopy(self._review_settings)
        return copy.deepcopy(self._launcher_defaults)

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 660, 560, 560, 460)
        self.setWindowTitle(tr("instance_import.settings.title"))
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        title = QLabel(tr("instance_import.settings.heading"))
        title.setObjectName("PageTitle")
        root.addWidget(title)

        loader_name, loader_version = self._preview.mod_loader
        package_details = QLabel(
            tr(
                "instance_import.settings.package",
                name=self._preview.name,
                minecraft=self._preview.version_id,
                loader=loader_name.title(),
                loader_version=loader_version,
            )
        )
        package_details.setObjectName("ValueLabel")
        package_details.setWordWrap(True)
        root.addWidget(package_details)

        help_label = QLabel(tr("instance_import.settings.description"))
        help_label.setObjectName("MutedLabel")
        help_label.setWordWrap(True)
        root.addWidget(help_label)

        self.launcher_defaults_radio = QRadioButton(tr("instance_import.settings.use_defaults"))
        self.launcher_defaults_radio.setChecked(True)
        defaults_detail = QLabel(InstanceSettingsEditorDialog.summary(self._launcher_defaults))
        defaults_detail.setObjectName("MutedLabel")
        defaults_detail.setWordWrap(True)
        root.addWidget(self.launcher_defaults_radio)
        root.addWidget(defaults_detail)

        self.keep_package_radio = QRadioButton(tr("instance_import.settings.keep_package"))
        self.keep_package_radio.setEnabled(self._preview.has_package_settings)
        keep_detail_text = (
            InstanceSettingsEditorDialog.summary(self._preview.settings)
            if self._preview.has_package_settings
            else tr("instance_import.settings.no_package_settings")
        )
        keep_detail = QLabel(keep_detail_text)
        keep_detail.setObjectName("MutedLabel")
        keep_detail.setWordWrap(True)
        root.addWidget(self.keep_package_radio)
        root.addWidget(keep_detail)

        self.review_radio = QRadioButton(tr("instance_import.settings.review"))
        self.review_detail = QLabel(InstanceSettingsEditorDialog.summary(self._review_settings))
        self.review_detail.setObjectName("MutedLabel")
        self.review_detail.setWordWrap(True)
        self.review_button = QPushButton(tr("instance_import.settings.open_editor"))
        self.review_button.clicked.connect(self._open_review_editor)
        self.review_radio.toggled.connect(self._update_review_state)
        root.addWidget(self.review_radio)
        root.addWidget(self.review_detail)
        root.addWidget(self.review_button)
        root.addStretch(1)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if self.cancel_button is not None:
            self.cancel_button.setText(tr("common.cancel"))
        self.import_button = self.buttons.addButton(
            tr("instance_import.settings.import"),
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self.import_button.setObjectName("PrimaryButton")
        self.import_button.clicked.connect(self._accept_import)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

    def _update_review_state(self, _checked: bool = False) -> None:
        enabled = self.review_radio.isChecked()
        self.review_button.setEnabled(enabled)
        self.review_detail.setEnabled(enabled)

    def _open_review_editor(self) -> bool:
        editor = InstanceSettingsEditorDialog(
            self._review_settings,
            self,
            title=tr("instance_import.settings.editor_title", name=self._preview.name),
        )
        if not editor.exec():
            return False
        self._review_settings = editor.settings_data
        self._review_confirmed = True
        self.review_detail.setText(InstanceSettingsEditorDialog.summary(self._review_settings))
        return True

    def _accept_import(self) -> None:
        if self.selected_mode == self.MODE_REVIEW and not self._review_confirmed:
            if not self._open_review_editor():
                return
        self.accept()
