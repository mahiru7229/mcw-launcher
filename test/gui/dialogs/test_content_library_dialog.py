from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.dialogs.content_library_dialog import ContentLibraryDialog
from src.models.content.installed_content import InstalledContentItem, InstalledContentLibrary
from src.models.instance.instance import Instance


@pytest.fixture
def instance(tmp_path: Path) -> Instance:
    root = tmp_path / "Library Dialog"
    root.mkdir()
    return Instance(instance_id="library-dialog", name="Library Dialog", version_id="1.21.1", instance_dir=root, mod_loader=("fabric", "0.16.0"))


def item(item_id: str, content_type: str, name: str, *, provider: str = "local", status: str = "ready", pinned: bool = False, removable: bool = True, toggleable: bool = True) -> InstalledContentItem:
    return InstalledContentItem(
        item_id=item_id,
        content_type=content_type,
        name=name,
        version="1.0",
        provider=provider,
        project_id="project" if provider != "local" else "",
        version_id="version" if provider != "local" else "",
        file_id="",
        file_name=f"{name.casefold()}.zip" if content_type != "mod" else f"{name.casefold()}.jar",
        target_path=f"mods/{name.casefold()}.jar" if content_type == "mod" else f"minecraft/resourcepacks/{name.casefold()}.zip",
        enabled=status != "disabled",
        managed_by_modpack=False,
        source_pack_provider="",
        size=1024,
        sha1="a" * 40,
        sha512="b" * 128,
        project_url="https://modrinth.com/mod/example" if provider == "modrinth" else "",
        status=status,
        pinned=pinned,
        ignored_update=False,
        toggleable=toggleable,
        removable=removable,
    )


def test_content_library_is_screen_fitted_and_filters_items(gui_app, instance: Instance):
    dialog = ContentLibraryDialog()
    dialog.set_instance(instance)
    library = InstalledContentLibrary(instance_name=instance.name, items=(
        item("mod:1", "mod", "Sodium", provider="modrinth", pinned=True),
        item("pack:1", "resourcepack", "Pretty", status="disabled"),
        item("modpack:1", "modpack", "Pack", provider="ftb", status="pending", removable=False, toggleable=False),
    ))

    dialog.set_library(library)

    assert dialog.width() > dialog.height()
    assert dialog.maximumWidth() == dialog.width()
    assert dialog.maximumHeight() == dialog.height()
    assert dialog.table.rowCount() == 3
    assert "3" in dialog.summary_label.text()

    dialog.search_input.setText("Sodium")
    assert sum(not dialog.table.isRowHidden(row) for row in range(dialog.table.rowCount())) == 1


def test_modpack_row_is_read_only_in_content_library(gui_app, instance: Instance):
    dialog = ContentLibraryDialog()
    dialog.set_instance(instance)
    dialog.set_library(InstalledContentLibrary(instance_name=instance.name, items=(
        item("modpack:1", "modpack", "FTB Pack", provider="ftb", status="pending", removable=False, toggleable=False),
    )))

    dialog.table.selectRow(0)

    assert dialog.manage_button.isEnabled() is False
    assert dialog.enable_button.isEnabled() is False
    assert dialog.disable_button.isEnabled() is False
    assert dialog.remove_button.isEnabled() is False
    assert dialog.pin_button.isEnabled() is True
