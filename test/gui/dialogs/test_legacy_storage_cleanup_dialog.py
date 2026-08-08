from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from src.core.storage.legacy_storage_migration_service import CleanupCandidate, CleanupPlan
from src.gui.dialogs.legacy_storage_cleanup_dialog import LegacyStorageCleanupDialog


def _candidate(candidate_id: str, path: Path, category: str, size: int, *, files: int = 1, directories: int = 0) -> CleanupCandidate:
    return CleanupCandidate(
        candidate_id=candidate_id,
        path=path,
        category=category,
        reason=f"Reason for {candidate_id}",
        safety="safe",
        size_bytes=size,
        file_count=files,
        directory_count=directories,
    )


def test_cleanup_dialog_shows_exact_items_category_totals_and_grand_total(gui_app, tmp_path: Path) -> None:
    plan = CleanupPlan((
        _candidate("stage", tmp_path / "forge-stage", "loader_staging", 1024 * 1024, files=4, directories=2),
        _candidate("update", tmp_path / "v1.0.0", "old_launcher_update", 2 * 1024 * 1024, files=1, directories=1),
    ))

    dialog = LegacyStorageCleanupDialog(plan)

    assert dialog.tree.topLevelItemCount() == 2
    assert "3.00 MB" in dialog.summary_label.text()
    assert "5" in dialog.summary_label.text()
    assert "3" in dialog.summary_label.text()
    assert set(dialog.selected_candidate_ids()) == {"stage", "update"}
    paths = []
    reasons = []
    for category_index in range(dialog.tree.topLevelItemCount()):
        category = dialog.tree.topLevelItem(category_index)
        for child_index in range(category.childCount()):
            child = category.child(child_index)
            paths.append(child.text(4))
            reasons.append(child.text(3))
    assert str(tmp_path / "forge-stage") in paths
    assert str(tmp_path / "v1.0.0") in paths
    assert all(reasons)


def test_cleanup_dialog_labels_unused_version_jar_category_explicitly(gui_app, tmp_path: Path) -> None:
    plan = CleanupPlan((
        _candidate("version-jar", tmp_path / "1.6.4.jar", "unused_minecraft_version_jar", 8 * 1024 * 1024),
    ))

    dialog = LegacyStorageCleanupDialog(plan)

    assert dialog.tree.topLevelItem(0).text(0) == "Unused Minecraft version JARs"
    assert "8.00 MB" in dialog.tree.topLevelItem(0).text(1)


def test_cleanup_dialog_updates_selected_total_when_item_is_unchecked(gui_app, tmp_path: Path) -> None:
    plan = CleanupPlan((
        _candidate("one", tmp_path / "one", "loader_staging", 1024 * 1024),
        _candidate("two", tmp_path / "two", "loader_staging", 2 * 1024 * 1024),
    ))
    dialog = LegacyStorageCleanupDialog(plan)
    category = dialog.tree.topLevelItem(0)

    category.child(1).setCheckState(0, Qt.CheckState.Unchecked)

    assert len(dialog.selected_candidate_ids()) == 1
    assert "1.00 MB" in dialog.selected_label.text() or "2.00 MB" in dialog.selected_label.text()
    assert dialog.clean_button.isEnabled() is True
