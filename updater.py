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
        if "windows replacement transaction may begin" in low:
            return 24, "Preparing Windows executable transition", "The launcher process has exited. MCW Updater will now perform the real native replacement check."
        if "direct launcher replacement blocked" in low:
            return 46, "Windows is still holding the previous launcher", message
        if "rename-away fallback" in low:
            return 54, "Switching launcher safely", "The previous launcher image is being retired so the new executable can take its place."
        if "launcher transition is still blocked" in low:
            return 48, "Waiting for Windows to release the launcher", message
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


def _find_launcher_directory() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if exe_dir.name.casefold() == "updater":
            return exe_dir.parent
        return exe_dir
    current = Path.cwd()
    if (current / "launcher.py").is_file() or (current / "src").is_dir():
        return current
    return Path(__file__).resolve().parent


def _restore_backup(launcher_dir: Path) -> tuple[bool, str]:
    backup_dir = launcher_dir / "updater" / "backup"
    if not backup_dir.is_dir():
        return False, "Không tìm thấy thư mục sao lưu (updater/backup)."
    backup_files = [p for p in backup_dir.rglob("*") if p.is_file()]
    if not backup_files:
        return False, "Thư mục sao lưu trống."
    import shutil
    restored_count = 0
    for backup_file in backup_files:
        rel = backup_file.relative_to(backup_dir)
        dest = launcher_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(backup_file, dest)
            restored_count += 1
        except Exception as e:
            return False, f"Lỗi khi khôi phục {rel}: {e}"
    return True, f"Đã khôi phục thành công {restored_count} tệp từ bản sao lưu."


def _clear_stale_locks(launcher_dir: Path) -> int:
    cleared = 0
    patterns = [".*.part", "*.part", ".run_lock", ".startup_lock", "*.lock"]
    for pat in patterns:
        for p in launcher_dir.glob(pat):
            try:
                if p.is_file():
                    p.unlink()
                    cleared += 1
            except Exception:
                pass
    return cleared


def _restart_launcher(launcher_dir: Path) -> bool:
    import subprocess
    candidates = [
        launcher_dir / "MCW Launcher.exe",
        launcher_dir / "mcw-launcher",
        launcher_dir / "launcher.py",
    ]
    for exe in candidates:
        if exe.is_file():
            cmd = [str(exe)]
            if exe.suffix == ".py":
                cmd = [sys.executable, str(exe)]
            kwargs: dict = {"cwd": str(launcher_dir)}
            if sys.platform == "win32":
                kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            else:
                kwargs["start_new_session"] = True
            subprocess.Popen(cmd, **kwargs)
            return True
    return False


