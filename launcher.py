from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import tempfile
import traceback


def _start_update_cleanup() -> None:
    from mcw_core.api.update.update_cleanup import UpdateCleanupWorker, consume_update_cleanup_arguments

    cleaned_arguments, cleanup_request = consume_update_cleanup_arguments(sys.argv)
    sys.argv = cleaned_arguments
    if cleanup_request is not None:
        UpdateCleanupWorker(cleanup_request).start()


def _write_startup_error(error: BaseException, stage_key: str = "startup.starting", traceback_text: str | None = None) -> Path | None:
    payload = (
        f"MCW Launcher startup failure\n"
        f"Timestamp: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Stage: {stage_key}\n"
        f"Error: {type(error).__name__}: {error}\n\n"
        f"{traceback_text or traceback.format_exc()}"
    )

    candidate_directories: list[Path] = []
    try:
        from mcw_core.api.fs.paths import Paths

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


def _validate_startup_dependencies(project_root: Path | None = None) -> None:
    """Fail early with one actionable error when a source checkout is incomplete.

    PyInstaller validates bundled modules during the build, so this filesystem
    check is only needed for source-mode patch installs. It prevents a chain of
    one-module-at-a-time ImportError failures after a partial patch extraction.
    """

    if getattr(sys, "frozen", False):
        return

    root = project_root or Path(__file__).resolve().parent
    required_paths = (
        Path("src/core/curseforge/curseforge_errors.py"),
        Path("src/core/lan/lan_agent_manager.py"),
        Path("src/core/lan/lan_agent_target_resolver.py"),
        Path("src/core/lan/lan_hosting_manager.py"),
        Path("src/core/repair/repair_service.py"),
        Path("src/core/network/download_manager.py"),
        Path("src/core/network/download_models.py"),
        Path("src/core/network/download_journal.py"),
        Path("src/core/network/network_errors.py"),
        Path("src/core/network/network_session.py"),
        Path("src/core/network/retry_policy.py"),
        Path("src/gui/dialogs/repair_center_dialog.py"),
        Path("runtime/mcw-lan-agent.jar"),
    )
    missing = [str(relative_path).replace("\\", "/") for relative_path in required_paths if not (root / relative_path).is_file()]
    if missing:
        joined = "\n- ".join(missing)
        raise RuntimeError(
            "MCW Launcher installation is incomplete. Reapply the complete "
            "source package or reinstall the current release before starting "
            "the launcher. Missing files:\n- "
            f"{joined}"
        )


