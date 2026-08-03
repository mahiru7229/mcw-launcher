from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from mcw_core.api.language.language_manager import tr
from src.gui.presenters.progress_presenter import ProgressPresenter
from src.models.progress.progress_state import ProgressState
from src.gui.theme.runtime import set_theme_icon, set_theme_static_text
from src.gui.widget.themed_animated_label import ThemedAnimatedLabel
from src.gui.widget.themed_progress_bar import ThemedProgressBar

if TYPE_CHECKING:
    from src.gui.animation.motion_runtime import MotionRuntime


class LaunchControlWidget(QFrame):
    launch_clicked = Signal()
    cancel_clicked = Signal()

    LAUNCH_TEXT = "launch.button"
    PAUSE_TEXT = "launch.pause_button"
    RESUME_TEXT = "launch.resume_button"
    CANCEL_TEXT = "launch.cancel_button"

    def __init__(self, compact: bool = False) -> None:
        super().__init__()
        self.setObjectName("LaunchControl")
        self._compact = bool(compact)
        self.setProperty("compactLayout", self._compact)
        self._mode = "idle"
        self._last_event: object | None = None
        self._last_result: dict | None = None
        self._last_error_status = "Launch failed"
        self._last_error_detail = "launch.error.logs_hint"
        self._last_completed_status = "Task completed"
        self._last_completed_detail = "Everything is ready."
        self._last_exit_result: object | None = None
        self._status_message = "Ready"
        self._detail_message = "Select an account and an instance, then launch."
        self._stage_state: str | None = None
        self._motion_runtime: MotionRuntime | None = None
        self._busy = False
        self._launch_active = False
        self._pause_pending = False
        self._download_paused = False
        self._cancel_pending = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        if self._compact:
            layout.setContentsMargins(14, 9, 14, 9)
            layout.setSpacing(12)
        else:
            layout.setContentsMargins(20, 14, 20, 14)
            layout.setSpacing(18)

        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(6)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(10)

        stage_icon_size = 26 if self._compact else 32
        self.stage_icon = ThemedAnimatedLabel("state.ready", "icon.state.ready", stage_icon_size, stage_icon_size)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("ValueLabel")

        self.stage_label = QLabel("READY")
        self.stage_label.setObjectName("StageBadge")
        self.stage_label.setProperty("state", "success")

        status_row.addWidget(self.stage_icon)
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.stage_label)

        self.detail_label = QLabel("Select an account and an instance, then launch.")
        self.detail_label.setObjectName("TinyLabel")
        self.detail_label.setWordWrap(True)

        self.progress_bar = ThemedProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")

        progress_layout.addLayout(status_row)
        progress_layout.addWidget(self.detail_label)
        progress_layout.addWidget(self.progress_bar)

        self.controls_widget = QWidget()
        self.controls_widget.setMinimumWidth(260 if self._compact else 340)
        self.controls_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self.launch_button = set_theme_icon(QPushButton(tr(self.LAUNCH_TEXT)), "icon.action.launch", 26 if self._compact else 32)
        set_theme_static_text(self.launch_button, "control.launch", tr(self.LAUNCH_TEXT))
        self.launch_button.setObjectName("PrimaryButton")
        self.launch_button.setProperty("themeRole", "launch")
        self.launch_button.setMinimumHeight(36 if self._compact else 48)
        self.launch_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.launch_button.clicked.connect(self.launch_clicked.emit)

        self.cancel_button = set_theme_icon(QPushButton(tr(self.CANCEL_TEXT)), "icon.action.cancel", 18 if self._compact else 20)
        set_theme_static_text(self.cancel_button, "control.cancel", tr(self.CANCEL_TEXT))
        self.cancel_button.setObjectName("SecondaryButton")
        self.cancel_button.setProperty("themeRole", "cancel")
        self.cancel_button.setProperty("motionVisibilityOnly", True)
        self.cancel_button.setProperty("motionVisibleTarget", False)
        self.cancel_button.setMinimumHeight(36 if self._compact else 48)
        self.cancel_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        self.cancel_button.setVisible(False)

        controls_layout.addWidget(self.launch_button, 1)
        controls_layout.addWidget(self.cancel_button, 1)

        layout.addLayout(progress_layout, 1)
        layout.addWidget(self.controls_widget)

    def set_motion_runtime(self, runtime: "MotionRuntime | None") -> None:
        self._motion_runtime = runtime
        if runtime is not None:
            runtime.animate_visibility(self.cancel_button, self._launch_active)

    def set_selected_instance(self, _instance: object | None) -> None:
        self._refresh_launch_button()

    def set_status(self, message: str, detail: str | None = None) -> None:
        self._status_message = message
        self.status_label.setText(tr(message))

        if detail is not None:
            self._detail_message = detail
            self.detail_label.setText(tr(detail))

    def set_progress_event(self, event: object) -> None:
        self._last_event = event
        view = ProgressPresenter.present(event)

        if view.state is ProgressState.FAILED:
            self.set_failed(view.title, view.detail)
            return
        if view.state is ProgressState.CANCELLED:
            self.set_cancelled(view.title, view.detail)
            return
        if view.state is ProgressState.SUCCEEDED:
            self.set_operation_completed(view.title, view.detail)
            return

        self._mode = "progress"
        self.status_label.setText(view.title)
        self.detail_label.setText(view.detail)
        self.stage_label.setText(view.stage_text)
        self._set_stage_state("busy")

        if view.percentage is None:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("")
            return

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(view.percentage)
        self.progress_bar.setFormat(f"{view.percentage}%")

    def set_result(self, result: dict) -> None:
        self._mode = "result"
        self._last_result = dict(result)
        version = result.get("minecraftVersion", "unknown")
        java_path = result.get("javaPath", "unknown")

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100%")
        warnings = tuple(result.get("warnings", ()) or ())
        if warnings:
            self.status_label.setText(tr("Minecraft {version} launched with warnings", version=version))
            self.detail_label.setText(str(warnings[0]))
            self.stage_label.setText(tr("WARNING"))
            self._set_stage_state("warning")
        else:
            self.status_label.setText(tr("Minecraft {version} launched", version=version))
            self.detail_label.setText(tr("Java: {path}", path=java_path))
            self.stage_label.setText(tr("RUNNING"))
            self._set_stage_state("success")
        self._refresh_launch_button()



    def set_operation_completed(self, status: str, detail: str) -> None:
        self._mode = "operation_completed"
        self._last_completed_status = status or "Task completed"
        self._last_completed_detail = detail or "Everything is ready."
        self._busy = False
        self._launch_active = False
        self._pause_pending = False
        self._download_paused = False
        self._cancel_pending = False
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100%")
        self.status_label.setText(tr(self._last_completed_status))
        self.detail_label.setText(tr(self._last_completed_detail))
        self.stage_label.setText(tr("READY"))
        self._set_stage_state("success")
        self._refresh_launch_button()

    def set_exit_result(self, result: object) -> None:
        self._mode = "exit"
        self._last_exit_result = result
        crashed = bool(getattr(result, "crashed", False))
        instance_name = str(getattr(result, "instance_name", "Minecraft"))
        exit_code = int(getattr(result, "exit_code", -1))
        duration_seconds = max(0, int(getattr(result, "duration_seconds", 0)))
        minutes, seconds = divmod(duration_seconds, 60)
        duration = tr("{minutes}m {seconds}s", minutes=minutes, seconds=seconds)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0 if crashed else 100)
        self.progress_bar.setFormat(tr("CRASHED") if crashed else tr("FINISHED"))
        if crashed:
            self.status_label.setText(tr("Minecraft crashed: {name}", name=instance_name))
            self.detail_label.setText(tr("Exit code: {code} • Play time: {duration}", code=exit_code, duration=duration))
            self.stage_label.setText(tr("CRASHED"))
            self._set_stage_state("error")
        else:
            self.status_label.setText(tr("Minecraft closed normally: {name}", name=instance_name))
            self.detail_label.setText(tr("Play time: {duration}", duration=duration))
            self.stage_label.setText(tr("FINISHED"))
            self._set_stage_state("success")
        self._refresh_launch_button()

    def set_failed(self, status: str = "Launch failed", detail: str | None = None) -> None:
        self._mode = "failed"
        self._last_error_status = status or "Launch failed"
        self._last_error_detail = detail or "launch.error.logs_hint"
        status_text = self._compact_failure_text(self._last_error_status, "Launch failed", 120)
        detail_text = self._compact_failure_text(self._last_error_detail, "launch.error.logs_hint", 180)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(tr("FAILED"))
        self.status_label.setText(status_text)
        self.detail_label.setText(detail_text)
        self.stage_label.setText(tr("FAILED"))
        self._set_stage_state("error")
        self._refresh_launch_button()

    def set_cancelled(self, status: str = "Task cancelled", detail: str | None = None) -> None:
        self._mode = "cancelled"
        self._last_error_status = status or "Task cancelled"
        self._last_error_detail = detail or "progress.cancelled.detail"
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(tr("CANCELLED"))
        self.status_label.setText(tr(self._last_error_status))
        self.detail_label.setText(tr(self._last_error_detail))
        self.stage_label.setText(tr("CANCELLED"))
        self._set_stage_state("warning")
        self._refresh_launch_button()

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self._refresh_launch_button()

    def set_launch_active(self, active: bool) -> None:
        self._launch_active = bool(active)
        if not self._launch_active:
            self._pause_pending = False
            self._download_paused = False
            self._cancel_pending = False
        self._refresh_launch_button()

    def set_pause_pending(self) -> None:
        if not self._launch_active:
            return
        self._pause_pending = True
        self.status_label.setText(tr("launch.pause_requested"))
        self.detail_label.setText(tr("launch.pause_requested_detail"))
        self.stage_label.setText(tr("launch.pausing_badge"))
        self._set_stage_state("warning")
        self._refresh_launch_button()

    def set_paused(self) -> None:
        self._mode = "paused"
        self._launch_active = True
        self._download_paused = True
        self._pause_pending = False
        self._cancel_pending = False
        self.status_label.setText(tr("launch.paused"))
        self.detail_label.setText(tr("launch.paused_detail"))
        self.stage_label.setText(tr("launch.paused_badge"))
        self.progress_bar.setFormat(tr("launch.paused_badge"))
        self._set_stage_state("warning")
        self._refresh_launch_button()

    def set_resumed(self) -> None:
        if not self._launch_active:
            return
        self._mode = "progress"
        self._download_paused = False
        self._pause_pending = False
        self._cancel_pending = False
        self.status_label.setText(tr("launch.resumed"))
        self.detail_label.setText(tr("launch.resumed_detail"))
        self.stage_label.setText(tr("launch.running_badge"))
        self.progress_bar.setFormat("%p%")
        self._set_stage_state("busy")
        self._refresh_launch_button()

    def set_cancel_pending(self) -> None:
        if not self._launch_active:
            return
        self._cancel_pending = True
        self._pause_pending = False
        self.status_label.setText(tr("launch.cancel_requested"))
        self.detail_label.setText(tr("launch.cancel_requested_detail"))
        self.stage_label.setText(tr("launch.cancelling_badge"))
        self._set_stage_state("warning")
        self._refresh_launch_button()

    def reset_progress(self) -> None:
        self._mode = "idle"
        self._busy = False
        self._launch_active = False
        self._pause_pending = False
        self._download_paused = False
        self._cancel_pending = False
        self._status_message = "Ready"
        self._detail_message = "Select an account and an instance, then launch."
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.status_label.setText(tr("Ready"))
        self.detail_label.setText(tr("Select an account and an instance, then launch."))
        self.stage_label.setText(tr("READY"))
        self._set_stage_state("success")
        self._refresh_launch_button()

    def _refresh_launch_button(self) -> None:
        if self._launch_active and self._download_paused:
            text_key = self.RESUME_TEXT
            static_role = "control.launch"
            theme_role = "launch"
        elif self._launch_active:
            text_key = self.PAUSE_TEXT
            static_role = "control.launch"
            theme_role = "launch"
        else:
            text_key = self.LAUNCH_TEXT
            static_role = "control.launch"
            theme_role = "launch"

        button_text = tr(text_key)
        self.launch_button.setProperty("themeRole", theme_role)
        self.launch_button.setProperty("themeStaticTextRole", static_role)
        self.launch_button.setProperty("themeStaticTextFallback", button_text)
        self.launch_button.setEnabled((self._launch_active and not self._pause_pending and not self._cancel_pending) or (not self._launch_active and not self._busy))

        if bool(self.launch_button.property("themeStaticTextHidden")) and not self._launch_active:
            self.launch_button.setText("")
        elif self.launch_button.text() != button_text:
            self.launch_button.setText(button_text)

        cancel_text = tr(self.CANCEL_TEXT)
        if self._motion_runtime is not None:
            self._motion_runtime.animate_visibility(self.cancel_button, self._launch_active)
        else:
            self.cancel_button.setVisible(self._launch_active)
        self.cancel_button.setEnabled(self._launch_active and not self._cancel_pending)
        self.cancel_button.setProperty("themeStaticTextFallback", cancel_text)
        if bool(self.cancel_button.property("themeStaticTextHidden")):
            self.cancel_button.setText("")
        elif self.cancel_button.text() != cancel_text:
            self.cancel_button.setText(cancel_text)

        for button in (self.launch_button, self.cancel_button):
            button.style().unpolish(button)
            button.style().polish(button)

    def retranslate_dynamic(self) -> None:
        if self._mode == "progress" and self._last_event is not None:
            self.set_progress_event(self._last_event)
        elif self._mode == "result" and self._last_result is not None:
            self.set_result(self._last_result)
        elif self._mode == "failed":
            self.set_failed(self._last_error_status, self._last_error_detail)
        elif self._mode == "paused":
            self.set_paused()
        elif self._mode == "cancelled":
            self.set_cancelled(self._last_error_status, self._last_error_detail)
        elif self._mode == "operation_completed":
            self.set_operation_completed(self._last_completed_status, self._last_completed_detail)
        elif self._mode == "exit" and self._last_exit_result is not None:
            self.set_exit_result(self._last_exit_result)
        else:
            self.status_label.setText(tr(self._status_message))
            self.detail_label.setText(tr(self._detail_message))
            self.stage_label.setText(tr("READY"))
            self._refresh_launch_button()

    @staticmethod
    def _compact_failure_text(value: str, fallback: str, max_length: int) -> str:
        translated = tr(value or fallback)
        compact = " ".join(str(translated).split())
        if not compact or len(compact) > max_length:
            return tr(fallback)
        return compact

    def _set_stage_state(self, state: str) -> None:
        icon_state = "ready" if state == "success" and self._mode in {"idle", "operation_completed"} else state
        state_key = f"{state}:{icon_state}"
        if self._stage_state == state_key:
            return
        self._stage_state = state_key
        self.stage_icon.set_theme_state(f"state.{icon_state}", f"icon.state.{icon_state}")
        self.stage_label.setProperty("state", state)
        self.stage_label.style().unpolish(self.stage_label)
        self.stage_label.style().polish(self.stage_label)
        if self._motion_runtime is not None:
            self._motion_runtime.pulse(self.stage_label)
