from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.core.auth.microsoft.oauth_callback_server import MicrosoftAuthorizationCancelledError
from src.gui.controllers.account_controller import AccountController
from src.gui.task_runner import TaskRunner


def test_microsoft_auth_runs_without_blocking_the_launcher(gui_app, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = TaskRunner()
    controller = AccountController(runner)
    started = []
    states = []

    monkeypatch.setattr(runner, "is_task_active", lambda _task_id: False)
    monkeypatch.setattr(runner, "run", lambda task_id, task, message, blocking=True: started.append((task_id, task, message, blocking)) or True)
    controller.microsoft_auth_state_changed.connect(lambda active, message: states.append((active, message)))

    controller.create_microsoft()

    assert started[0][0] == controller.MICROSOFT_TASK_ID
    assert started[0][3] is False
    assert states and states[0][0] is True
    gui_app.processEvents()


def test_cancel_microsoft_sets_cancel_event_and_does_not_emit_error(gui_app, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = TaskRunner()
    controller = AccountController(runner)
    errors = []
    statuses = []

    monkeypatch.setattr(runner, "is_task_active", lambda task_id: task_id == controller.MICROSOFT_TASK_ID)
    controller.error_created.connect(lambda *args: errors.append(args))
    controller.status_changed.connect(statuses.append)

    controller.cancel_microsoft()
    assert controller._microsoft_cancel_event.is_set()

    controller._on_task_failed(controller.MICROSOFT_TASK_ID, MicrosoftAuthorizationCancelledError("cancelled"))

    assert errors == []
    assert statuses
    gui_app.processEvents()
