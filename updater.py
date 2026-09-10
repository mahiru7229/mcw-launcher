from __future__ import annotations

import json
from pathlib import Path
import queue
import sys
import threading
import time


def _resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative


def _request_payload(request_path: Path) -> dict:
    try:
        payload = json.loads(Path(request_path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _request_ready_path(request_path: Path) -> Path | None:
    raw = str(_request_payload(request_path).get("ready_path") or "").strip()
    return Path(raw) if raw else None


def _request_target_version(request_path: Path) -> str:
    return str(_request_payload(request_path).get("target_version") or "").strip()


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

    # Deliberately self-contained: the updater must remain usable even if the
    # launcher's GUI stack is broken. Tk ships with CPython and PyInstaller.
    root = tk.Tk()
    root.title("MCW Updater")
    root.resizable(False, False)
    root.configure(bg="#0b1220")

    width, height = 610, 430
    root.geometry(f"{width}x{height}")
    root.update_idletasks()
    x = max(0, (root.winfo_screenwidth() - width) // 2)
    y = max(0, (root.winfo_screenheight() - height) // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    try:
        root.iconbitmap(str(_resource_path("assets/icons/mcw_launcher.ico")))
    except Exception:
        pass

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "MCW.Horizontal.TProgressbar",
        troughcolor="#172033",
        background="#63a4ff",
        bordercolor="#172033",
        lightcolor="#63a4ff",
        darkcolor="#63a4ff",
        thickness=12,
    )

    container = tk.Frame(root, bg="#0b1220", padx=34, pady=28)
    container.pack(fill="both", expand=True)

    header = tk.Frame(container, bg="#0b1220")
    header.pack(fill="x")

    logo_image = None
    try:
        logo_image = tk.PhotoImage(file=str(_resource_path("assets/icons/mcw_launcher.png")))
        # Source logo is 512x512; 6x subsampling yields an ~85px mark without Pillow.
        logo_image = logo_image.subsample(6, 6)
        logo = tk.Label(header, image=logo_image, bg="#0b1220", bd=0)
        logo.pack(side="left", padx=(0, 18))
    except Exception:
        logo = tk.Label(
            header,
            text="MCW",
            fg="#ffffff",
            bg="#172033",
            font=("Segoe UI", 18, "bold"),
            width=5,
            height=2,
        )
        logo.pack(side="left", padx=(0, 18))

    heading = tk.Frame(header, bg="#0b1220")
    heading.pack(side="left", fill="x", expand=True)
    tk.Label(
        heading,
        text="MCW Updater",
        fg="#f8fafc",
        bg="#0b1220",
        font=("Segoe UI", 20, "bold"),
        anchor="w",
    ).pack(fill="x")
    target_version = _request_target_version(request_path)
    target_text = f"Updating MCW Launcher to {target_version}" if target_version else "Updating MCW Launcher"
    tk.Label(
        heading,
        text=target_text,
        fg="#94a3b8",
        bg="#0b1220",
        font=("Segoe UI", 10),
        anchor="w",
    ).pack(fill="x", pady=(4, 0))

    card = tk.Frame(container, bg="#111a2b", padx=22, pady=20, highlightthickness=1, highlightbackground="#22304a")
    card.pack(fill="x", pady=(28, 0))

    status_var = tk.StringVar(value="Preparing secure update...")
    detail_var = tk.StringVar(value="The launcher will close only after the updater is ready.")
    tk.Label(
        card,
        textvariable=status_var,
        fg="#f8fafc",
        bg="#111a2b",
        font=("Segoe UI", 11, "bold"),
        anchor="w",
    ).pack(fill="x")
    tk.Label(
        card,
        textvariable=detail_var,
        fg="#94a3b8",
        bg="#111a2b",
        font=("Segoe UI", 9),
        anchor="w",
        justify="left",
        wraplength=500,
    ).pack(fill="x", pady=(6, 14))

    progress = ttk.Progressbar(card, style="MCW.Horizontal.TProgressbar", mode="determinate", maximum=100, length=500)
    progress.pack(fill="x")
    progress["value"] = 6

    footer = tk.Frame(container, bg="#0b1220")
    footer.pack(fill="x", pady=(18, 0))
    phase_var = tk.StringVar(value="Initializing updater")
    tk.Label(
        footer,
        textvariable=phase_var,
        fg="#64748b",
        bg="#0b1220",
        font=("Segoe UI", 9),
        anchor="w",
    ).pack(side="left")
    tk.Label(
        footer,
        text="Safe update • automatic rollback",
        fg="#64748b",
        bg="#0b1220",
        font=("Segoe UI", 9),
        anchor="e",
    ).pack(side="right")

    root.protocol("WM_DELETE_WINDOW", lambda: None)
    root.update_idletasks()

    results: queue.Queue[int] = queue.Queue(maxsize=1)
    _signal_ready(request_path)

    def worker() -> None:
        results.put(run_update_applier(request_path))

    threading.Thread(target=worker, name="mcw-updater-apply", daemon=True).start()

    last_line = ""
    log_path = request_path.parent / "update.log"

    def map_progress(message: str) -> tuple[int, str, str]:
        low = message.casefold()
        if "waiting for launcher process" in low:
            return 12, "Waiting for MCW Launcher to close", "The updater is waiting for the current launcher process to exit safely."
        if "remaining launcher process" in low:
            return 18, "Waiting for launcher processes", message
        if "executable lock" in low or "replaceable" in low or "fully stopped" in low:
            return 24, "Confirming launcher file is unlocked", message
        if "creating rollback backup" in low:
            return 34, "Creating recovery backup", "A rollback copy is being prepared before any launcher file is changed."
        if "replacing launcher executable" in low:
            return 50, "Updating launcher executable", "Replacing the main launcher only after Windows released the file lock."
        if "copying update from" in low:
            return 61, "Installing update files", "Applying the verified release payload."
        if "cleaning obsolete launcher path" in low:
            return 78, "Cleaning old files", message
        if "starting updated launcher" in low:
            return 92, "Starting MCW Launcher", "The update is installed and the new launcher is starting."
        if "completed" in low:
            return 100, "Update complete", "MCW Launcher was updated successfully."
        if "failed" in low or "rollback" in low:
            return max(int(progress["value"]), 10), "Recovery in progress", message
        return int(progress["value"]), message, "MCW Updater is continuing the installation."

    def poll() -> None:
        nonlocal last_line
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                line = text.splitlines()[-1]
                if line != last_line:
                    last_line = line
                    message = line.split("] ", 1)[-1]
                    value, title, detail = map_progress(message)
                    progress["value"] = value
                    status_var.set(title)
                    detail_var.set(detail)
                    phase_var.set(message[:74])
        except OSError:
            pass

        try:
            code = results.get_nowait()
        except queue.Empty:
            root.after(120, poll)
            return

        if code == 0:
            progress["value"] = 100
            status_var.set("Update complete")
            detail_var.set("MCW Launcher has been updated successfully and is starting now.")
            phase_var.set("Completed")
            delay = 1100
        else:
            status_var.set("Update could not be completed")
            detail_var.set("MCW Updater stopped safely and attempted automatic recovery. Check the updater log for details.")
            phase_var.set("Recovery / failure")
            delay = 2600
        root.update_idletasks()
        root.after(delay, root.destroy)
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
