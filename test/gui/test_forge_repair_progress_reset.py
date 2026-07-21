from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

import src.gui.main_window_2 as main_window_module
from src.gui.main_window_2 import MainWindow


class _LaunchControl:
    def __init__(self) -> None:
        self.reset_calls = 0
        self.failed_messages: list[str] = []

    def reset_progress(self) -> None:
        self.reset_calls += 1

    def set_failed(self, message: str) -> None:
        self.failed_messages.append(message)


class _StatusTarget:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def set_status(self, message: str) -> None:
        self.messages.append(message)


def _window_stub() -> SimpleNamespace:
    return SimpleNamespace(
        instance_controller=SimpleNamespace(
            REPAIR_TASK_ID="instance.repair.full",
            LOADER_REPAIR_TASK_ID="instance.loader.repair",
        ),
        launch_controller=SimpleNamespace(TASK_ID="minecraft.launch"),
        launch_control=_LaunchControl(),
        home_page=_StatusTarget(),
        right_panel=_StatusTarget(),
        mod_manager_dialog=SimpleNamespace(set_update_error=lambda _message: None),
    )


def test_successful_forge_repair_resets_progress_on_next_gui_turn(monkeypatch):
    window = _window_stub()
    scheduled = []
    monkeypatch.setattr(main_window_module.QTimer, "singleShot", lambda delay, callback: scheduled.append((delay, callback)))

    MainWindow._on_task_succeeded(window, "instance.loader.repair", object())

    assert len(scheduled) == 1
    assert scheduled[0][0] == 0
    scheduled[0][1]()
    assert window.launch_control.reset_calls == 1


def test_failed_forge_repair_leaves_terminal_failed_progress_state():
    window = _window_stub()

    MainWindow._on_task_failed(window, "instance.loader.repair", RuntimeError("repair failed"))

    assert window.launch_control.failed_messages == ["repair failed"]
    assert window.home_page.messages
    assert window.right_panel.messages