def _gui_recovery() -> int:
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except Exception:
        return _cli_recovery()

    launcher_dir = _find_launcher_directory()
    backup_dir = launcher_dir / "updater" / "backup"
    has_backup = backup_dir.is_dir() and any(backup_dir.iterdir())

    root = tk.Tk()
    root.title("MCW Launcher - Recovery & Repair Tool")
    root.geometry("540x360")
    root.minsize(500, 320)
    root.configure(bg="#0f172a")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background="#0f172a", foreground="#f8fafc")
    style.configure("TLabel", background="#0f172a", foreground="#e2e8f0", font=("Segoe UI", 10))
    style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#38bdf8")
    style.configure("Subtitle.TLabel", font=("Segoe UI", 9), foreground="#94a3b8")
    style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"), foreground="#4ade80" if has_backup else "#f87171")
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    title_label = ttk.Label(frame, text="MCW Launcher - Cứu hộ & Khôi phục", style="Title.TLabel")
    title_label.pack(anchor="w", pady=(0, 4))

    desc_label = ttk.Label(frame, text="Công cụ phục hồi khẩn cấp khi launcher gặp sự cố khởi động hoặc lỗi cập nhật.", style="Subtitle.TLabel")
    desc_label.pack(anchor="w", pady=(0, 16))

    info_frame = ttk.LabelFrame(frame, text=" Thông tin hệ thống ", padding=10)
    info_frame.pack(fill="x", pady=(0, 16))

    dir_lbl = ttk.Label(info_frame, text=f"Thư mục cài đặt: {launcher_dir}")
    dir_lbl.pack(anchor="w")

    status_text = "Có bản sao lưu phiên bản trước (Sẵn sàng khôi phục)" if has_backup else "Không có bản sao lưu trước đó"
    backup_lbl = ttk.Label(info_frame, text=f"Trạng thái sao lưu: {status_text}", style="Status.TLabel")
    backup_lbl.pack(anchor="w", pady=(4, 0))

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", pady=(8, 0))

    def on_restore():
        success, msg = _restore_backup(launcher_dir)
        if success:
            if messagebox.askyesno("Khôi phục thành công", f"{msg}\n\nBạn có muốn khởi động lại MCW Launcher ngay bây giờ không?"):
                _restart_launcher(launcher_dir)
                root.destroy()
        else:
            messagebox.showerror("Khôi phục thất bại", msg)

    def on_clear_locks():
        cleared = _clear_stale_locks(launcher_dir)
        messagebox.showinfo("Dọn dẹp khóa", f"Đã dọn dẹp {cleared} tệp khóa / tệp tạm.")

    restore_btn = tk.Button(
        btn_frame,
        text="Khôi phục phiên bản trước (Rollback)",
        bg="#0284c7" if has_backup else "#334155",
        fg="#ffffff",
        font=("Segoe UI", 10, "bold"),
        padx=12,
        pady=8,
        relief="flat",
        state=tk.NORMAL if has_backup else tk.DISABLED,
        command=on_restore,
    )
    restore_btn.pack(fill="x", pady=4)

    clean_btn = tk.Button(
        btn_frame,
        text="Dọn dẹp khóa & Tệp tạm (Clear Locks)",
        bg="#1e293b",
        fg="#e2e8f0",
        font=("Segoe UI", 9),
        padx=12,
        pady=6,
        relief="flat",
        command=on_clear_locks,
    )
    clean_btn.pack(fill="x", pady=4)

    close_btn = tk.Button(
        btn_frame,
        text="Đóng",
        bg="#0f172a",
        fg="#94a3b8",
        font=("Segoe UI", 9),
        padx=12,
        pady=4,
        relief="flat",
        command=root.destroy,
    )
    close_btn.pack(fill="x", pady=4)

    root.mainloop()
    return 0


def _cli_recovery() -> int:
    launcher_dir = _find_launcher_directory()
    print("=== MCW Launcher Emergency Recovery ===")
    print(f"Launcher Directory: {launcher_dir}")
    if "--clear-locks" in sys.argv:
        cleared = _clear_stale_locks(launcher_dir)
        print(f"Cleared {cleared} locks.")
        return 0
    if "--restore-backup" in sys.argv:
        success, msg = _restore_backup(launcher_dir)
        print(msg)
        if success and "--restart" in sys.argv:
            _restart_launcher(launcher_dir)
        return 0 if success else 1

    print("Usage:")
    print("  --recovery --restore-backup [--restart] : Restore previous version from backup")
    print("  --recovery --clear-locks               : Clear stale lock files")
    return 0


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] in {"--version", "-V"}:
        from src.config import VERSION_TAG
        print(f"MCW Updater {VERSION_TAG}")
        return 0

    if len(sys.argv) == 3 and sys.argv[1] == "--apply-update":
        request_path = Path(sys.argv[2])
        if sys.platform == "win32":
            return _gui_apply(request_path)
        return _headless_apply(request_path)

    if len(sys.argv) == 1 or (len(sys.argv) >= 2 and sys.argv[1] in {"--recovery", "--repair", "-r"}):
        if sys.platform == "win32" and not any(arg == "--cli" for arg in sys.argv):
            return _gui_recovery()
        return _cli_recovery()

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
