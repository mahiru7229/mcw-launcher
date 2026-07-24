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
        block_launch_on_modrinth_failure=True,
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
        "show_static_text": True,
        "modrinth_include_beta": False,
        "modrinth_include_alpha": False,
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
