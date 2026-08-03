from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QLabel, QRadioButton, QVBoxLayout

from mcw_core.api.language.language_manager import tr
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.package.modpack_export import ModpackExportOptions


class ModpackExportDialog(QDialog):
    def __init__(self, instance_name: str, parent=None) -> None:
        super().__init__(parent)
        self._instance_name = instance_name
        self.output_path: Path | None = None
        self._build_ui()
        self._update_mode()

    @property
    def options(self) -> ModpackExportOptions:
        mode = ModpackExportOptions.PROVIDER_PROFILE if self.provider_radio.isChecked() else ModpackExportOptions.PORTABLE
        portable_mode = str(self.portable_mode.currentData() or ModpackExportOptions.SMART)
        return ModpackExportOptions(mode=mode, portable_mode=portable_mode, include_saves=self.include_saves.isChecked())

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 720, 610, 590, 500)
        self.setWindowTitle(tr("modpack_package.export.title"))
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        title = QLabel(tr("modpack_package.export.heading"))
        title.setObjectName("PageTitle")
        root.addWidget(title)
        intro = QLabel(tr("modpack_package.export.description"))
        intro.setObjectName("MutedLabel")
        intro.setWordWrap(True)
        root.addWidget(intro)

        self.provider_radio = QRadioButton(tr("modpack_package.export.provider_profile"))
        self.provider_radio.setChecked(True)
        provider_help = QLabel(tr("modpack_package.export.provider_profile_help"))
        provider_help.setObjectName("MutedLabel")
        provider_help.setWordWrap(True)
        root.addWidget(self.provider_radio)
        root.addWidget(provider_help)

        self.portable_radio = QRadioButton(tr("modpack_package.export.portable"))
        portable_help = QLabel(tr("modpack_package.export.portable_help"))
        portable_help.setObjectName("MutedLabel")
        portable_help.setWordWrap(True)
        root.addWidget(self.portable_radio)
        root.addWidget(portable_help)

        self.portable_mode = QComboBox()
        self.portable_mode.addItem(tr("modpack_package.export.smart"), ModpackExportOptions.SMART)
        self.portable_mode.addItem(tr("modpack_package.export.full"), ModpackExportOptions.FULL)
        root.addWidget(self.portable_mode)
        self.include_saves = QCheckBox(tr("workspace.export.include_saves"))
        root.addWidget(self.include_saves)

        warning = QLabel(tr("modpack_package.export.warning"))
        warning.setObjectName("WarningLabel")
        warning.setWordWrap(True)
        root.addWidget(warning)
        root.addStretch(1)

        self.provider_radio.toggled.connect(self._update_mode)
        self.portable_radio.toggled.connect(self._update_mode)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel is not None:
            cancel.setText(tr("common.cancel"))
        export_button = buttons.addButton(tr("modpack_package.export.action"), QDialogButtonBox.ButtonRole.AcceptRole)
        export_button.setObjectName("PrimaryButton")
        export_button.clicked.connect(self._choose_output)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _update_mode(self) -> None:
        portable = self.portable_radio.isChecked()
        self.portable_mode.setEnabled(portable)
        self.include_saves.setEnabled(portable)

    def _choose_output(self) -> None:
        options = self.options
        if options.mode == ModpackExportOptions.PROVIDER_PROFILE:
            suggested = f"{self._instance_name}-MCW-Profile.zip"
            title = tr("modpack_package.export.provider_save_title")
            file_filter = tr("modpack_package.export.provider_filter")
            suffix = ".zip"
        else:
            suggested = f"{self._instance_name}.mcwpack"
            title = tr("modpack_package.export.portable_save_title")
            file_filter = tr("modpack_package.export.portable_filter")
            suffix = ".mcwpack"
        path, _ = QFileDialog.getSaveFileName(self, title, suggested, file_filter)
        if not path:
            return
        output = Path(path)
        if output.suffix.casefold() != suffix:
            output = output.with_suffix(suffix)
        self.output_path = output
        self.accept()
