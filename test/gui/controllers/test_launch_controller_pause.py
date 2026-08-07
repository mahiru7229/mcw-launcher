from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal

from src.core.network.download_pause import DownloadCancelledError, DownloadPausedError, download_pause_controller
from src.gui.controllers.launch_controller import LaunchController


class FakeTaskRunner(QObject):
    task_succeeded = Signal(str, object)
    task_failed = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.active = False

    def is_task_active(self, task_id: str) -> bool:
        return self.active and task_id == LaunchController.TASK_ID


@pytest.fixture(autouse=True)
def reset_pause_controller():
    download_pause_controller.finish()
    yield
    download_pause_controller.finish()


def test_clicking_launch_again_toggles_pause_and_resume() -> None:
    runner = FakeTaskRunner()
    controller = LaunchController(runner)
    runner.active = True
    paused: list[bool] = []
    resumed: list[bool] = []
    controller.launch_paused.connect(lambda: paused.append(True))
    controller.launch_resumed.connect(lambda: resumed.append(True))
    download_pause_controller.begin()

    controller.launch()
    assert paused == [True]
    assert download_pause_controller.is_paused is True

    controller.launch()
    assert resumed == [True]
    assert download_pause_controller.is_paused is False


def test_cancel_request_and_cancelled_task_do_not_open_error_dialog() -> None:
    runner = FakeTaskRunner()
    controller = LaunchController(runner)
    runner.active = True
    requested: list[bool] = []
    cancelled: list[bool] = []
    errors: list[tuple[str, str]] = []
    controller.cancel_requested.connect(lambda: requested.append(True))
    controller.launch_cancelled.connect(lambda: cancelled.append(True))
    controller.error_created.connect(lambda title, message: errors.append((title, message)))
    download_pause_controller.begin()

    controller.cancel()
    assert requested == [True]
    assert download_pause_controller.is_cancel_requested is True

    controller._on_task_failed(LaunchController.TASK_ID, DownloadCancelledError("cancelled"))
    assert cancelled == [True]
    assert errors == []


def test_legacy_paused_task_still_emits_paused_signal_without_error_dialog() -> None:
    runner = FakeTaskRunner()
    controller = LaunchController(runner)
    paused: list[bool] = []
    errors: list[tuple[str, str]] = []
    controller.launch_paused.connect(lambda: paused.append(True))
    controller.error_created.connect(lambda title, message: errors.append((title, message)))

    controller._on_task_failed(LaunchController.TASK_ID, DownloadPausedError("paused"))

    assert paused == [True]
    assert errors == []


def test_failed_launch_logs_full_error_without_opening_error_dialog() -> None:
    runner = FakeTaskRunner()
    controller = LaunchController(runner)
    errors: list[tuple[str, str]] = []
    logs: list[str] = []
    statuses: list[str] = []
    controller.error_created.connect(lambda title, message: errors.append((title, message)))
    controller.log_created.connect(logs.append)
    controller.status_changed.connect(statuses.append)
    error = RuntimeError("Forge pre-launch check failed:\n- Example mod uses the wrong loader")

    controller._on_task_failed(LaunchController.TASK_ID, error)

    assert errors == []
    assert statuses == ["Launch failed"]
    assert logs == ["RuntimeError: Forge pre-launch check failed:\n- Example mod uses the wrong loader"]


def test_manual_content_pause_cannot_be_resumed_by_launch_toggle():
    runner = FakeTaskRunner()
    controller = LaunchController(runner)
    runner.active = True
    required = RuntimeError("manual files required")
    emitted = []
    controller.manual_content_required.connect(emitted.append)
    download_pause_controller.begin()
    assert download_pause_controller.request_pause() is True

    controller._on_manual_content_required(required)

    assert emitted == [required]
    assert controller.waiting_for_manual_content is True
    controller.launch()
    assert download_pause_controller.is_paused is True

    assert controller.resume_manual_content() is True
    assert controller.waiting_for_manual_content is False
    assert download_pause_controller.is_paused is False
