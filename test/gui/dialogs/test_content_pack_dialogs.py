from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QSizePolicy

from src.gui.dialogs.content_pack_browser_dialog import ContentPackBrowserDialog
from src.gui.dialogs.content_pack_manager_dialog import ContentPackManagerDialog
from src.models.content.content_pack import ContentPackEntry
from src.models.instance.instance import Instance


@pytest.fixture
def instance(tmp_path: Path) -> Instance:
    instance_dir = tmp_path / "Visual Pack"
    (instance_dir / "minecraft").mkdir(parents=True)
    return Instance(instance_id="visual", name="Visual Pack", version_id="1.21.1", instance_dir=instance_dir, mod_loader=("fabric", "0.16.0"))


def test_content_browsers_are_wide_and_hide_long_descriptions_by_default(gui_app, instance: Instance):
    for kind in ("resourcepack", "shader"):
        dialog = ContentPackBrowserDialog(kind)
        dialog.set_instance(instance)

        assert dialog.content_type == kind
        assert dialog.width() > dialog.height()
        assert dialog.width() <= 1240
        assert dialog.height() <= 620
        assert dialog.maximumWidth() == dialog.width()
        assert dialog.maximumHeight() == dialog.height()
        assert dialog.detail_panel.description_visible is False
        assert dialog.version_combo.sizePolicy().horizontalPolicy() is QSizePolicy.Policy.Expanding
        assert dialog.provider_combo.itemData(0) == "modrinth"


def test_project_details_compact_long_contributors_and_metadata(gui_app):
    dialog = ContentPackBrowserDialog("resourcepack")
    contributors = ", ".join(f"Contributor {index}" for index in range(12))
    versions = tuple(f"1.{index}" for index in range(30))

    dialog.detail_panel.set_project(
        token="long-project",
        provider="Modrinth",
        title="Long metadata project",
        author=contributors,
        summary="Summary",
        description="Description",
        icon_url="",
        web_url="https://modrinth.com/resourcepack/example",
        metadata={"Minecraft": versions, "Contributors": tuple(f"Person {index}" for index in range(20))},
    )

    assert "(+7)" in dialog.detail_panel.provider_label.text()
    assert contributors not in dialog.detail_panel.provider_label.text()
    assert contributors in dialog.detail_panel.provider_label.toolTip()
    assert "(+22)" in dialog.detail_panel.metadata_label.text()
    assert "1.29" not in dialog.detail_panel.metadata_label.text()
    assert dialog.detail_panel.metadata_label.maximumHeight() == 132


def test_content_manager_tracks_resource_and_shader_tabs(gui_app, instance: Instance):
    dialog = ContentPackManagerDialog()
    dialog.set_instance(instance)
    resource_entry = ContentPackEntry(
        entry_id="resource",
        content_type="resourcepack",
        provider="modrinth",
        project_id="project",
        version_id="version",
        file_id="file.zip",
        project_name="Pretty Pack",
        version_number="1.0",
        pack_format=34,
        pack_description="Pretty",
        file_name="pretty.zip",
        target_path="minecraft/resourcepacks/pretty.zip",
        sha1="a" * 40,
        sha512="b" * 128,
        size=12,
        source_url="https://cdn.example/pretty.zip",
        project_url="https://modrinth.com/resourcepack/pretty",
        installed_at="2026-08-03T00:00:00+00:00",
        enabled=True,
    )

    dialog.set_entries(instance.name, "resourcepack", [resource_entry])

    assert dialog.tabs.count() == 2
    assert dialog._tables["resourcepack"].rowCount() == 1
    assert dialog.selected_entry() == resource_entry
    assert dialog.enable_button.isEnabled() is True