def _find_recovery_executable() -> Path | None:
    if getattr(sys, "frozen", False):
        launcher_dir = Path(sys.executable).resolve().parent
    else:
        launcher_dir = Path(__file__).resolve().parent

    candidates = [
        launcher_dir / "updater" / "MCW Updater.exe",
        launcher_dir / "updater" / "mcw-updater",
        launcher_dir / "updater.py",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _launch_recovery_tool(executable: Path) -> None:
    import os
    import subprocess

    cmd = [str(executable), "--recovery"]
    if executable.suffix == ".py":
        cmd = [sys.executable, str(executable), "--recovery"]
    parent_dir = executable.parent.parent if executable.parent.name == "updater" else executable.parent
    kwargs: dict = {"cwd": str(parent_dir)}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen(cmd, **kwargs)
    except Exception:
        pass


def main() -> None:
    _start_update_cleanup()

    from src.gui.application import create_application
    from src.gui.startup_splash import StartupSplash

    app = create_application(sys.argv)
    from mcw_core.api.network.network_session import network_session
    app.aboutToQuit.connect(network_session.close)
    splash = StartupSplash()
    splash.show()
    splash.update_progress(2, "startup.starting")
    startup_stage_key = "startup.starting"

    try:
        from mcw_core.api.bootstrap import initialize_application
        from mcw_core.api.startup_runner import run_startup_task

        def update_startup_progress(percent: int, message_key: str) -> None:
            nonlocal startup_stage_key
            startup_stage_key = str(message_key)
            splash.update_progress(percent, startup_stage_key)

        settings = run_startup_task(initialize_application, update_startup_progress, app.processEvents)

        from mcw_core.api.theme.theme_manager import theme_manager
        from src.gui.theme.font_runtime import theme_font_runtime

        appearance_settings = settings.get("appearance", {}) if isinstance(settings, dict) else {}
        theme_manager.reload()
        selected_theme = theme_manager.select(str(appearance_settings.get("theme", "mcw-default")))
        theme_font_runtime.apply(app, selected_theme)
        splash.update()
        app.processEvents()

        from mcw_core.api.language.language_manager import language_manager, tr

        language_manager.reload()
        language_manager.set_language(settings.get("gui", {}).get("language", "en-US"), notify=False)
        splash.retranslate()

        from mcw_core.api.hardware.gpu_preference_manager import GpuPreferenceManager

        def detect_graphics(progress_callback):
            progress_callback(91, "startup.detecting_graphics")
            return GpuPreferenceManager.detect()

        gpu_detection = run_startup_task(detect_graphics, update_startup_progress, app.processEvents, timeout_seconds=12.0)

        from mcw_core.api.hardware.first_run_recommendation_service import FirstRunRecommendationService

        first_run_recommendation = FirstRunRecommendationService.fallback()
        onboarding = settings.get("onboarding", {}) if isinstance(settings, dict) else {}
        if not bool(onboarding.get("completed", False)):
            def inspect_first_run_defaults(progress_callback):
                progress_callback(92, "startup.inspecting_runtime")
                return FirstRunRecommendationService.inspect()

            try:
                first_run_recommendation = run_startup_task(inspect_first_run_defaults, update_startup_progress, app.processEvents, timeout_seconds=25.0)
            except Exception:
                # Hardware discovery is advisory and must never prevent startup.
                first_run_recommendation = FirstRunRecommendationService.fallback()
        startup_stage_key = "startup.loading_interface"
        splash.update_progress(93, startup_stage_key)

        _validate_startup_dependencies()

        # Import and construct Qt widgets only on the GUI thread. Persistent I/O
        # above is isolated so a locked database cannot freeze the splash forever.
        from src.gui.main_window import MainWindow

        window = MainWindow(gpu_detection)
        startup_stage_key = "startup.finalizing"
        splash.update_progress(99, startup_stage_key)
        window.show()
        app.processEvents()
        startup_stage_key = "startup.ready"
        splash.update_progress(100, startup_stage_key, "startup.ready_detail")
        splash.finish(window)

        from PySide6.QtWidgets import QDialog
        from mcw_core.api.config.launcher_settings_manager import LauncherSettingsManager
        from src.gui.dialogs.first_run_setup_dialog import FirstRunSetupDialog

        if FirstRunSetupDialog.should_show(settings):
            setup_dialog = FirstRunSetupDialog(settings, gpu_detection, first_run_recommendation, window)
            if setup_dialog.exec() == QDialog.DialogCode.Accepted:
                LauncherSettingsManager().save(setup_dialog.selected_settings())
                window.gui_settings_controller.load()
                window.launcher_settings_page.set_gpu_detection(gpu_detection)
    except Exception as error:
        from PySide6.QtWidgets import QMessageBox
        from mcw_core.api.language.language_manager import tr
        from mcw_core.api.startup_runner import StartupWorkerError

        traceback_text = error.traceback_text if isinstance(error, StartupWorkerError) else traceback.format_exc()
        error_path = _write_startup_error(error, startup_stage_key, traceback_text)
        splash.show_error()
        splash.raise_()
        splash.activateWindow()
        msg_box = QMessageBox(splash)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(tr("startup.failed_title"))
        msg_box.setText(tr("startup.failed_message", error=error, stage=stage_text, path=path_text))

        recovery_exe = _find_recovery_executable()
        recovery_btn = None
        if recovery_exe is not None:
            recovery_btn = msg_box.addButton(tr("startup.open_recovery_tool"), QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton(QMessageBox.StandardButton.Close)

        msg_box.exec()
        if recovery_btn is not None and msg_box.clickedButton() == recovery_btn:
            _launch_recovery_tool(recovery_exe)

        splash.close()
        raise SystemExit(1) from None

    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
