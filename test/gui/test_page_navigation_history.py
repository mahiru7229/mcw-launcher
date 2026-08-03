from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.main_window_2 import MainWindow


class _Button:
    def __init__(self) -> None:
        self.enabled = False
        self.tooltip = ""

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)

    def setToolTip(self, value: str) -> None:
        self.tooltip = value

    def setAccessibleName(self, _value: str) -> None:
        pass

    def setAccessibleDescription(self, _value: str) -> None:
        pass


def _window_stub() -> SimpleNamespace:
    window = SimpleNamespace(
        _page_history=[],
        _page_history_index=-1,
        page_back_button=_Button(),
        page_forward_button=_Button(),
    )
    window._update_page_navigation = lambda: MainWindow._update_page_navigation(window)
    return window


def test_page_history_supports_back_forward_and_truncates_future() -> None:
    window = _window_stub()

    MainWindow._record_page_history(window, "instances")
    MainWindow._record_page_history(window, "instance_settings")
    MainWindow._record_page_history(window, "launcher_settings")

    assert window.page_back_button.enabled is True
    assert window.page_forward_button.enabled is False

    visited: list[str] = []
    window.show_page = lambda page_id, record_history=False: visited.append(page_id) or True
    MainWindow._navigate_page_history(window, -1)

    assert visited == ["instance_settings"]
    assert window._page_history_index == 1
    assert window.page_forward_button.enabled is True

    MainWindow._record_page_history(window, "logs")

    assert window._page_history == ["instances", "instance_settings", "logs"]
    assert window.page_forward_button.enabled is False
