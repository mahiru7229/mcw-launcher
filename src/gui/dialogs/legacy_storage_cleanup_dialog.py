from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout

from mcw_core.api.language.language_manager import tr
from mcw_core.api.storage.legacy_storage_migration_service import CleanupPlan


def format_bytes(value: int) -> str:
    size = max(0, int(value))
    units = ((1024 ** 4, "TB"), (1024 ** 3, "GB"), (1024 ** 2, "MB"), (1024, "KB"))
    for divisor, unit in units:
        if size >= divisor:
            return f"{size / divisor:.2f} {unit}"
    return f"{size} B"


class LegacyStorageCleanupDialog(QDialog):
    def __init__(self, plan: CleanupPlan, parent=None) -> None:
        super().__init__(parent)
        self._plan = plan
        self._candidate_by_id = {candidate.candidate_id: candidate for candidate in plan.candidates}
        self.setWindowTitle(tr("storage.legacy.dialog.title"))
        self.resize(980, 620)

        layout = QVBoxLayout(self)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels([
            tr("storage.legacy.dialog.item"),
            tr("storage.legacy.dialog.reclaimable"),
            tr("storage.legacy.dialog.safety"),
            tr("storage.legacy.dialog.reason"),
            tr("storage.legacy.dialog.path"),
        ])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree, 1)

        footer = QHBoxLayout()
        self.selected_label = QLabel()
        footer.addWidget(self.selected_label, 1)
        self.cancel_button = QPushButton(tr("storage.legacy.dialog.cancel"))
        self.cancel_button.clicked.connect(self.reject)
        footer.addWidget(self.cancel_button)
        self.clean_button = QPushButton()
        self.clean_button.setObjectName("PrimaryButton")
        self.clean_button.clicked.connect(self.accept)
        footer.addWidget(self.clean_button)
        layout.addLayout(footer)

        self._populate()

    @property
    def plan(self) -> CleanupPlan:
        return self._plan

    def selected_candidate_ids(self) -> tuple[str, ...]:
        selected: list[str] = []
        for index in range(self.tree.topLevelItemCount()):
            category_item = self.tree.topLevelItem(index)
            for child_index in range(category_item.childCount()):
                child = category_item.child(child_index)
                candidate_id = str(child.data(0, Qt.ItemDataRole.UserRole) or "")
                if candidate_id and child.checkState(0) == Qt.CheckState.Checked:
                    selected.append(candidate_id)
        return tuple(selected)

    def _populate(self) -> None:
        self.tree.blockSignals(True)
        self.tree.clear()
        grouped = defaultdict(list)
        for candidate in self._plan.candidates:
            grouped[candidate.category].append(candidate)

        for category, candidates in sorted(grouped.items(), key=lambda item: (-sum(candidate.effective_reclaimable_bytes for candidate in item[1]), item[0])):
            total = sum(candidate.effective_reclaimable_bytes for candidate in candidates)
            category_item = QTreeWidgetItem([self._category_label(category), format_bytes(total), "", "", ""])
            category_item.setFlags(category_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            category_item.setCheckState(0, Qt.CheckState.Checked)
            category_item.setData(0, Qt.ItemDataRole.UserRole + 1, "category")
            self.tree.addTopLevelItem(category_item)
            for candidate in candidates:
                child = QTreeWidgetItem([
                    candidate.path.name or str(candidate.path),
                    format_bytes(candidate.effective_reclaimable_bytes),
                    candidate.safety,
                    candidate.reason,
                    str(candidate.path),
                ])
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setCheckState(0, Qt.CheckState.Checked)
                child.setData(0, Qt.ItemDataRole.UserRole, candidate.candidate_id)
                child.setToolTip(4, str(candidate.path))
                category_item.addChild(child)
            category_item.setExpanded(True)

        self.tree.blockSignals(False)
        for column in range(5):
            self.tree.resizeColumnToContents(column)
        self.summary_label.setText(tr("storage.legacy.dialog.summary", size=format_bytes(self._plan.total_bytes), files=self._plan.file_count, folders=self._plan.directory_count))
        self._update_selected_summary()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0:
            return
        self.tree.blockSignals(True)
        try:
            if item.data(0, Qt.ItemDataRole.UserRole + 1) == "category":
                state = item.checkState(0)
                for index in range(item.childCount()):
                    item.child(index).setCheckState(0, state)
            elif item.parent() is not None:
                parent = item.parent()
                states = {parent.child(index).checkState(0) for index in range(parent.childCount())}
                if states == {Qt.CheckState.Checked}:
                    parent.setCheckState(0, Qt.CheckState.Checked)
                elif states == {Qt.CheckState.Unchecked}:
                    parent.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
        finally:
            self.tree.blockSignals(False)
        self._update_selected_summary()

    def _update_selected_summary(self) -> None:
        selected_ids = set(self.selected_candidate_ids())
        selected = [candidate for candidate in self._plan.candidates if candidate.candidate_id in selected_ids]
        total = sum(candidate.effective_reclaimable_bytes for candidate in selected)
        self.selected_label.setText(tr("storage.legacy.dialog.selected", size=format_bytes(total), count=len(selected)))
        self.clean_button.setText(tr("storage.legacy.dialog.clean", size=format_bytes(total)))
        self.clean_button.setEnabled(bool(selected))

    @staticmethod
    def _category_label(category: str) -> str:
        labels = {
            "loader_staging": "Forge / NeoForge staging",
            "old_launcher_update": "Old launcher updates",
            "unused_minecraft_version_jar": "Unused Minecraft version JARs",
            "orphan_instance_residue": "Incomplete legacy instance folders",
            "unreferenced_provider_content": "Unreferenced provider content",
            "unreferenced_content_store": "Unreferenced shared content",
            "stale_temporary_data": "Stale temporary data",
        }
        return labels.get(category, category.replace("_", " ").title())
