from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")

from src.gui.dialogs.curseforge_manual_download_dialog import CurseForgeManualDownloadDialog


def test_manual_dialog_disables_add_files_while_import_is_running(gui_app):
    dialog = CurseForgeManualDownloadDialog()
    dialog.set_requirements([SimpleNamespace(provider="curseforge", project_id=1, file_id=2, managed_path="mods/example.jar", file_name="example.jar")])

    assert dialog.add_files_button.isEnabled() is True
    dialog.set_import_busy(True)
    assert dialog.add_files_button.isEnabled() is False
    dialog.set_import_busy(False)
    assert dialog.add_files_button.isEnabled() is True
