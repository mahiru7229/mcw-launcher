from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from mcw_core.api.language.language_manager import tr
from src.gui.window_sizing import resize_dialog_to_screen
class CurseForgeManualDownloadDialog(QDialog):
    files_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._requirements: list[object] = []
        self._installed: set[tuple[str, str, str, str]] = set()
        self._instance_name = ""
        self._provider_name = "CurseForge"
        resize_dialog_to_screen(self, 980, 560, 700, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        self.summary_label = QLabel()
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.summary_label)

        self.table = QTableWidget(0, 5)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._update_actions)
        self.table.itemDoubleClicked.connect(lambda _item: self._open_page())
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.open_page_button = QPushButton()
        self.add_files_button = QPushButton()
        self.close_button = QPushButton()
        self.open_page_button.clicked.connect(self._open_page)
        self.add_files_button.clicked.connect(self._select_files)
        self.close_button.clicked.connect(self.accept)
        actions.addWidget(self.open_page_button)
        actions.addWidget(self.add_files_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)
        self.retranslate_dynamic()

    def set_instance_context(self, instance_name: str, _instance_dir: Path | str | None = None) -> None:
        self._instance_name = str(instance_name or "")
        self._update_summary()
        self._update_actions()

    def set_requirements(self, requirements: tuple[object, ...] | list[object]) -> None:
        self._requirements = list(requirements)
        provider = str(getattr(self._requirements[0], "provider", "curseforge") if self._requirements else "curseforge").strip().casefold()
        self._provider_name = "Modrinth" if provider == "modrinth" else "CurseForge"
        self._installed.clear()
        self.retranslate_dynamic()

    def mark_installed(self, requirement: object) -> None:
        self._installed.add(self._requirement_key(requirement))
        self._render()

    @property
    def remaining_count(self) -> int:
        return len(self.remaining_requirements)

    @property
    def remaining_requirements(self) -> tuple[object, ...]:
        return tuple(item for item in self._requirements if self._requirement_key(item) not in self._installed)

    @property
    def is_modpack_archive_mode(self) -> bool:
        return bool(self._requirements) and all(str(getattr(item, "managed_kind", "")) == "modpack_archive" for item in self._requirements)

    def _render(self) -> None:
        self.table.setRowCount(len(self._requirements))
        for row, requirement in enumerate(self._requirements):
            installed = self._requirement_key(requirement) in self._installed
            values = [
                getattr(requirement, "project_name", "Unknown"),
                getattr(requirement, "file_name", "download.bin"),
                f"{getattr(requirement, 'file_size', 0) / (1024 * 1024):.1f} MB" if getattr(requirement, "file_size", 0) > 0 else "—",
                getattr(requirement, "reason", "Manual download required"),
                tr("curseforge.manual.status.installed") if installed else tr("curseforge.manual.status.waiting"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, requirement)
                if column == 3:
                    item.setToolTip(str(value))
                self.table.setItem(row, column, item)
        if self._requirements and self.table.currentRow() < 0:
            self.table.selectRow(0)
        self._update_summary()
        self._update_actions()

    def _update_summary(self) -> None:
        remaining = self.remaining_count
        if self.is_modpack_archive_mode:
            self.summary_label.setText(tr("artifact.manual.modpack_archive_summary", provider=self._provider_name, instance=self._instance_name))
        elif self._instance_name:
            self.summary_label.setText(tr("artifact.manual.summary_instance", provider=self._provider_name, count=remaining, instance=self._instance_name))
        else:
            self.summary_label.setText(tr("artifact.manual.summary", provider=self._provider_name, count=remaining))

    def _selected_requirement(self) -> object | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        requirement = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        return requirement if requirement is not None and hasattr(requirement, "file_name") else None

    def _update_actions(self) -> None:
        requirement = self._selected_requirement()
        self.open_page_button.setEnabled(requirement is not None and bool(self._best_url(requirement)))
        self.add_files_button.setEnabled(self.remaining_count > 0)

    def _open_page(self) -> None:
        requirement = self._selected_requirement()
        if requirement is not None:
            url = self._best_url(requirement)
            if url:
                QDesktopServices.openUrl(QUrl(url))

    @staticmethod
    def _best_url(requirement: object) -> str:
        return str(getattr(requirement, "direct_url", "") or getattr(requirement, "version_url", "") or getattr(requirement, "project_url", "")).strip()

    @staticmethod
    def _requirement_key(requirement: object) -> tuple[str, str, str, str]:
        return (
            str(getattr(requirement, "provider", "unknown")),
            str(getattr(requirement, "project_id", "")),
            str(getattr(requirement, "file_id", getattr(requirement, "version_id", ""))),
            str(getattr(requirement, "managed_path", "")),
        )

    def _select_files(self) -> None:
        if self.is_modpack_archive_mode:
            selected, _ = QFileDialog.getOpenFileName(
                self,
                tr("artifact.manual.add_modpack_file_title", provider=self._provider_name),
                str(Path.home() / "Downloads"),
                tr("artifact.manual.modpack_file_filter"),
            )
            if selected:
                self.files_selected.emit([Path(selected)])
            return
        selected, _ = QFileDialog.getOpenFileNames(
            self,
            tr("artifact.manual.add_files_title", provider=self._provider_name),
            str(Path.home() / "Downloads"),
            tr("artifact.manual.file_filter"),
        )
        if selected:
            self.files_selected.emit([Path(path) for path in selected])

    def retranslate_dynamic(self) -> None:
        title_key = "artifact.manual.modpack_archive_title" if self.is_modpack_archive_mode else "artifact.manual.title"
        title = tr(title_key, provider=self._provider_name)
        self.setWindowTitle(title)
        self.title_label.setText(title)
        self.table.setHorizontalHeaderLabels([
            tr("curseforge.column.name"),
            tr("curseforge.manual.column.file"),
            tr("curseforge.manual.column.size"),
            tr("curseforge.manual.column.reason"),
            tr("curseforge.manual.column.status"),
        ])
        self.open_page_button.setText(tr("artifact.manual.open_link"))
        self.add_files_button.setText(tr("artifact.manual.add_modpack_file") if self.is_modpack_archive_mode else tr("artifact.manual.add_files"))
        self.close_button.setText(tr("common.close"))
        self._render()
