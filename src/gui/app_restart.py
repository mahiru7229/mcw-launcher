from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping


PYINSTALLER_RESET_ENVIRONMENT = "PYINSTALLER_RESET_ENVIRONMENT"


def is_frozen_application() -> bool:
    """Return whether the launcher is running from a frozen application bundle."""

    return bool(getattr(sys, "frozen", False))


def restart_command() -> tuple[str, list[str], str]:
    """Return the executable, arguments, and working directory for a clean restart.

    Frozen builds restart the current executable. Source checkouts restart through
    the active Python interpreter and the repository's ``launcher.py`` entrypoint.
    Startup-only cleanup arguments have already been consumed by ``launcher.py``
    before the main window is created, so the remaining arguments are safe to
    preserve.
    """

    if is_frozen_application():
        executable = Path(sys.executable).resolve()
        return str(executable), list(sys.argv[1:]), str(executable.parent)

    launcher_path = Path(__file__).resolve().parents[2] / "launcher.py"
    executable = Path(sys.executable).resolve()
    return str(executable), [str(launcher_path), *sys.argv[1:]], str(launcher_path.parent)


def restart_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Build the child environment required by the replacement process.

    PyInstaller 6.9 and newer assume that a process started through the same
    executable is a worker that may reuse the current one-file extraction
    directory. A replacement launcher must instead unpack as an independent app
    instance, because it is expected to outlive the current process.

    The reset marker is passed only to the replacement process; the environment
    of the running launcher is never mutated.
    """

    environment = dict(os.environ if source is None else source)
    if is_frozen_application():
        environment[PYINSTALLER_RESET_ENVIRONMENT] = "1"
    else:
        environment.pop(PYINSTALLER_RESET_ENVIRONMENT, None)
    return environment


def start_restarted_process() -> bool:
    """Start a replacement launcher process without terminating the current one."""

    executable, arguments, working_directory = restart_command()
    command = [executable, *arguments]

    try:
        subprocess.Popen(
            command,
            cwd=working_directory,
            env=restart_environment(),
            close_fds=True,
        )
    except (OSError, ValueError):
        return False
    return True
