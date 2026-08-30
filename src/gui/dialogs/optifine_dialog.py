from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.language.language_manager import tr
from src.gui.window_sizing import resize_dialog_to_screen
from src.gui.widget.scrollable_page import scrollable_page
from src.models.optifine.optifine_models import OptiFineVersion


class OptiFineDialog(QDialog):
    OFFICIAL_DOWNLOADS_URL = "https://optifine.net/downloads"
    state_requested = Signal(str)
    install_requested = Signal(str, object, str)
    repair_requested = Signal(str)
    uninstall_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setModal(False)
        self._instance = None
        self._state = None
        self._source_path: Path | None = None
        self._detected_version: OptiFineVersion | None = None
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 660, 470, 540, 400)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.description_label = QLabel()
        self.description_label.setObjectName("MutedLabel")
        self.description_label.setWordWrap(True)
        content_layout.addWidget(self.description_label)

        form = QGridLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(8)
        form.setColumnStretch(1, 1)
        self.instance_value = QLabel()
        self.mode_value = QLabel()
        self.version_value = QLabel()
        self.version_value.setWordWrap(False)
        self.version_value.setMinimumWidth(280)
        self.version_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.source_value = QLabel()
        self.source_value.setWordWrap(True)
        self.source_value.setMinimumWidth(280)
        self.source_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.instance_label = QLabel()
        self.mode_label = QLabel()
        self.version_label = QLabel()
        self.source_label = QLabel()
        form.addWidget(self.instance_label, 0, 0)
        form.addWidget(self.instance_value, 0, 1)
        form.addWidget(self.mode_label, 1, 0)
        form.addWidget(self.mode_value, 1, 1)
        form.addWidget(self.version_label, 2, 0)
        form.addWidget(self.version_value, 2, 1)
        form.addWidget(self.source_label, 3, 0, Qt.AlignmentFlag.AlignTop)
        form.addWidget(self.source_value, 3, 1)
        content_layout.addLayout(form)

        source_row = QHBoxLayout()
        self.open_official_button = QPushButton()
        self.choose_file_button = QPushButton()
        self.open_official_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.OFFICIAL_DOWNLOADS_URL)))
        self.choose_file_button.clicked.connect(self._choose_file)
        source_row.addWidget(self.open_official_button)
        source_row.addWidget(self.choose_file_button)
        source_row.addStretch(1)
        content_layout.addLayout(source_row)

        self.status_label = QLabel()
        self.status_label.setObjectName("MutedLabel")
        self.status_label.setWordWrap(True)
        content_layout.addWidget(self.status_label)
        content_layout.addStretch(1)
        self.content_scroll = scrollable_page(content, object_name="OptiFineScrollArea")
        root.addWidget(self.content_scroll, 1)

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
        self._state = None
        self._source_path = None
        self._detected_version = None
        self.source_value.setText(tr("optifine.file.not_selected"))
        self.version_value.setText(tr("optifine.file.not_detected"))
        self.instance_value.setText(str(getattr(instance, "name", "")))
        loader = self._loader()
        self.mode_value.setText(tr("optifine.mode.standalone") if loader == "vanilla" else tr("optifine.mode.forge_mod") if loader == "forge" else tr("optifine.mode.unsupported"))
        self.state_requested.emit(str(getattr(instance, "name", "")))
        self._update_state()
        self.show()
        self.raise_()
        self.activateWindow()

    def set_state(self, instance_name: str, state: object) -> None:
        if self._instance is None or str(getattr(self._instance, "name", "")) != str(instance_name):
            return
        self._state = state
        self._update_state()

    def _choose_file(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(self, tr("optifine.file.choose_title"), "", "OptiFine (*.jar);;Java Archive (*.jar)")
        if not path:
            return
        try:
            detected = OptiFineVersion.from_filename(Path(path).name)
        except ValueError:
            QMessageBox.warning(self, tr("optifine.title"), tr("optifine.file.invalid_name"))
            return
        expected = str(getattr(self._instance, "version_id", "")) if self._instance is not None else ""
        if expected and detected.minecraft_version != expected:
            QMessageBox.warning(
                self,
                tr("optifine.title"),
                tr("optifine.file.version_mismatch", actual=detected.minecraft_version, expected=expected),
            )
            return
        self._source_path = Path(path)
        self._detected_version = detected
        self.source_value.setText(str(self._source_path))
        self.version_value.setText(tr("optifine.file.detected", version=detected.display_name, minecraft=detected.minecraft_version))
        self.status_label.setText(tr("optifine.file.ready"))
        self._update_state()

    def _install(self) -> None:
        if self._instance is None or self._source_path is None or self._detected_version is None:
            QMessageBox.information(self, tr("optifine.title"), tr("optifine.file.required"))
            return
        self.install_requested.emit(str(getattr(self._instance, "name", "")), self._source_path, "auto")

    def _repair(self) -> None:
        if self._instance is not None:
            self.repair_requested.emit(str(getattr(self._instance, "name", "")))

    def _uninstall(self) -> None:
        if self._instance is None:
            return
        if QMessageBox.question(self, tr("optifine.title"), tr("optifine.uninstall.confirm")) == QMessageBox.StandardButton.Yes:
            self.uninstall_requested.emit(str(getattr(self._instance, "name", "")))

    def _loader(self) -> str:
        if self._instance is None:
            return ""
        loader = getattr(self._instance, "mod_loader", ("", "")) or ("", "")
        return str(loader[0]).casefold()

    def _update_state(self, *_args) -> None:
        loader = self._loader()
        supported = loader in {"vanilla", "forge"}
        installed = bool(getattr(self._state, "installed", False))
        self.install_button.setEnabled(supported and self._source_path is not None and self._detected_version is not None)
        self.repair_button.setEnabled(installed and bool(getattr(self._state, "managed", False)))
        self.uninstall_button.setEnabled(installed and bool(getattr(self._state, "managed", False)))
        if not supported:
            self.status_label.setText(tr("optifine.mode.unsupported_detail"))
        elif self._source_path is None and installed:
            self.status_label.setText(tr("optifine.state.installed", version=getattr(self._state, "version_id", ""), mode=getattr(self._state, "mode", "")))
        elif self._source_path is None:
            self.status_label.setText(tr("optifine.file.select_hint"))

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("optifine.title"))
        self.description_label.setText(tr("optifine.description"))
        self.instance_label.setText(tr("optifine.instance"))
        self.mode_label.setText(tr("optifine.install_mode"))
        self.version_label.setText(tr("optifine.detected_version"))
        self.source_label.setText(tr("optifine.file"))
        self.open_official_button.setText(tr("optifine.open_official"))
        self.choose_file_button.setText(tr("optifine.choose_file"))
        self.install_button.setText(tr("optifine.install"))
        self.repair_button.setText(tr("workspace.action.repair"))
        self.uninstall_button.setText(tr("common.uninstall"))
        self.close_button.setText(tr("common.close"))
