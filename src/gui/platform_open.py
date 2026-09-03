from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


_LINUX_HANDLER_CHECK_SECONDS = 0.75
_FROZEN_CHILD_ENVIRONMENT_KEYS = (
    "GIO_EXTRA_MODULES",
    "GI_TYPELIB_PATH",
    "GTK_PATH",
    "PYTHONHOME",
    "PYTHONPATH",
    "QML2_IMPORT_PATH",
    "QML_IMPORT_PATH",
    "QT_PLUGIN_PATH",
    "QT_QPA_PLATFORM_PLUGIN_PATH",
)


def _linux_child_environment() -> dict[str, str]:
    """Return an environment safe for launching system desktop programs."""

    environment = os.environ.copy()
    if not getattr(sys, "frozen", False):
        return environment

    original_library_path = environment.pop("LD_LIBRARY_PATH_ORIG", None)
    if original_library_path:
        environment["LD_LIBRARY_PATH"] = original_library_path
    else:
        environment.pop("LD_LIBRARY_PATH", None)

    for name in _FROZEN_CHILD_ENVIRONMENT_KEYS:
        environment.pop(name, None)
    return environment


def _linux_open_commands(path: Path) -> tuple[tuple[str, ...], ...]:
    candidates: list[tuple[str, ...]] = [
        ("xdg-open", str(path)),
        ("gio", "open", str(path)),
    ]
    if path.is_dir():
        candidates.append(("pcmanfm-qt", str(path)))

    commands: list[tuple[str, ...]] = []
    for candidate in candidates:
        executable = shutil.which(candidate[0])
        if executable:
            commands.append((executable, *candidate[1:]))
    return tuple(commands)


def _start_linux_handler(command: tuple[str, ...], environment: dict[str, str]) -> bool:
    try:
        process = subprocess.Popen(
            list(command),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
            env=environment,
        )
        try:
            return process.wait(timeout=_LINUX_HANDLER_CHECK_SECONDS) == 0
        except subprocess.TimeoutExpired:
            # Some file managers keep the initial process alive after opening
            # the path. Reaching the timeout therefore means the handler did
            # not fail immediately and can be treated as accepted.
            return True
    except (OSError, subprocess.SubprocessError):
        return False


def open_local_path(path: str | Path) -> bool:
    """Open a file or directory with the desktop's native handler.

    Qt's ``openUrl`` is unreliable with ``file://`` URLs on some lightweight
    Linux desktops. Prefer the freedesktop launchers there and keep Qt as the
    cross-platform fallback.
    """

    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        return False
    if sys.platform.startswith("linux"):
        environment = _linux_child_environment()
        for command in _linux_open_commands(resolved):
            if _start_linux_handler(command, environment):
                return True
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(resolved))))
