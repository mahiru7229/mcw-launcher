import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.dialogs.mod_manager_dialog import ModManagerDialog
from src.models.instance.instance import Instance
from src.models.mod.mod_info import ModInfo


def test_dialog_renders_fabric_mods(gui_app, tmp_path):
    instance = Instance(instance_id="id", name="Fabric", version_id="1.20.1", instance_dir=tmp_path, mod_loader=("fabric", "0.19.3"))
    dialog = ModManagerDialog()

    try:
        dialog.set_instance(instance)
        dialog.set_mods([ModInfo(path=tmp_path / "example.jar", file_name="example.jar", enabled=True, mod_id="example", name="Example", version="1.0")])

        assert dialog.add_button.isEnabled()
        assert dialog.table.rowCount() == 1
        assert dialog.table.item(0, 1).text() == "Example"
    finally:
        dialog.close()
        dialog.deleteLater()
        gui_app.processEvents()
