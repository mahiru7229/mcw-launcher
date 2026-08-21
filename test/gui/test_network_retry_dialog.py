from __future__ import annotations

import os
from enum import IntFlag
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

import src.gui.main_window as main_window_module
from src.gui.main_window import MainWindow


class _Button:
    def __init__(self) -> None:
        self.text = ""

    def setText(self, text: str) -> None:
        self.text = text


class _FakeMessageBox:
    class Icon:
        Warning = 1

    class StandardButton(IntFlag):
        Retry = 1
        Cancel = 2

    next_result = StandardButton.Retry.value

    def __init__(self, _parent=None) -> None:
        self.buttons = {
            self.StandardButton.Retry: _Button(),
            self.StandardButton.Cancel: _Button(),
        }

    def setIcon(self, _icon) -> None:
        pass

    def setWindowTitle(self, _title: str) -> None:
        pass

    def setText(self, _text: str) -> None:
        pass

    def setInformativeText(self, _text: str) -> None:
        pass

    def setStandardButtons(self, _buttons) -> None:
        pass

    def setDefaultButton(self, _button) -> None:
        pass

    def setEscapeButton(self, _button) -> None:
        pass

    def button(self, button):
        return self.buttons.get(button)

    def exec(self) -> int:
        return int(self.next_result)


def _window_stub():
    return SimpleNamespace(statuses=[], errors=[], _set_status=lambda message: None, _show_error=lambda title, message: None)


def test_retry_dialog_restarts_registered_task(monkeypatch) -> None:
    monkeypatch.setattr(main_window_module, "QMessageBox", _FakeMessageBox)
    retried: list[str] = []
    controller = SimpleNamespace(retry_network_task=lambda task_id: retried.append(task_id) or True)
    window = _window_stub()
    _FakeMessageBox.next_result = _FakeMessageBox.StandardButton.Retry.value

    MainWindow._show_network_retry(window, controller, "metadata.load", "Metadata", "timed out")

    assert retried == ["metadata.load"]


def test_retry_dialog_cancel_does_not_restart_task(monkeypatch) -> None:
    monkeypatch.setattr(main_window_module, "QMessageBox", _FakeMessageBox)
    retried: list[str] = []
    statuses: list[str] = []
    controller = SimpleNamespace(retry_network_task=lambda task_id: retried.append(task_id) or True)
    window = SimpleNamespace(_set_status=statuses.append, _show_error=lambda _title, _message: None)
    _FakeMessageBox.next_result = _FakeMessageBox.StandardButton.Cancel.value

    MainWindow._show_network_retry(window, controller, "metadata.load", "Metadata", "timed out")

    assert retried == []
    assert statuses
