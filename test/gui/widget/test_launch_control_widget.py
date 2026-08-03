import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QSizePolicy

from src.gui.widget.launch_control_widget import LaunchControlWidget
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_stage import ProgressStage


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_selecting_instance_before_launch_does_not_require_prior_state_change(app):
    widget = LaunchControlWidget()

    widget.set_selected_instance(SimpleNamespace(name="Pack"))

    assert widget.launch_button.text() == "Launch"
    assert widget.launch_button.isEnabled() is True


def test_launch_controls_support_pause_resume_and_cancel(app):
    widget = LaunchControlWidget()
    widget.show()

    assert widget.launch_button.text() == "Launch"
    assert widget.cancel_button.isVisible() is False

    widget.set_busy(True)
    assert widget.launch_button.isEnabled() is False

    widget.set_launch_active(True)
    assert widget.launch_button.text() == "Pause"
    assert widget.cancel_button.isVisible() is True
    assert widget.launch_button.isEnabled() is True

    widget.set_paused()
    assert widget.launch_button.text() == "Resume"
    assert widget.cancel_button.isVisible() is True
    assert widget.stage_label.text() == "PAUSED"
    assert "Press Resume" in widget.detail_label.text()

    widget.set_resumed()
    assert widget.launch_button.text() == "Pause"
    assert widget.stage_label.text() == "RUNNING"

    widget.set_cancel_pending()
    assert widget.launch_button.isEnabled() is False
    assert widget.cancel_button.isEnabled() is False
    assert widget.stage_label.text() == "CANCELLING"

    widget.set_launch_active(False)
    widget.set_busy(False)
    assert widget.launch_button.text() == "Launch"
    assert widget.cancel_button.isVisible() is False
    assert widget.launch_button.isEnabled() is True


def test_paused_state_keeps_progress_and_invites_resume(app):
    widget = LaunchControlWidget()
    widget.show()
    event = ProgressEvent(stage=ProgressStage.DOWNLOADING_ASSETS, message="Downloading assets...", current=1, total=2)

    widget.set_launch_active(True)
    widget.set_progress_event(event)
    widget.set_paused()

    assert widget.stage_label.text() == "PAUSED"
    assert "Press Resume" in widget.detail_label.text()
    assert widget.launch_button.text() == "Resume"
    assert widget.cancel_button.isVisible() is True
    assert widget.stage_label.property("state") == "warning"

def test_exit_result_shows_instance_and_restores_launch_button(app):
    widget = LaunchControlWidget()
    result = SimpleNamespace(instance_name="Runtime Test", crashed=True, exit_code=1, duration_seconds=75)

    widget.set_launch_active(True)
    widget.set_launch_active(False)
    widget.set_exit_result(result)

    assert "Runtime Test" in widget.status_label.text()
    assert "1" in widget.detail_label.text()
    assert widget.stage_label.text() == "CRASHED"
    assert widget.launch_button.text() == "Launch"


def test_non_blocking_modrinth_warning_is_shown_without_failed_state(app):
    widget = LaunchControlWidget()

    widget.set_result({
        "minecraftVersion": "1.21",
        "javaPath": "javaw.exe",
        "warnings": ("mods/example.jar must be installed manually",),
    })

    assert "warnings" in widget.status_label.text().lower()
    assert "mods/example.jar" in widget.detail_label.text()
    assert widget.stage_label.text() == "WARNING"
    assert widget.stage_label.property("state") == "warning"
    assert widget.launch_button.text() == "Launch"


def test_failed_state_keeps_technical_error_out_of_progress_area(app):
    widget = LaunchControlWidget()
    technical_error = "Forge pre-launch check failed:\n" + "\n".join(f"- broken mod {index}" for index in range(80))

    widget.set_failed(technical_error)

    assert widget.status_label.text() == "Launch failed"
    assert widget.detail_label.text() == "Open Logs to see the full error details."
    assert "broken mod" not in widget.detail_label.text()
    assert widget.stage_label.text() == "FAILED"


def test_completed_operation_sets_terminal_ready_progress(app):
    widget = LaunchControlWidget()

    widget.set_operation_completed("loader.progress.ready", "loader.progress.ready_detail")

    assert widget.progress_bar.value() == 100
    assert widget.progress_bar.format() == ""
    assert widget.percentage_label.text() == "100%"
    assert widget.stage_label.text() == "READY"
    assert widget.stage_label.property("state") == "success"
    assert widget.status_label.text() == "Mod loader ready"
    assert "instance is ready" in widget.detail_label.text()


def test_idle_launch_fills_controls_and_active_state_splits_pause_cancel(app):
    widget = LaunchControlWidget()
    widget.resize(1000, 120)
    widget.show()
    app.processEvents()

    assert widget.launch_button.sizePolicy().horizontalPolicy() is QSizePolicy.Policy.Expanding
    assert widget.launch_button.sizePolicy().verticalPolicy() is QSizePolicy.Policy.Expanding
    assert widget.cancel_button.sizePolicy().horizontalPolicy() is QSizePolicy.Policy.Expanding
    assert widget.cancel_button.sizePolicy().verticalPolicy() is QSizePolicy.Policy.Expanding
    assert widget.controls_widget.sizePolicy().horizontalPolicy() is QSizePolicy.Policy.Expanding
    assert widget.controls_widget.sizePolicy().verticalPolicy() is QSizePolicy.Policy.Expanding
    assert widget.controls_widget.width() < widget.width() * 0.4
    assert widget.progress_bar.format() == ""
    assert widget.percentage_label.text() == "0%"
    assert widget.launch_button.minimumHeight() >= 74
    assert widget.cancel_button.minimumHeight() >= 74
    assert widget.cancel_button.isVisible() is False
    idle_width = widget.launch_button.width()
    idle_height = widget.launch_button.height()

    widget.set_launch_active(True)
    app.processEvents()

    assert widget.launch_button.text() == "Pause"
    assert widget.cancel_button.isVisible() is True
    assert widget.launch_button.width() < idle_width
    assert abs(widget.launch_button.width() - widget.cancel_button.width()) <= 2
    assert widget.launch_button.height() == widget.cancel_button.height()
    assert widget.launch_button.height() >= idle_height - 2
