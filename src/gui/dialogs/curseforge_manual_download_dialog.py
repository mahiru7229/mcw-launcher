import re
import time
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from mcw_core.api.language.language_manager import tr
from mcw_core.api.curseforge.curseforge_links import best_manual_download_url
from src.gui.window_sizing import resize_dialog_to_screen


class CurseForgeManualDownloadDialog(QDialog):
    files_selected = Signal(object)
    auto_files_selected = Signal(object)
    cancelled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._requirements: list[object] = []
        self._installed: set[tuple[str, str, str, str]] = set()
        self._scanned_files: set[Path] = set()
        self._instance_name = ""
        self._provider_name = "CurseForge"
        self._import_busy = False
        self._scan_start_time = time.time()
        self.last_files_auto_detected = False

        self._downloads_timer = QTimer(self)
        self._downloads_timer.setInterval(1500)
        self._downloads_timer.timeout.connect(self._scan_downloads_folder)

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
        self.auto_detect_checkbox = QCheckBox()
        self.auto_detect_checkbox.setChecked(True)
        self.cancel_button = QPushButton()
        self.cancel_button.setObjectName("SecondaryButton")
        self.close_button = QPushButton()

        self.open_page_button.clicked.connect(self._open_page)
        self.add_files_button.clicked.connect(self._select_files)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.close_button.clicked.connect(self._on_close_clicked)

        actions.addWidget(self.open_page_button)
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.auto_detect_checkbox)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.close_button)
        root.addLayout(actions)
        self.retranslate_dynamic()

    def set_instance_context(self, instance_name: str, _instance_dir: Path | str | None = None) -> None:
        self._instance_name = str(instance_name or "")
        self._update_summary()
        self._update_actions()

    def set_requirements(self, requirements: tuple[object, ...] | list[object]) -> None:
        self._requirements = list(requirements)
        providers = {str(getattr(item, "provider", "manual") or "manual").strip().casefold() for item in self._requirements}
        provider = next(iter(providers), "manual") if len(providers) == 1 else "mixed"
        self._provider_name = {"modrinth": "Modrinth", "curseforge": "CurseForge"}.get(provider, "MCWPack")
        self._installed.clear()
        self._scanned_files.clear()
        self._scan_start_time = time.time()
        self.last_files_auto_detected = False
        self.retranslate_dynamic()

    def mark_installed(self, requirement: object) -> None:
        self._installed.add(self._requirement_key(requirement))
        self._render()
        if self.remaining_count == 0:
            self._downloads_timer.stop()
            self.accept()

    def set_import_busy(self, busy: bool) -> None:
        self._import_busy = bool(busy)
        self._update_actions()

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
        self.add_files_button.setEnabled(self.remaining_count > 0 and not self._import_busy)

    def _open_page(self) -> None:
        requirement = self._selected_requirement()
        if requirement is not None:
            url = self._best_url(requirement)
            if url:
                QDesktopServices.openUrl(QUrl(url))

    @staticmethod
    def _best_url(requirement: object) -> str:
        return best_manual_download_url(requirement)

    @staticmethod
    def _requirement_key(requirement: object) -> tuple[str, str, str, str]:
        return (
            str(getattr(requirement, "provider", "unknown")),
            str(getattr(requirement, "project_id", "")),
            str(getattr(requirement, "file_id", getattr(requirement, "version_id", ""))),
            str(getattr(requirement, "managed_path", "")),
        )

    def _select_files(self) -> None:
        if self._import_busy:
            return
        self.last_files_auto_detected = False
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

    def _scan_downloads_folder(self) -> None:
        if not self.auto_detect_checkbox.isChecked() or self._import_busy or self.remaining_count == 0:
            return
        downloads_dir = Path.home() / "Downloads"
        if not downloads_dir.is_dir():
            return

        threshold = (self._scan_start_time or time.time()) - 3.0
        allowed_exts = {".mrpack", ".zip"} if self.is_modpack_archive_mode else {".jar", ".zip"}
        candidates: list[Path] = []
        try:
            for entry in downloads_dir.iterdir():
                if not entry.is_file():
                    continue
                if entry.suffix.casefold() in {".crdownload", ".part", ".tmp", ".download", ".aria2"}:
                    continue
                if entry.suffix.casefold() not in allowed_exts:
                    continue
                if entry in self._scanned_files:
                    continue
                try:
                    stat = entry.stat()
                    if stat.st_mtime < threshold:
                        continue
                    if stat.st_size == 0:
                        continue
                    # Ensure file is not write-locked by browser
                    with entry.open("rb") as test_f:
                        test_f.read(1)
                except OSError:
                    continue

                if self._could_match_any_requirement(entry):
                    candidates.append(entry)
                    self._scanned_files.add(entry)
        except OSError:
            return

        if candidates and not self._import_busy:
            self.last_files_auto_detected = True
            self.auto_files_selected.emit(candidates)
            self.files_selected.emit(candidates)

    def _could_match_any_requirement(self, file_path: Path) -> bool:
        clean_stem = re.sub(r"\s*(?:\(\d+\)|_\d+|\s-\sCopy|\sCopy)$", "", file_path.stem, flags=re.IGNORECASE)
        clean_name_cf = (clean_stem + file_path.suffix).casefold()
        file_name_cf = file_path.name.casefold()
        clean_stem_cf = clean_stem.casefold()

        for req in self.remaining_requirements:
            req_file_cf = str(getattr(req, "file_name", "")).casefold()
            req_proj_cf = str(getattr(req, "project_name", "")).casefold()
            req_stem_cf = Path(req_file_cf).stem.casefold()

            if clean_name_cf == req_file_cf or file_name_cf == req_file_cf:
                return True
            if clean_stem_cf == req_stem_cf:
                return True

            req_prefix = re.split(r"[-_vV\d]", req_stem_cf)[0].casefold()
            src_prefix = re.split(r"[-_vV\d]", clean_stem_cf)[0].casefold()
            if req_prefix and src_prefix and len(req_prefix) >= 3 and req_prefix == src_prefix:
                return True
            if (len(clean_stem_cf) >= 3 and clean_stem_cf in req_proj_cf) or (len(req_prefix) >= 3 and req_prefix in req_proj_cf):
                return True

        return False

    def _on_cancel_clicked(self) -> None:
        self._downloads_timer.stop()
        self.cancelled.emit()
        self.reject()

    def _on_close_clicked(self) -> None:
        self._downloads_timer.stop()
        if self.remaining_count > 0:
            self.cancelled.emit()
            self.reject()
        else:
            self.accept()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not getattr(self, "_scan_start_time", 0):
            self._scan_start_time = time.time()
        self._downloads_timer.start()

    def hideEvent(self, event) -> None:
        self._downloads_timer.stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        self._downloads_timer.stop()
        if self.remaining_count > 0:
            self.cancelled.emit()
        super().closeEvent(event)

    def reject(self) -> None:
        self._downloads_timer.stop()
        if self.remaining_count > 0:
            self.cancelled.emit()
        super().reject()

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
        self.auto_detect_checkbox.setText(tr("artifact.manual.auto_detect"))
        self.cancel_button.setText(tr("artifact.manual.cancel_launch"))
        self.close_button.setText(tr("common.close"))
        self._render()
