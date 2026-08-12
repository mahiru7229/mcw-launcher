from __future__ import annotations

from pathlib import Path
from threading import Thread
from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")

from src.gui.controllers.update_controller import UpdateController
from src.gui.task_runner import TaskCancellationToken, TaskContext, TaskRunner
from src.models.update.update_info import ReleaseAsset, UpdateInfo


def _info() -> UpdateInfo:
    return UpdateInfo(
        current_version="1.4.0-beta.2",
        version="1.4.0-beta.2",
        tag_name="v1.4.0-beta.2",
        title="Beta 2",
        release_notes="",
        release_url="https://example.invalid/release",
        published_at="2026-08-12T00:00:00Z",
        prerelease=True,
        asset=ReleaseAsset(
            name="MCW-Launcher-v1.4.0-beta.2-windows-x64.zip",
            download_url="https://example.invalid/update.zip",
            size=123,
            sha256="a" * 64,
        ),
    )


def test_prepare_enters_priority_mode_and_waits_for_cancelled_work_to_settle(gui_app, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = TaskRunner()
    controller = UpdateController(runner, channel="beta")
    token = TaskCancellationToken()
    context = TaskContext(
        context_id="legacy-task",
        task_id="java.install.21",
        group="java.install.21",
        thread=Thread(target=lambda: None, daemon=True),
        token=token,
        blocking=True,
        cooperative=False,
    )
    runner._contexts[context.context_id] = context
    runner._blocking_tasks = 1

    cancelled_core = []
    controller._core = SimpleNamespace(operations=SimpleNamespace(cancel=lambda: cancelled_core.append(True) or True))
    started = []

    def fake_run(task_id, task, message, blocking=True, **kwargs):
        started.append((task_id, blocking, kwargs))
        return True

    monkeypatch.setattr(runner, "run", fake_run)

    assert controller.prepare(_info()) is True
    assert token.cancelled is True
    assert cancelled_core == [True]
    assert runner.is_priority_mode is True
    assert started == []

    runner._contexts.pop(context.context_id)
    runner._blocking_tasks = 0
    controller._on_task_settled("java.install.21", False, RuntimeError("cancelled"))

    assert started[0][0] == controller.PREPARE_TASK_ID
    assert started[0][1] is True
    assert controller._pending_update_info is None
