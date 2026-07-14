import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.gui.widget.launch_control_widget import LaunchControlWidget
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_stage import ProgressStage


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_launch_button_text_never_changes(app):
    widget = LaunchControlWidget()
    event = ProgressEvent(stage=ProgressStage.DOWNLOADING_ASSETS, message="Downloading assets...", current=1, total=2)

    assert widget.launch_button.text() == "Launch"

    widget.set_selected_instance(SimpleNamespace(name="Test Instance"))
    widget.set_busy(True)
    widget.set_progress_event(event)
    widget.set_result({"minecraftVersion": "1.21", "javaPath": "javaw.exe"})
    widget.set_failed("Failed")
    widget.set_busy(False)
    widget.reset_progress()

    assert widget.launch_button.text() == "Launch"
