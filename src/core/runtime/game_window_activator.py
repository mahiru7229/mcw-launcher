from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
import threading
import time
from typing import Callable

from src.core.system.platform_info import PlatformInfo

logger = logging.getLogger(__name__)


class GameWindowActivator:
    """Monitors and activates the Minecraft game window directly to the foreground."""

    @classmethod
    def allow_foreground(cls, pid: int | None = None) -> bool:
        """Grants permission for the specified process to set the foreground window on Windows."""
        if not PlatformInfo.is_windows():
            return False
        try:
            user32 = ctypes.windll.user32
            # ASFW_ANY = -1 allows any process, or target a specific PID
            target = int(pid) if isinstance(pid, int) and pid > 0 else -1
            result = user32.AllowSetForegroundWindow(target)
            return bool(result)
        except Exception as error:
            logger.debug("AllowSetForegroundWindow failed: %s", error)
            return False

    @classmethod
    def _collect_process_tree_pids(cls, root_pid: int) -> set[int]:
        """Returns root_pid and any direct/indirect child PIDs on Windows."""
        pids = {int(root_pid)}
        if not PlatformInfo.is_windows() or root_pid <= 0:
            return pids
        try:
            kernel32 = ctypes.windll.kernel32
            TH32CS_SNAPPROCESS = 0x00000002

            class PROCESSENTRY32W(ctypes.Structure):
                _fields_ = [
                    ("dwSize", wintypes.DWORD),
                    ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_void_p),
                    ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD),
                    ("szExeFile", wintypes.WCHAR * 260),
                ]

            snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if snapshot == ctypes.c_void_p(-1).value or not snapshot:
                return pids
            try:
                parent_map: dict[int, int] = {}
                entry = PROCESSENTRY32W()
                entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
                if kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                    while True:
                        parent_map[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
                        if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                            break
                changed = True
                while changed:
                    changed = False
                    for child_pid, parent_pid in parent_map.items():
                        if parent_pid in pids and child_pid not in pids:
                            pids.add(child_pid)
                            changed = True
            finally:
                kernel32.CloseHandle(snapshot)
        except Exception:
            pass
        return pids

    @classmethod
    def find_window_for_pid(cls, pid: int) -> int | None:
        """Finds the main visible game window handle (HWND) for the given process PID."""
        if not PlatformInfo.is_windows():
            return None
        try:
            user32 = ctypes.windll.user32
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
            user32.EnumWindows.restype = wintypes.BOOL
            user32.IsWindowVisible.argtypes = [wintypes.HWND]
            user32.IsWindowVisible.restype = wintypes.BOOL
            user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
            user32.GetWindow.restype = wintypes.HWND
            user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
            user32.GetWindowRect.restype = wintypes.BOOL

            target_pids = cls._collect_process_tree_pids(pid)
            matched_hwnd: int | None = None
            GW_OWNER = 4

            def enum_proc(hwnd: int, _lparam: int) -> bool:
                nonlocal matched_hwnd
                try:
                    if not user32.IsWindowVisible(hwnd):
                        return True

                    window_pid = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                    if int(window_pid.value) not in target_pids:
                        return True

                    if user32.GetWindow(hwnd, GW_OWNER):
                        return True

                    # Filter out 0x0 or tiny dummy helper windows (e.g. GLFW/OpenGL dummy context windows)
                    rect = wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    width = rect.right - rect.left
                    height = rect.bottom - rect.top
                    if width < 100 or height < 100:
                        return True

                    matched_hwnd = hwnd
                    return False
                except Exception:
                    pass

                return True

            cb = WNDENUMPROC(enum_proc)
            user32.EnumWindows(cb, 0)
            return matched_hwnd
        except Exception as error:
            logger.debug("find_window_for_pid failed: %s", error)
            return None

    @classmethod
    def activate_window(cls, hwnd: int) -> bool:
        """Brings the specified window handle to the top foreground and focuses it."""
        if not PlatformInfo.is_windows():
            return False
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            user32.IsIconic.argtypes = [wintypes.HWND]
            user32.IsIconic.restype = wintypes.BOOL
            user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.ShowWindow.restype = wintypes.BOOL
            user32.GetForegroundWindow.argtypes = []
            user32.GetForegroundWindow.restype = wintypes.HWND
            user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
            user32.GetWindowThreadProcessId.restype = wintypes.DWORD
            user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
            user32.AttachThreadInput.restype = wintypes.BOOL
            user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
            user32.SetWindowPos.restype = wintypes.BOOL
            user32.BringWindowToTop.argtypes = [wintypes.HWND]
            user32.BringWindowToTop.restype = wintypes.BOOL
            user32.SetForegroundWindow.argtypes = [wintypes.HWND]
            user32.SetForegroundWindow.restype = wintypes.BOOL
            user32.SetFocus.argtypes = [wintypes.HWND]
            user32.SetFocus.restype = wintypes.HWND
            kernel32.GetCurrentThreadId.argtypes = []
            kernel32.GetCurrentThreadId.restype = wintypes.DWORD

            # Only restore if the window is actually minimized (iconic); calling
            # SW_RESTORE on a maximized window would un-maximize (shrink) it.
            if user32.IsIconic(hwnd):
                SW_RESTORE = 9
                user32.ShowWindow(hwnd, SW_RESTORE)

            current_thread = kernel32.GetCurrentThreadId()
            target_thread = user32.GetWindowThreadProcessId(hwnd, None)
            foreground_hwnd = user32.GetForegroundWindow()
            foreground_thread = user32.GetWindowThreadProcessId(foreground_hwnd, None) if foreground_hwnd else 0

            attached_current = False
            attached_foreground = False
            try:
                if current_thread and target_thread and current_thread != target_thread:
                    attached_current = bool(user32.AttachThreadInput(current_thread, target_thread, True))
                if foreground_thread and target_thread and foreground_thread != target_thread:
                    attached_foreground = bool(user32.AttachThreadInput(foreground_thread, target_thread, True))

                # Pop to top of z-order: HWND_TOPMOST (-1) then HWND_NOTOPMOST (-2)
                user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0010)
                user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0040)
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.SetFocus(hwnd)
            finally:
                if attached_current:
                    user32.AttachThreadInput(current_thread, target_thread, False)
                if attached_foreground:
                    user32.AttachThreadInput(foreground_thread, target_thread, False)

            return True
        except Exception as error:
            logger.debug("activate_window failed: %s", error)
            return False

    @classmethod
    def watch_and_activate(
        cls,
        process: object,
        timeout_seconds: float = 90.0,
        poll_interval: float = 0.25,
        on_window_found: Callable[[int], None] | None = None,
    ) -> threading.Thread | None:
        """Watches for the Minecraft window to appear, activates it, and invokes on_window_found."""
        pid = getattr(process, "pid", None)
        if not isinstance(pid, int) or pid <= 0:
            return None

        # Give the process permission to set foreground immediately
        cls.allow_foreground(pid)

        def worker() -> None:
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                poll = getattr(process, "poll", None)
                if callable(poll) and poll() is not None:
                    # Process exited before window appeared
                    break

                hwnd = cls.find_window_for_pid(pid)
                if hwnd is not None:
                    if on_window_found is not None:
                        try:
                            on_window_found(hwnd)
                        except Exception as cb_err:
                            logger.debug("on_window_found error: %s", cb_err)
                    cls.activate_window(hwnd)
                    break

                time.sleep(poll_interval)

        thread = threading.Thread(target=worker, name=f"mcw-window-activator-{pid}", daemon=True)
        thread.start()
        return thread
