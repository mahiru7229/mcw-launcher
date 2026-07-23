from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import tempfile
import traceback


def _run_update_mode() -> int | None:
    if len(sys.argv) < 2 or sys.argv[1] != "--apply-update":
        return None
    if len(sys.argv) != 3:
        return 2

    from src.core.update.update_applier import run_update_applier

    return run_update_applier(Path(sys.argv[2]))


def _start_update_cleanup() -> None:
    from src.core.update.update_cleanup import UpdateCleanupWorker, consume_update_cleanup_arguments

    cleaned_arguments, cleanup_request = consume_update_cleanup_arguments(sys.argv)
    sys.argv = cleaned_arguments
    if cleanup_request is not None:
        UpdateCleanupWorker(cleanup_request).start()


def _write_startup_error(error: BaseException) -> Path | None:
    payload = (
        f"MCW Launcher startup failure\n"
        f"Timestamp: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Error: {type(error).__name__}: {error}\n\n"
        f"{traceback.format_exc()}"
    )

    candidate_directories: list[Path] = []
    try:
        from src.core.fs.paths import Paths

        candidate_directories.append(Paths.LOGS_ROOT)
    except Exception:
        pass

    candidate_directories.append(Path(tempfile.gettempdir()) / "MCW Launcher")
    for directory in candidate_directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / "startup-error.log"
            path.write_text(payload, encoding="utf-8")
            return path
        except OSError:
            continue
    return None


def main() -> None:
    update_result = _run_update_mode()
    if update_result is not None:
        raise SystemExit(update_result)

    _start_update_cleanup()

    from src.gui.application import create_application
    from src.gui.startup_splash import StartupSplash

    app = create_application(sys.argv)
    splash = StartupSplash()
    splash.show()
    splash.update_progress(2, "startup.starting")

    try:
        from src.core.bootstrap import initialize_application

        settings = initialize_application(splash.update_progress)

        from src.core.language.language_manager import language_manager, tr

        language_manager.reload()
        language_manager.set_language(settings.get("gui", {}).get("language", "en-US"), notify=False)
        splash.retranslate()
        splash.update_progress(93, "startup.loading_interface")

        # Import the main window only after writable directories and databases are ready.
        # Some GUI controllers load account data during import or construction.
        from src.gui.main_window_2 import MainWindow

        window = MainWindow()
        splash.update_progress(99, "startup.finalizing")
        window.show()
        app.processEvents()
        splash.update_progress(100, "startup.ready", "startup.ready_detail")
        splash.finish(window)
    except Exception as error:
        from PySide6.QtWidgets import QMessageBox
        from src.core.language.language_manager import tr

        error_path = _write_startup_error(error)
        splash.show_error()
        path_text = str(error_path) if error_path is not None else tr("startup.error_log_unavailable")
        QMessageBox.critical(None, tr("startup.failed_title"), tr("startup.failed_message", error=error, path=path_text))
        splash.close()
        raise SystemExit(1) from None

    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
