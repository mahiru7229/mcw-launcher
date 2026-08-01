import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QSizePolicy

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


def test_launcher_settings_can_request_managed_java_install(gui_app):
    page = LauncherSettingsPage()
    requested = []
    page.install_java_requested.connect(requested.append)

    index = page.java_install_combo.findData(21)
    page.java_install_combo.setCurrentIndex(index)
    page.java_install_button.click()

    assert requested == [21]
    assert [page.java_install_combo.itemData(index) for index in range(page.java_install_combo.count())] == [8, 17, 21, 25]

    page.set_latest_java_release(26)
    latest_index = page.java_install_combo.findData(26)
    page.java_install_combo.setCurrentIndex(latest_index)
    page.java_install_button.click()

    assert requested == [21, 26]
    assert [page.java_install_combo.itemData(index) for index in range(page.java_install_combo.count())] == [8, 17, 21, 25, 26]
    assert "26" in page.java_install_combo.itemText(latest_index)


def test_instance_defaults_card_keeps_text_compact_and_places_extra_space_before_button(gui_app):
    page = LauncherSettingsPage()

    assert page.instance_defaults_card.title_label.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Fixed
    assert page.instance_defaults_card.subtitle_label.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Fixed
    assert page.instance_defaults_summary.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Fixed

    button_index = page.instance_defaults_card.layout.indexOf(page.edit_instance_defaults_button)
    spacer = page.instance_defaults_card.layout.itemAt(button_index - 1).spacerItem()
    assert spacer is not None
    assert spacer.expandingDirections()
