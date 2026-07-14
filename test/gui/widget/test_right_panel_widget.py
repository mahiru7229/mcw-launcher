import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.gui.widget.right_panel_widget import RightPanelWidget


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_running_instances_are_shown_in_right_panel(app):
    widget = RightPanelWidget()
    running_instances = [
        SimpleNamespace(name="Vanilla", state="running"),
        SimpleNamespace(name="Modded", state="preparing"),
    ]

    widget.set_running_instances(running_instances)

    assert widget.running_count.text() == "2 instances running"
    assert "Vanilla — Running" in widget.running_list.text()
    assert "Modded — Preparing" in widget.running_list.text()


def test_empty_running_instances_state(app):
    widget = RightPanelWidget()

    widget.set_running_instances([])

    assert widget.running_count.text() == "No instances running"
