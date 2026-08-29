from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def open_local_path(path: str | Path) -> bool:
    """Open a file or directory with the desktop's native handler.

    Qt's ``openUrl`` is unreliable with ``file://`` URLs on some lightweight
    Linux desktops. Prefer the freedesktop launchers there and keep Qt as the
    cross-platform fallback.
    """

    resolved = Path(path).expanduser().resolve()
    if sys.platform.startswith("linux"):
        commands = (("xdg-open", str(resolved)), ("gio", "open", str(resolved)))
        for command in commands:
            if shutil.which(command[0]) is None:
                continue
            try:
                subprocess.Popen(
                    list(command),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    start_new_session=True,
                )
                return True
            except OSError:
                continue
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(resolved))))
