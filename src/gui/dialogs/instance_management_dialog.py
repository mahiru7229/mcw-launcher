from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
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
    create_backup_requested = Signal(str, str)
    restore_backup_requested = Signal(str)
    open_backups_requested = Signal(str)
    open_logs_requested = Signal(str)
    export_diagnostics_requested = Signal(str)
    advanced_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setModal(False)
        self._instance: object | None = None
        self._instance_name = ""
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
        self.launch_button = set_theme_icon(QPushButton(), "icon.action.launch")
        self.launch_button.setObjectName("PrimaryButton")
        self.open_folder_button = set_theme_icon(QPushButton(), "icon.action.folder")
        self.launch_button.clicked.connect(lambda: self._emit_and_hide(self.launch_requested))
        self.open_folder_button.clicked.connect(lambda: self.open_folder_requested.emit(self._instance_name))
        layout.addWidget(self.overview_title)
        layout.addWidget(self.overview_detail)
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
        self.version_summary = QLabel()
        self.version_summary.setObjectName("ValueLabel")
        self.version_summary.setWordWrap(True)
        self.advanced_button = set_theme_icon(QPushButton(), "icon.action.edit")
        self.advanced_button.setObjectName("PrimaryButton")
        self.advanced_button.clicked.connect(lambda: self._emit_and_hide(self.advanced_requested, self._instance_name))
        layout.addWidget(self.version_title)
        layout.addWidget(self.version_detail)
        layout.addWidget(self.version_summary)
        layout.addWidget(self.advanced_button)
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

    def set_instance(self, instance: object | None) -> None:
        self._instance = instance
        self._instance_name = str(getattr(instance, "name", "")) if instance is not None else ""
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
        self.version_summary.setText(tr("workspace.editor.version_summary", version=version_id, loader=loader_text))

    def show_overview(self) -> None:
        self.navigation.setCurrentRow(0)

    def retranslate_dynamic(self) -> None:
        labels = (
            "workspace.editor.nav.overview",
            "workspace.editor.nav.version",
            "workspace.editor.nav.mods",
            "workspace.editor.nav.settings",
            "workspace.editor.nav.maintenance",
            "workspace.editor.nav.diagnostics",
        )
        for item, key in zip(self._nav_items, labels):
            item.setText(tr(key))
        self.overview_title.setText(tr("workspace.editor.overview"))
        self.version_title.setText(tr("workspace.editor.version"))
        self.mods_title.setText(tr("workspace.editor.mods"))
        self.settings_title.setText(tr("workspace.editor.settings"))
        self.maintenance_title.setText(tr("workspace.editor.maintenance"))
        self.diagnostics_title.setText(tr("workspace.editor.diagnostics"))
        self.version_detail.setText(tr("workspace.editor.version_detail"))
        self.mods_detail.setText(tr("workspace.editor.mods_detail"))
        self.settings_detail.setText(tr("workspace.editor.settings_detail"))
        self.maintenance_detail.setText(tr("workspace.editor.maintenance_detail"))
        self.diagnostics_detail.setText(tr("workspace.editor.diagnostics_detail"))
        self.launch_button.setText(tr("workspace.action.launch"))
        self.open_folder_button.setText(tr("workspace.action.open_folder"))
        self.advanced_button.setText(tr("workspace.action.advanced"))
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
