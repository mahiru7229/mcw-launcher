from __future__ import annotations

import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import TextIO

from src.core.fs.paths import Paths
from src.models.instance.instance import Instance


class JavaRuntime:
    _process_logs: dict[int, tuple[Path, TextIO]] = {}
    _process_logs_lock = threading.RLock()

    @classmethod
    def run(cls, java: Path, command: list[str], instance: Instance) -> subprocess.Popen:
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        log_dir = Paths.instance_logs_dir(instance)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_path = log_dir / f"minecraft-{timestamp}.log"
        log_file = log_path.open("w", encoding="utf-8", errors="replace")

        try:
            process = subprocess.Popen(
                [str(java), *command],
                cwd=Paths.load_instance_dir(instance.name),
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=creation_flags,
            )
        except Exception:
            log_file.close()
            raise

        pid = getattr(process, "pid", None)
        if isinstance(pid, int) and pid > 0:
            with cls._process_logs_lock:
                cls._process_logs[pid] = (log_path, log_file)
        return process

    @classmethod
    def log_path(cls, process: object) -> Path | None:
        pid = getattr(process, "pid", None)
        if not isinstance(pid, int) or pid <= 0:
            return None
        with cls._process_logs_lock:
            record = cls._process_logs.get(pid)
        return record[0] if record is not None else None

    @classmethod
    def close_process_log(cls, process: object) -> None:
        pid = getattr(process, "pid", None)
        if not isinstance(pid, int) or pid <= 0:
            return
        with cls._process_logs_lock:
            record = cls._process_logs.pop(pid, None)
        if record is None:
            return
        try:
            record[1].close()
        except OSError:
            pass
