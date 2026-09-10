from __future__ import annotations

import json
from pathlib import Path
import queue
import sys
import threading
import time


def _request_ready_path(request_path: Path) -> Path | None:
    try:
        payload = json.loads(Path(request_path).read_text(encoding="utf-8"))
    except Exception:
        return None
    raw = str(payload.get("ready_path") or "").strip() if isinstance(payload, dict) else ""
    return Path(raw) if raw else None


def _signal_ready(request_path: Path) -> None:
    ready_path = _request_ready_path(request_path)
    if ready_path is None:
        return
    ready_path.parent.mkdir(parents=True, exist_ok=True)
    ready_path.write_text(
        json.dumps({"ready": True, "pid": __import__("os").getpid(), "timestamp": time.time()}),
        encoding="utf-8",
    )


def _headless_apply(request_path: Path) -> int:
    _signal_ready(request_path)
    from src.core.update.update_applier import run_update_applier
    return run_update_applier(request_path)


def _gui_apply(request_path: Path) -> int:
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return _headless_apply(request_path)

    from src.core.update.update_applier import run_update_applier

    root = tk.Tk()
    root.title("MCW Updater")
    root.resizable(False, False)
    try:
        root.iconbitmap(str(Path(__file__).resolve().parent / "assets" / "icons" / "mcw_launcher.ico"))
    except Exception:
        pass

    frame = ttk.Frame(root, padding=22)
    frame.grid(row=0, column=0, sticky="nsew")
    title = ttk.Label(frame, text="MCW Launcher Update", font=("Segoe UI", 14, "bold"))
    title.grid(row=0, column=0, sticky="w")
    status_var = tk.StringVar(value="Preparing updater...")
    status = ttk.Label(frame, textvariable=status_var, width=52)
    status.grid(row=1, column=0, sticky="w", pady=(12, 8))
    progress = ttk.Progressbar(frame, mode="indeterminate", length=390)
    progress.grid(row=2, column=0, sticky="ew")
    progress.start(12)
    note = ttk.Label(frame, text="Do not turn off the computer while launcher files are being replaced.", wraplength=390)
    note.grid(row=3, column=0, sticky="w", pady=(10, 0))
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    root.update_idletasks()

    results: queue.Queue[int] = queue.Queue(maxsize=1)
    _signal_ready(request_path)

    def worker() -> None:
        results.put(run_update_applier(request_path))

    threading.Thread(target=worker, name="mcw-updater-apply", daemon=True).start()

    last_line = ""
    log_path = request_path.parent / "update.log"

    def poll() -> None:
        nonlocal last_line
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                line = text.splitlines()[-1]
                if line != last_line:
                    last_line = line
                    message = line.split("] ", 1)[-1]
                    status_var.set(message)
        except OSError:
            pass
        try:
            code = results.get_nowait()
        except queue.Empty:
            root.after(120, poll)
            return
        progress.stop()
        status_var.set("Update completed. Starting MCW Launcher..." if code == 0 else "Update failed. Recovery was attempted.")
        root.update_idletasks()
        root.after(900 if code == 0 else 1800, root.destroy)
        root._mcw_exit_code = code  # type: ignore[attr-defined]

    root.after(80, poll)
    root.mainloop()
    return int(getattr(root, "_mcw_exit_code", 1))


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] in {"--version", "-V"}:
        from src.config import VERSION_TAG
        print(f"MCW Updater {VERSION_TAG}")
        return 0

    if len(sys.argv) != 3 or sys.argv[1] != "--apply-update":
        return 2

    request_path = Path(sys.argv[2])
    if sys.platform == "win32":
        return _gui_apply(request_path)
    return _headless_apply(request_path)


if __name__ == "__main__":
    raise SystemExit(main())
