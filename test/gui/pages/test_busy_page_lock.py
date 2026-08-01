import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.pages.account_page import AccountPage
from src.gui.pages.instances_page import InstancesPage
from src.gui.pages.launcher_settings_page import LauncherSettingsPage


@pytest.mark.parametrize("page_factory", [AccountPage, InstancesPage, LauncherSettingsPage])
def test_busy_pages_remain_enabled_and_scrollable(gui_app, page_factory):
    page = page_factory()

    page.set_busy(True)

    assert page.isEnabled() is True
    assert page.viewport().isEnabled() is True
    assert page.interaction_locked is True
    assert page._busy_overlay.isHidden() is False

    page.set_busy(False)

    assert page.interaction_locked is False
    assert page._busy_overlay.isHidden() is True
