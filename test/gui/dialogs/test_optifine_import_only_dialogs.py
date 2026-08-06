import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.gui.dialogs.create_instance_dialog import CreateInstanceDialog
from src.gui.dialogs.optifine_dialog import OptiFineDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_create_dialog_uses_import_only_optifine_flow(app, monkeypatch, tmp_path: Path) -> None:
    dialog = CreateInstanceDialog()
    dialog.set_versions([SimpleNamespace(id="1.12.2", type="release")])
    dialog.optifine_checkbox.setChecked(True)
    source = tmp_path / "OptiFine_1.12.2_HD_U_G5.jar"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source), ""))

    dialog._choose_optifine_file()

    assert not hasattr(dialog, "optifine_version_combo")
    assert not hasattr(dialog, "optifine_preview_checkbox")
    assert not hasattr(dialog, "optifine_versions_requested")
    assert dialog.selected_optifine_version().minecraft_version == "1.12.2"
    assert dialog._optifine_source_path == source


def test_create_dialog_rejects_wrong_optifine_minecraft_version(app, monkeypatch, tmp_path: Path) -> None:
    dialog = CreateInstanceDialog()
    dialog.set_versions([SimpleNamespace(id="1.12.2", type="release")])
    dialog.optifine_checkbox.setChecked(True)
    source = tmp_path / "OptiFine_1.20.1_HD_U_I6.jar"
    warnings = []
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source), ""))
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: warnings.append(args[2]))

    dialog._choose_optifine_file()

    assert warnings
    assert dialog._optifine_source_path is None
    assert dialog.selected_optifine_version() is None


def test_manage_dialog_has_no_online_version_controls(app) -> None:
    dialog = OptiFineDialog()

    assert not hasattr(dialog, "version_combo")
    assert not hasattr(dialog, "preview_checkbox")
    assert not hasattr(dialog, "refresh_button")
    assert not hasattr(dialog, "versions_requested")
