from __future__ import annotations

from threading import Thread
from typing import Any

import pytest

pytest.importorskip("PySide6")

from src.gui.task_runner import (
    TaskCancellationToken,
    TaskContext,
    TaskRunner,
    TaskState,
)


@pytest.mark.parametrize(
    ("succeeded", "signal_name", "payload"),
    (
        (True, "task_succeeded", object()),
        (False, "task_failed", RuntimeError("failed")),
    ),
)
def test_completion_callbacks_observe_released_blocking_state(
    gui_app,
    succeeded: bool,
    signal_name: str,
    payload: Any,
):
    runner = TaskRunner()
    context = TaskContext(
        context_id="context-1",
        task_id="modpack.update.preview",
        group="modpack.update.preview",
        thread=Thread(target=lambda: None, daemon=True),
        token=TaskCancellationToken(),
        blocking=True,
        cooperative=False,
    )
    runner._contexts[context.context_id] = context
    runner._blocking_tasks = 1
    observed_states = []

    getattr(runner, signal_name).connect(
        lambda *_args: observed_states.append(
            (runner.is_busy, runner.has_active_tasks)
        )
    )

    runner._finish_worker(context.context_id, succeeded, payload)

    assert observed_states == [(False, False)]


def test_cancel_marks_task_and_token_without_killing_thread(gui_app) -> None:
    runner = TaskRunner()
    token = TaskCancellationToken()
    context = TaskContext(
        context_id="context-1",
        task_id="versions.load",
        group="versions",
        thread=Thread(target=lambda: None, daemon=True),
        token=token,
        blocking=False,
        cooperative=True,
    )
    runner._contexts[context.context_id] = context

    assert runner.cancel("versions.load") is True
    assert token.cancelled is True
    assert context.state is TaskState.CANCEL_REQUESTED


def test_shutdown_requests_cancellation_and_rejects_new_work(gui_app) -> None:
    runner = TaskRunner()
    token = TaskCancellationToken()
    context = TaskContext(
        context_id="context-1",
        task_id="java.scan",
        group="java.scan",
        thread=Thread(target=lambda: None, daemon=True),
        token=token,
        blocking=False,
        cooperative=False,
    )
    runner._contexts[context.context_id] = context

    assert runner.begin_shutdown() == ("java.scan",)
    assert runner.is_shutting_down is True
    assert token.cancelled is True
    assert runner.run("later", lambda: None, "later", blocking=False) is False


def test_priority_mode_cancels_competing_tasks_and_rejects_new_non_priority_work(gui_app) -> None:
    runner = TaskRunner()
    token = TaskCancellationToken()
    context = TaskContext(
        context_id="context-1",
        task_id="java.scan",
        group="java.scan",
        thread=Thread(target=lambda: None, daemon=True),
        token=token,
        blocking=False,
        cooperative=True,
    )
    runner._contexts[context.context_id] = context
    rejected = []
    runner.task_rejected.connect(rejected.append)

    assert runner.begin_priority_mode("update.") == ("java.scan",)
    assert runner.is_priority_mode is True
    assert runner.priority_prefix == "update."
    assert token.cancelled is True
    assert runner.run("modrinth.search", lambda: None, "search", blocking=False) is False
    assert rejected

    assert runner.end_priority_mode("update.") is True
    assert runner.is_priority_mode is False
