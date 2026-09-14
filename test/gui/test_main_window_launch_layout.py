import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.gui.display_profile import select_display_profile
from src.gui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_main_window_layout_has_no_bottom_launch_control(app, monkeypatch):
    monkeypatch.setattr(MainWindow, "_initialize_data", lambda self: None)
    monkeypatch.setattr(MainWindow, "_detect_display_profile", lambda self: select_display_profile(1920, 1080))
    window = MainWindow()

    # Verify launch_control is not visible in layout
    assert window.launch_control.isVisible() is False
    # Verify content_stack is in center layout
    assert window.content_stack is not None
    assert window.instances_page is not None
    # Verify instances_page cancel_launch_requested is connected to launch_controller.cancel
    assert hasattr(window.instances_page, "cancel_launch_requested")
