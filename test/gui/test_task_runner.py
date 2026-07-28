from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QThread

from src.gui.task_runner import TaskContext, TaskRunner


@pytest.mark.parametrize(
    ("finish_method", "signal_name", "payload"),
    (
        ("_finish_success", "task_succeeded", object()),
        ("_finish_failure", "task_failed", RuntimeError("failed")),
    ),
)
def test_completion_callbacks_observe_released_blocking_state(
    gui_app,
    finish_method: str,
    signal_name: str,
    payload: Any,
):
    runner = TaskRunner()
    thread = QThread()
    runner._contexts["modpack.update.preview"] = TaskContext(
        task_id="modpack.update.preview",
        thread=thread,
        worker=object(),
        blocking=True,
    )
    runner._blocking_tasks = 1
    observed_states = []

    getattr(runner, signal_name).connect(
        lambda *_args: observed_states.append(
            (runner.is_busy, runner.has_active_tasks)
        )
    )

    getattr(runner, finish_method)("modpack.update.preview", payload)

    assert observed_states == [(False, False)]
