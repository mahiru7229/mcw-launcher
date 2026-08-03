from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

import src.gui.main_window_2 as main_window_module
from src.gui.main_window_2 import MainWindow
from src.models.progress.progress_state import ProgressState


def test_successful_provider_import_replaces_preparing_progress(monkeypatch):
    events: list[object] = []
    scheduled: list[tuple[int, object]] = []
    window = SimpleNamespace(
        instance_controller=SimpleNamespace(
            CREATE_TASK_ID="instance.create",
            LOADER_CHANGE_TASK_ID="instance.loader",
            LOADER_REPAIR_TASK_ID="instance.loader.repair",
            FORGE_RESTORE_TASK_ID="instance.loader.restore",
        ),
        launch_controller=SimpleNamespace(TASK_ID="minecraft.launch"),
        _suppress_loader_progress=False,
        _on_progress=events.append,
    )
    monkeypatch.setattr(main_window_module.QTimer, "singleShot", lambda delay, callback: scheduled.append((delay, callback)))

    MainWindow._on_task_succeeded(window, "modpack.import", object())

    assert len(scheduled) == 1
    assert scheduled[0][0] == 0
    scheduled[0][1]()
    assert len(events) == 1
    event = events[0]
    assert event.state is ProgressState.SUCCEEDED
    assert event.message == "modpack_package.import.completed"
    assert event.detail == "modpack_package.import.completed_detail"
