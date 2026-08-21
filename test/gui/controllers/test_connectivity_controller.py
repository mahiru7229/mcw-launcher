from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from src.core.network.connectivity_monitor import ConnectivitySnapshot
from src.gui.controllers.connectivity_controller import ConnectivityController
from src.gui.task_runner import TaskConflictPolicy, TaskRunner


def test_probe_schedules_non_blocking_replaceable_task(gui_app, monkeypatch: pytest.MonkeyPatch):
    runner = TaskRunner()
    controller = ConnectivityController(runner)
    captured = {}

    def run(task_id, task, message, blocking=True, **kwargs):
        captured.update(task_id=task_id, blocking=blocking, policy=kwargs.get("conflict_policy"))
        return True

    monkeypatch.setattr(runner, "run", run)

    assert controller.probe(force=True) is True
    assert captured == {
        "task_id": "network.connectivity.probe",
        "blocking": False,
        "policy": TaskConflictPolicy.REPLACE,
    }


def test_offline_result_emits_connectivity_state(gui_app):
    controller = ConnectivityController(TaskRunner())
    received = []
    controller.connectivity_changed.connect(lambda online, detail: received.append((online, detail)))

    controller._on_task_succeeded(
        controller.TASK_ID,
        ConnectivitySnapshot(False, checked_at=1.0, latency_ms=50.0, detail="TimeoutError"),
    )

    assert received == [(False, "TimeoutError")]
