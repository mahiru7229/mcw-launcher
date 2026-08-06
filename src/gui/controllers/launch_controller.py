from __future__ import annotations

from threading import Lock
from typing import Any

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr
from mcw_core.api.package.portable_content_manager import PortableManualDownloadRequired
from src.gui.controllers.base_controller import BaseController
from src.gui.presenters.launch_error_presenter import LaunchErrorPresenter
from src.gui.task_runner import TaskRunner
from mcw_core import CompatibilityConfirmationRequired, LaunchRequest, ProgressEvent, get_default_core, is_download_cancelled, is_download_paused


class LaunchController(BaseController):
    progress_received = Signal(object)
    launch_finished = Signal(object)
    game_exited = Signal(object)
    pause_requested = Signal()
    launch_paused = Signal()
    launch_resumed = Signal()
    cancel_requested = Signal()
    launch_cancelled = Signal()
    portable_manual_download_required = Signal(object)
    compatibility_confirmation_required = Signal(object)

    TASK_ID = "minecraft.launch"

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()

        self._task_runner = task_runner
        self._core = get_default_core()
        self._selected_instance = None
        self._selected_account = None
        self._debug_mode = False
        self._progress_log_lock = Lock()
        self._last_progress_log_key: tuple[object, ...] | None = None

        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def set_instance(self, instance: object | None) -> None:
        self._selected_instance = instance

    def set_account(self, account: object | None) -> None:
        self._selected_account = account

    def set_debug_mode(self, enabled: bool) -> None:
        self._debug_mode = enabled

    def launch(self, allow_compatibility_issues_once: bool = False) -> None:
        if self._task_runner.is_task_active(self.TASK_ID):
            if self._core.operations.state.paused:
                self.resume()
            else:
                self.pause()
            return

        if self._selected_instance is None:
            self._emit_error(tr("Launch Minecraft"), tr("Select an instance first."))
            return

        if self._selected_account is None:
            self._emit_error(tr("Launch Minecraft"), tr("Create or select an account first."))
            return

        instance_name = self._selected_instance.name
        account = self._selected_account
        debug_mode = self._debug_mode

        def task() -> dict[str, Any]:
            try:
                self._core.operations.checkpoint()
                result = self._core.launch(
                    LaunchRequest(
                        instance=instance_name,
                        account=account,
                        debug_mode=debug_mode,
                        on_progress=self._on_progress,
                        on_exit=self._on_game_exit,
                        allow_compatibility_issues_once=allow_compatibility_issues_once,
                    )
                )
                return result.as_dict()
            finally:
                self._core.operations.finish()

        self._core.operations.begin()
        started = self._task_runner.run(self.TASK_ID, task, tr("Launching '{name}'...", name=instance_name))
        if not started:
            self._core.operations.finish()

    def pause(self) -> None:
        if not self._core.operations.pause():
            return
        self.pause_requested.emit()
        self.launch_paused.emit()
        self.status_changed.emit(tr("launch.paused"))
        self.log_created.emit(tr("launch.paused_log"))

    def resume(self) -> None:
        if not self._core.operations.resume():
            return
        self.launch_resumed.emit()
        self.status_changed.emit(tr("launch.resumed"))
        self.log_created.emit(tr("launch.resumed_log"))

    def cancel(self) -> None:
        if not self._core.operations.cancel():
            return
        self.cancel_requested.emit()
        self.status_changed.emit(tr("launch.cancel_requested"))
        self.log_created.emit(tr("launch.cancel_requested_log"))

    def _on_progress(self, event: ProgressEvent) -> None:
        self.progress_received.emit(event)
        key = self._progress_log_key(event)
        with self._progress_log_lock:
            if key == self._last_progress_log_key:
                return
            self._last_progress_log_key = key
        self.log_created.emit(self._format_progress(event))

    @staticmethod
    def _progress_log_key(event: ProgressEvent) -> tuple[object, ...]:
        stage = getattr(getattr(event, "stage", None), "value", getattr(event, "stage", None))
        if not event.is_determinate:
            return stage, str(event.message), None
        percentage = int(event.percentage or 0)
        bucket = 100 if percentage >= 100 else (percentage // 10) * 10
        return stage, bucket


    def _on_game_exit(self, result: object) -> None:
        self.game_exited.emit(result)
        instance_name = str(getattr(result, "instance_name", "Minecraft"))
        exit_code = int(getattr(result, "exit_code", -1))
        crashed = bool(getattr(result, "crashed", exit_code != 0))
        if crashed:
            self.status_changed.emit(tr("Minecraft crashed: {name}", name=instance_name))
            self.log_created.emit(tr("Minecraft exited with code {code}: {name}", code=exit_code, name=instance_name))
        else:
            self.status_changed.emit(tr("Minecraft closed normally: {name}", name=instance_name))
            self.log_created.emit(tr("Minecraft exited normally: {name}", name=instance_name))

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id != self.TASK_ID:
            return

        self.launch_finished.emit(result)

        version = result.get("minecraftVersion", "unknown")
        warnings = tuple(result.get("warnings", ()) or ())
        if warnings:
            self.status_changed.emit(tr("Minecraft {version} launched with warnings", version=version))
            self.log_created.emit(tr("Minecraft process created with {count} warning(s): {version}", count=len(warnings), version=version))
            for warning in warnings:
                self.log_created.emit(tr("Launch warning: {warning}", warning=warning))
            return

        self.status_changed.emit(tr("Minecraft {version} launched", version=version))
        self.log_created.emit(tr("Minecraft process created successfully: {version}", version=version))

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id != self.TASK_ID:
            return

        if is_download_cancelled(error):
            self.launch_cancelled.emit()
            self.status_changed.emit(tr("launch.cancelled"))
            self.log_created.emit(tr("launch.cancelled_log"))
            return

        if is_download_paused(error):
            self.launch_paused.emit()
            self.status_changed.emit(tr("launch.paused"))
            self.log_created.emit(tr("launch.paused_log"))
            return

        if isinstance(error, CompatibilityConfirmationRequired):
            self.compatibility_confirmation_required.emit(error)
            self.status_changed.emit(tr("compatibility.confirmation.required"))
            self.log_created.emit(f"CompatibilityConfirmationRequired: {len(error.issues)} issue(s)")
            return

        if isinstance(error, PortableManualDownloadRequired):
            self.portable_manual_download_required.emit(error)
            self.status_changed.emit(tr("portable.manual.required", count=len(error.requirements)))
            self.log_created.emit(f"PortableManualDownloadRequired: {len(error.requirements)} file(s)")
            return

        view = LaunchErrorPresenter.present(error)

        self.status_changed.emit(view.status)
        self.log_created.emit(f"{type(error).__name__}: {error}")

    @staticmethod
    def _format_progress(event: ProgressEvent) -> str:
        stage = event.stage.value

        if event.is_determinate:
            return f"[{stage}] {event.message} {event.current}/{event.total} ({event.percentage or 0:.1f}%)"

        return f"[{stage}] {event.message}"
