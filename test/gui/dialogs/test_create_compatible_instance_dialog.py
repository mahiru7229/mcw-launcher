import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.dialogs.create_compatible_instance_dialog import CreateCompatibleInstanceDialog
from src.models.modrinth.version import ModrinthFile, ModrinthVersion


def _version() -> ModrinthVersion:
    return ModrinthVersion(
        version_id="version",
        project_id="project",
        name="Version",
        version_number="1.0.0",
        version_type="release",
        game_versions=("1.21.1", "1.20.1"),
        loaders=("fabric",),
        files=(ModrinthFile(url="https://example.invalid/mod.jar", filename="mod.jar", sha1="a", sha512="b", size=1, primary=True),),
    )


def test_create_dialog_lists_supported_versions_and_suggests_name(gui_app, monkeypatch):
    monkeypatch.setattr("src.gui.dialogs.create_compatible_instance_dialog.InstanceManager.next_available_name", lambda value: f"{value} Ready")
    dialog = CreateCompatibleInstanceDialog(_version(), "fabric")

    assert dialog.game_version_combo.count() == 2
    assert dialog.game_version == "1.21.1"
    assert dialog.loader == "fabric"
    assert "Fabric" in dialog.instance_name
    assert dialog.create_button.isEnabled()
