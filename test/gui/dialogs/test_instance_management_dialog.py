from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.dialogs.instance_management_dialog import InstanceManagementDialog


def make_instance(loader=("vanilla", "-1")) -> SimpleNamespace:
    return SimpleNamespace(
        name="Test",
        version_id="1.20.1",
        instance_dir="instances/Test",
        mod_loader=loader,
    )


def test_instance_editor_uses_instance_centered_navigation(gui_app):
    dialog = InstanceManagementDialog()
    dialog.set_instance(make_instance(("neoforge", "47.1.106")))

    assert dialog.navigation.count() == 6
    assert dialog.title_label.text() == "Test"
    assert dialog.manage_mods_button.isEnabled() is True
    assert dialog.export_diagnostics_button.isEnabled() is True


def test_instance_editor_disables_mod_actions_for_vanilla(gui_app):
    dialog = InstanceManagementDialog()
    dialog.set_instance(make_instance())

    assert dialog.manage_mods_button.isEnabled() is False
    assert dialog.open_logs_button.isEnabled() is False
    assert dialog.export_diagnostics_button.isEnabled() is False
