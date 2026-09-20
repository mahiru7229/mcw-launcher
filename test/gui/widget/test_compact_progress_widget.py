import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from mcw_core.api.language.language_manager import language_manager
from src.gui.widget.compact_progress_widget import CompactProgressWidget
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_stage import ProgressStage
from src.models.progress.progress_state import ProgressState


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_compact_progress_widget_initial_state(app):
    widget = CompactProgressWidget()
    assert widget.download_label.text() is not None
    assert widget.install_label.text() is not None
    assert widget.speed_label.text() is not None
    assert "---" in widget.speed_label.text()
    assert widget.progress_bar.value() == 0


def test_compact_progress_widget_download_stage(app):
    widget = CompactProgressWidget()
    event = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_ASSETS,
        message="Downloading assets",
        current=50,
        total=100,
        bytes_per_second=1024 * 1024 * 12.5,
    )
    widget.set_progress_event(event)

    assert "50%" in widget.download_label.text()
    assert "12.5 MB/s" in widget.speed_label.text()
    assert widget.progress_bar.value() == 35  # 50 * 0.7


def test_compact_progress_widget_install_stage(app):
    widget = CompactProgressWidget()
    event = ProgressEvent(
        stage=ProgressStage.INSTALLING_MOD_LOADER,
        message="Installing mod loader",
        current=80,
        total=100,
    )
    widget.set_progress_event(event)

    assert "100%" in widget.download_label.text()
    assert "80%" in widget.install_label.text()
    assert "---" in widget.speed_label.text()
    assert widget.progress_bar.value() == 70 + int(80 * 0.3)


def test_compact_progress_widget_succeeded_stage(app):
    widget = CompactProgressWidget()
    event = ProgressEvent(
        stage=ProgressStage.FINISHED,
        message="Ready",
        state=ProgressState.SUCCEEDED,
    )
    widget.set_progress_event(event)

    assert "100%" in widget.download_label.text()
    assert "100%" in widget.install_label.text()
    assert widget.progress_bar.value() == 100


def test_compact_progress_widget_cancel_button_signal(app):
    widget = CompactProgressWidget()
    emitted = []
    widget.cancel_clicked.connect(lambda: emitted.append(True))
    widget.cancel_button.click()
    assert emitted == [True]


def test_compact_progress_widget_active_lifecycle(app):
    widget = CompactProgressWidget()
    widget.set_active(True)
    assert widget.isVisible() is True

    widget.set_active(False)
    assert widget.isVisible() is False
    assert widget.progress_bar.value() == 0


def test_compact_progress_widget_stage_and_detail(app):
    widget = CompactProgressWidget()
    event = ProgressEvent(
        stage=ProgressStage.CHECKING_MODS,
        message="Checking mod dependencies",
        detail="spawnanimations-v1.11.1-mc1.17-1.21.9-mod.jar",
        state=ProgressState.RUNNING,
    )
    widget.set_progress_event(event)

    assert widget.stage_label.text() != ""
    assert "spawnanimations" in widget.status_label.full_text()
    assert widget.status_label.toolTip() == widget.status_label.full_text()


def test_compact_progress_widget_full_metrics_details(app):
    widget = CompactProgressWidget()
    from src.models.progress.progress_unit import ProgressUnit
    event = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_LIBRARIES,
        message="Downloading libraries",
        current=1024 * 1024 * 10,
        total=1024 * 1024 * 20,
        unit=ProgressUnit.BYTES,
        bytes_per_second=1024 * 1024 * 3.5,
    )
    widget.set_progress_event(event)

    assert "50%" in widget.download_label.text()
    assert "10.0 MB / 20.0 MB" in widget.download_label.text()
    assert "3.5 MB/s" in widget.speed_label.text()


