from __future__ import annotations

import sys
from pathlib import Path



def restart_command() -> tuple[str, list[str], str]:
    """Return the executable, arguments, and working directory for a clean restart.

    Frozen builds restart the current executable. Source checkouts restart through
    the active Python interpreter and the repository's ``launcher.py`` entrypoint.
    Startup-only cleanup arguments have already been consumed by ``launcher.py``
    before the main window is created, so the remaining arguments are safe to
    preserve.
    """

    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        return str(executable), list(sys.argv[1:]), str(executable.parent)

    launcher_path = Path(__file__).resolve().parents[2] / "launcher.py"
    executable = Path(sys.executable).resolve()
    return str(executable), [str(launcher_path), *sys.argv[1:]], str(launcher_path.parent)


def start_restarted_process() -> bool:
    """Start a replacement launcher process without terminating the current one."""

    from PySide6.QtCore import QProcess

    executable, arguments, working_directory = restart_command()
    result = QProcess.startDetached(executable, arguments, working_directory)
    if isinstance(result, tuple):
        return bool(result[0])
    return bool(result)
