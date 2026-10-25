from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from src.core.runtime.game_window_activator import GameWindowActivator
from src.core.system.platform_info import PlatformInfo


class DummyProcess:
    def __init__(self, pid: int = 12345, running: bool = True) -> None:
        self.pid = pid
        self._running = running

    def poll(self) -> int | None:
        return None if self._running else 0


def test_allow_foreground_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PlatformInfo, "is_windows", lambda: False)
    assert GameWindowActivator.allow_foreground(12345) is False


def test_find_window_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PlatformInfo, "is_windows", lambda: False)
    assert GameWindowActivator.find_window_for_pid(12345) is None


def test_activate_window_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PlatformInfo, "is_windows", lambda: False)
    assert GameWindowActivator.activate_window(9999) is False


def test_watch_and_activate_rejects_invalid_pid() -> None:
    proc = DummyProcess(pid=0)
    assert GameWindowActivator.watch_and_activate(proc) is None


def test_watch_and_activate_triggers_callback_when_window_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(GameWindowActivator, "allow_foreground", lambda pid: True)
    monkeypatch.setattr(GameWindowActivator, "find_window_for_pid", lambda pid: 54321)
    activated = []
    monkeypatch.setattr(GameWindowActivator, "activate_window", lambda hwnd: activated.append(hwnd) or True)

    found = []
    proc = DummyProcess(pid=12345)
    thread = GameWindowActivator.watch_and_activate(
        proc,
        timeout_seconds=2.0,
        poll_interval=0.01,
        on_window_found=found.append,
    )
    assert thread is not None
    thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert activated == [54321]
    assert found == [54321]


def test_watch_and_activate_stops_when_process_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(GameWindowActivator, "allow_foreground", lambda pid: True)
    monkeypatch.setattr(GameWindowActivator, "find_window_for_pid", lambda pid: None)

    proc = DummyProcess(pid=12345, running=True)
    thread = GameWindowActivator.watch_and_activate(
        proc,
        timeout_seconds=5.0,
        poll_interval=0.01,
    )
    assert thread is not None
    # Process exits shortly
    proc._running = False
    thread.join(timeout=2.0)
    assert not thread.is_alive()


def test_find_window_for_pid_ignores_other_pid_with_minecraft_title(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PlatformInfo, "is_windows", lambda: True)
    monkeypatch.setattr(GameWindowActivator, "_collect_process_tree_pids", lambda pid: {int(pid)})

    fake_user32 = MagicMock()

    def fake_enum_windows(callback, lparam):
        import ctypes
        from ctypes import wintypes

        def fake_get_pid(hwnd, byref_pid):
            byref_pid._obj.value = 99999
            return 1

        fake_user32.GetWindowThreadProcessId.side_effect = fake_get_pid
        fake_user32.IsWindowVisible.return_value = 1
        fake_user32.GetWindow.return_value = 0

        def fake_rect(hwnd, byref_rect):
            byref_rect._obj.left = 0
            byref_rect._obj.top = 0
            byref_rect._obj.right = 800
            byref_rect._obj.bottom = 600
            return 1

        fake_user32.GetWindowRect.side_effect = fake_rect

        # Run callback with hwnd 77777
        callback(77777, 0)
        return 1

    fake_user32.EnumWindows.side_effect = fake_enum_windows

    import ctypes
    monkeypatch.setattr(ctypes.windll, "user32", fake_user32)

    # Looking for target PID 12345 should return None because PID 99999 doesn't match
    matched = GameWindowActivator.find_window_for_pid(12345)
    assert matched is None


def test_activate_window_restore_behavior_matches_is_iconic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PlatformInfo, "is_windows", lambda: True)
    import ctypes
    fake_user32 = MagicMock()
    fake_kernel32 = MagicMock()
    fake_kernel32.GetCurrentThreadId.return_value = 100
    fake_user32.GetWindowThreadProcessId.return_value = 100
    fake_user32.GetForegroundWindow.return_value = 0

    monkeypatch.setattr(ctypes.windll, "user32", fake_user32)
    monkeypatch.setattr(ctypes.windll, "kernel32", fake_kernel32)

    # Case 1: IsIconic returns 0 -> ShowWindow(SW_RESTORE=9) MUST NOT be called
    fake_user32.IsIconic.return_value = 0
    fake_user32.ShowWindow.reset_mock()
    assert GameWindowActivator.activate_window(1234) is True
    fake_user32.ShowWindow.assert_not_called()

    # Case 2: IsIconic returns 1 -> ShowWindow(SW_RESTORE=9) MUST be called
    fake_user32.IsIconic.return_value = 1
    fake_user32.ShowWindow.reset_mock()
    assert GameWindowActivator.activate_window(1234) is True
    fake_user32.ShowWindow.assert_called_once_with(1234, 9)


def test_main_window_on_game_window_ready_when_inactive_uses_showminnoactive(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.gui.main_window import MainWindow

    fake_window = MagicMock(spec=MainWindow)
    fake_window._last_launch_was_quick_play = False
    fake_window.gui_settings_controller = MagicMock()
    fake_window.gui_settings_controller.current = {"minimize_on_launch": True}
    fake_window.isMinimized.return_value = False
    fake_window.isActiveWindow.return_value = False
    fake_window.winId.return_value = 88888

    shown_commands = []
    fake_user32 = MagicMock()
    fake_user32.ShowWindow = lambda hwnd, cmd: shown_commands.append((hwnd, cmd))

    import ctypes
    monkeypatch.setattr(ctypes.windll, "user32", fake_user32)
    monkeypatch.setattr("mcw_core.api.system.platform_info.PlatformInfo.is_windows", lambda: True)
    monkeypatch.setattr("mcw_core.api.runtime.game_window_activator.GameWindowActivator.activate_window", lambda hwnd: True)

    MainWindow._on_game_window_ready(fake_window, 99999)

    # When not active on Windows, showMinimized must NOT be called, and ShowWindow(winId, 7) MUST be called
    fake_window.showMinimized.assert_not_called()
    assert (88888, 7) in shown_commands
