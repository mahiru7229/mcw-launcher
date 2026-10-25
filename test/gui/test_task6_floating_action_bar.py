from __future__ import annotations

import os
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.gui.pages.instance_settings_page import InstanceSettingsPage
from src.gui.pages.launcher_settings_page import LauncherSettingsPage


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_launcher_settings_reset_button_in_card_and_emits(qapp) -> None:
    page = LauncherSettingsPage()
    assert hasattr(page, "reset_defaults_card")
    assert hasattr(page, "reset_button")
    assert page.reset_button.parentWidget() is page.reset_defaults_card

    emitted = []
    page.reset_requested.connect(lambda: emitted.append(True))
    page.reset_button.click()
    assert emitted == [True]


def test_launcher_settings_floating_action_bar_parent_and_dirty(qapp) -> None:
    page = LauncherSettingsPage()
    assert hasattr(page, "floating_action_bar")
    assert page.floating_action_bar.parentWidget() is page.viewport()
    assert hasattr(page, "discard_button")
    assert hasattr(page, "save_button")
    assert hasattr(page, "unsaved_label")

    # Initial clean state
    page._saved_data = page.form_data()
    page._set_dirty(False)
    assert page.discard_button.isEnabled() is False
    assert page.floating_action_bar.property("unsavedChanges") is False

    # Dirty state
    page._set_dirty(True)
    assert page.discard_button.isEnabled() is True
    assert page.floating_action_bar.property("unsavedChanges") is True

    # Clicking discard resets dirty
    page.discard_button.click()
    assert page._dirty is False
    assert page.discard_button.isEnabled() is False


def test_instance_settings_floating_action_bar_parent_and_dirty(qapp) -> None:
    page = InstanceSettingsPage()
    assert hasattr(page, "floating_action_bar")
    assert page.floating_action_bar.parentWidget() is page.viewport()
    assert hasattr(page, "discard_button")
    assert hasattr(page, "save_button")
    assert hasattr(page, "unsaved_label")

    page._saved_data = page.form_data()
    page._set_dirty(False)
    assert page.discard_button.isEnabled() is False
    assert page.floating_action_bar.property("unsavedChanges") is False

    page._set_dirty(True)
    assert page.discard_button.isEnabled() is True
    assert page.floating_action_bar.property("unsavedChanges") is True

    page.discard_button.click()
    assert page._dirty is False
    assert page.discard_button.isEnabled() is False
