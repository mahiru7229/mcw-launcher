from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QFileDialog

from src.gui.dialogs.modpack_export_dialog import ModpackExportDialog
from src.models.package.modpack_export import ModpackExportOptions


def test_modpack_export_dialog_defaults_to_mrpack(gui_app) -> None:
    dialog = ModpackExportDialog("TestInstance")
    try:
        assert dialog.mrpack_radio.isChecked()
        assert not dialog.provider_radio.isChecked()
        assert not dialog.portable_radio.isChecked()
        assert dialog.options.mode == ModpackExportOptions.MRPACK
    finally:
        dialog.close()


def test_modpack_export_dialog_mode_switching(gui_app) -> None:
    dialog = ModpackExportDialog("TestInstance")
    try:
        dialog.portable_radio.setChecked(True)
        assert dialog.options.mode == ModpackExportOptions.PORTABLE
        assert dialog.portable_mode.isEnabled()

        dialog.provider_radio.setChecked(True)
        assert dialog.options.mode == ModpackExportOptions.PROVIDER_PROFILE
        assert not dialog.portable_mode.isEnabled()

        dialog.mrpack_radio.setChecked(True)
        assert dialog.options.mode == ModpackExportOptions.MRPACK
        assert not dialog.portable_mode.isEnabled()
    finally:
        dialog.close()


def test_modpack_export_dialog_choose_output_mrpack(gui_app, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dialog = ModpackExportDialog("MyPack")
    target_path = str(tmp_path / "custom_output.mrpack")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (target_path, "filter"))

    try:
        dialog._choose_output()
        assert dialog.output_path == Path(target_path)
    finally:
        dialog.close()
