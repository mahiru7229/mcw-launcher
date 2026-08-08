from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.dialogs.instance_management_dialog import AdvancedInstanceManagerDialog, InstanceManagementDialog
from src.gui.pages.instances_page import InstancesPage
from mcw_core.models import InstanceRuntimeProfile


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

    assert dialog.navigation.count() == 7
    assert dialog.title_label.text() == "Test"
    assert dialog.manage_mods_button.isEnabled() is True
    assert dialog.export_diagnostics_button.isEnabled() is True


def test_instance_editor_disables_mod_actions_for_vanilla(gui_app):
    dialog = InstanceManagementDialog()
    dialog.set_instance(make_instance())

    assert dialog.manage_mods_button.isEnabled() is False
    assert dialog.open_logs_button.isEnabled() is False
    assert dialog.export_diagnostics_button.isEnabled() is False


def test_advanced_instance_manager_dialog_is_resizable_for_compact_screens(gui_app):
    dialog = AdvancedInstanceManagerDialog(InstancesPage())

    assert dialog.minimumWidth() == 520
    assert dialog.minimumHeight() == 420
    assert dialog.maximumWidth() > dialog.width()
    assert dialog.maximumHeight() > dialog.height()


def test_instance_editor_overview_shows_library_metadata(gui_app):
    dialog = InstanceManagementDialog()
    instance = make_instance(("forge", "47.4.0"))
    instance.favorite = True
    instance.group = "Modpacks"
    instance.tags = ("heavy", "automation")

    dialog.set_instance(instance)

    assert "Favorite" in dialog.overview_library_detail.text()
    assert "Modpacks" in dialog.overview_library_detail.text()
    assert "heavy" in dialog.overview_library_detail.text()


def test_instance_editor_runtime_page_selects_compatible_java(gui_app, tmp_path):
    dialog = InstanceManagementDialog()
    dialog.set_instance(make_instance(("forge", "47.2.0")))
    profile = InstanceRuntimeProfile(
        instance_name="Test",
        minecraft_version="1.20.1",
        loader_name="forge",
        loader_version="47.2.0",
        required_java_major=17,
        managed_java_major=17,
        java_automatic=True,
        configured_java_path="",
    )
    java17 = tmp_path / "java17" / "bin" / "javaw.exe"
    java21 = tmp_path / "java21" / "bin" / "javaw.exe"
    dialog.set_runtime_profile(profile)
    dialog.set_java_installations([
        SimpleNamespace(major_version=17, version_string="17.0.12", vendor="Temurin", architecture="amd64", executable=java17, source="program_files", valid=True),
        SimpleNamespace(major_version=21, version_string="21.0.4", vendor="Temurin", architecture="amd64", executable=java21, source="program_files", valid=True),
    ])

    assert "Java 17" in dialog.runtime_required_label.text()
    assert dialog.runtime_java_combo.count() == 2  # Automatic + compatible Java 17 only.
    assert dialog.runtime_java_combo.itemData(0) == ""
    assert dialog.runtime_java_combo.itemData(1) == str(java17)


def test_instance_editor_runtime_actions_emit_current_instance(gui_app):
    dialog = InstanceManagementDialog()
    dialog.set_instance(make_instance(("forge", "47.2.0")))
    dialog.set_runtime_profile(InstanceRuntimeProfile(
        instance_name="Test", minecraft_version="1.20.1", loader_name="forge", loader_version="47.2.0",
        required_java_major=17, managed_java_major=17, java_automatic=True, configured_java_path="",
    ))
    applied = []
    installs = []
    scans = []
    dialog.runtime_apply_requested.connect(lambda name, path: applied.append((name, path)))
    dialog.runtime_install_requested.connect(installs.append)
    dialog.runtime_scan_requested.connect(lambda: scans.append(True))

    dialog.runtime_apply_button.click()
    dialog.runtime_install_button.click()
    dialog.runtime_scan_button.click()

    assert applied == [("Test", "")]
    assert installs == [17]
    assert scans == [True]
