import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.widget.sidebar_widget import SidebarWidget


def test_sidebar_marks_settings_page_with_unsaved_indicator(gui_app):
    sidebar = SidebarWidget()
    button = sidebar._buttons["launcher_settings"]

    sidebar.set_page_dirty("launcher_settings", True)

    assert button.property("unsavedChanges") is True
    assert button.text().startswith("● ")

    sidebar.set_page_dirty("launcher_settings", False)

    assert button.property("unsavedChanges") is False
    assert not button.text().startswith("● ")


def test_sidebar_collapses_to_icon_only_and_restores_dirty_label(gui_app):
    sidebar = SidebarWidget()
    sidebar.set_page_dirty("launcher_settings", True)

    sidebar.set_collapsed_visual(True)

    assert sidebar._buttons["launcher_settings"].text() == ""
    assert sidebar._buttons["launcher_settings"].toolTip()

    sidebar.set_collapsed_visual(False)

    assert sidebar._buttons["launcher_settings"].text().startswith("● ")
    assert sidebar._buttons["launcher_settings"].toolTip() == ""


def test_sidebar_toggle_uses_large_standard_arrow_icon(gui_app):
    sidebar = SidebarWidget()

    assert sidebar._toggle_button.text() == ""
    assert sidebar._toggle_button.icon().isNull() is False
    assert sidebar._toggle_button.iconSize().width() >= 22
    assert sidebar._toggle_button.height() >= 36

    sidebar.set_collapsed_visual(True)

    assert sidebar._toggle_button.icon().isNull() is False
