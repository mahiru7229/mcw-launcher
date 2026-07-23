import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from pathlib import Path

from src.gui.dialogs.compatible_instance_dialog import CompatibleInstanceDialog
from src.models.instance.instance import Instance
from src.models.modrinth.version import ModrinthFile, ModrinthVersion


def _instance(name: str, game_version: str, loader: str) -> Instance:
    return Instance(instance_id=name.lower(), name=name, version_id=game_version, instance_dir=Path(name), mod_loader=(loader, "test"))


def _version() -> ModrinthVersion:
    return ModrinthVersion(
        version_id="version",
        project_id="project",
        name="Version",
        version_number="1.0.0",
        version_type="release",
        game_versions=("1.20.1", "1.21.1"),
        loaders=("fabric",),
        files=(ModrinthFile(url="https://example.invalid/mod.jar", filename="mod.jar", sha1="a", sha512="b", size=1, primary=True),),
    )


def test_dialog_only_renders_compatible_instances(gui_app, monkeypatch):
    monkeypatch.setattr("src.gui.dialogs.compatible_instance_dialog.InstanceRunLock.is_active", lambda _instance: False)
    dialog = CompatibleInstanceDialog(
        _version(),
        "fabric",
        [_instance("Correct", "1.21.1", "fabric"), _instance("Wrong", "1.21.1", "forge")],
    )

    assert dialog.table.rowCount() == 1
    assert dialog.table.item(0, 0).text() == "Correct"
    assert dialog.install_button.isEnabled()


def test_dialog_keeps_create_option_available_without_compatible_instances(gui_app, monkeypatch):
    monkeypatch.setattr("src.gui.dialogs.compatible_instance_dialog.InstanceRunLock.is_active", lambda _instance: False)
    dialog = CompatibleInstanceDialog(_version(), "fabric", [_instance("Wrong", "1.21.1", "forge")])

    assert dialog.table.rowCount() == 0
    assert dialog.install_button.isEnabled() is False
    assert dialog.create_button.isEnabled() is True
