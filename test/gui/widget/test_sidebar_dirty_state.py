import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.widget.sidebar_widget import SidebarWidget


def test_sidebar_marks_settings_page_with_unsaved_indicator(gui_app):
    sidebar = SidebarWidget()
    button = sidebar._buttons["instance_settings"]

    sidebar.set_page_dirty("instance_settings", True)

    assert button.property("unsavedChanges") is True
    assert button.text().startswith("● ")

    sidebar.set_page_dirty("instance_settings", False)

    assert button.property("unsavedChanges") is False
    assert not button.text().startswith("● ")
