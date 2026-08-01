import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.pages.instance_settings_page import InstanceSettingsPage
from src.gui.pages.launcher_settings_page import LauncherSettingsPage


def _instance_settings() -> SimpleNamespace:
    return SimpleNamespace(
        java_path="",
        min_memory=1024,
        max_memory=2048,
        width=1280,
        height=720,
        fullscreen=False,
        offline_multiplayer_enabled=False,
        lan_auth_mode="microsoft_only",
        lan_connection_provider="manual",
        modrinth_failure_policy="inherit",
        curseforge_failure_policy="inherit",
        jvm_arguments=[],
        game_arguments=[],
    )


def _launcher_settings() -> dict:
    return {
        "start_page": "home",
        "show_snapshots": False,
        "debug_mode": False,
        "remember_window_size": True,
        "language": "en-US",
        "auto_check_updates": True,
        "update_channel": "stable",
        "tester_mode": False,
        "theme": "mcw-default",
        "show_static_text": False,
        "accent_mode": "theme",
        "accent_color": "#8ed35b",
        "modrinth_include_beta": False,
        "modrinth_include_alpha": False,
        "block_launch_on_modrinth_failure": True,
        "block_launch_on_curseforge_failure": True,
        "curseforge_gateway_urls": ("https://one.example/api/curseforge",),
        "download_limit_mbps": 0.0,
    }


def test_instance_settings_highlights_unsaved_changes_and_can_discard(gui_app):
    page = InstanceSettingsPage(total_memory_mb=8192)
    page.set_settings("Pack", _instance_settings())

    page.fullscreen.setChecked(True)

    assert page.is_dirty is True
    assert page.unsaved_label.isHidden() is False
    assert page.save_button.property("unsavedChanges") is True

    page.discard_changes()

    assert page.is_dirty is False
    assert page.fullscreen.isChecked() is False


def test_launcher_settings_highlights_unsaved_changes_and_can_discard(gui_app):
    page = LauncherSettingsPage()
    page.set_settings(_launcher_settings())

    page.show_snapshots.setChecked(True)

    assert page.is_dirty is True
    assert page.unsaved_label.isHidden() is False
    assert page.save_button.property("unsavedChanges") is True

    page.discard_changes()

    assert page.is_dirty is False
    assert page.show_snapshots.isChecked() is False


def test_launcher_settings_has_five_masked_gateway_slots(gui_app):
    from PySide6.QtWidgets import QLineEdit

    page = LauncherSettingsPage()
    page.set_settings(_launcher_settings())

    assert len(page.curseforge_gateway_inputs) == 5
    assert all(field.echoMode() == QLineEdit.EchoMode.Password for field in page.curseforge_gateway_inputs)
    assert page.curseforge_gateway_inputs[0].text() == "https://one.example/api/curseforge"
    assert page.form_data()["curseforge_gateway_urls"][1:] == ["", "", "", ""]


def test_launcher_settings_round_trips_motion_mode(gui_app):
    page = LauncherSettingsPage()
    settings = _launcher_settings()
    settings["motion_mode"] = "reduced"

    page.set_settings(settings)

    assert page.current_motion_mode() == "reduced"
    assert page.form_data()["motion_mode"] == "reduced"


def test_launcher_settings_round_trips_custom_accent(gui_app):
    page = LauncherSettingsPage()
    settings = _launcher_settings()
    settings["accent_mode"] = "custom"
    settings["accent_color"] = "#b26cff"

    page.set_settings(settings)

    assert page.current_accent_mode() == "custom"
    assert page.current_accent_color() == "#b26cff"
    assert page.form_data()["accent_mode"] == "custom"
    assert page.form_data()["accent_color"] == "#b26cff"
