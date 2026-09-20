from __future__ import annotations

import time

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QVBoxLayout, QWidget

from mcw_core.api.language.language_manager import tr
from src.gui.core.task_queue import TaskQueue, TaskQueueItem
from src.gui.presenters.progress_presenter import ProgressPresenter
from src.gui.widget.elided_label import ElidedLabel


class GlobalTaskIndicator(QFrame):
    """Global task progress and status indicator card for MainWindow.

    Connects to GuiTaskQueue to display background task status, rich progress details,
    speed metrics, stage badge, Modrinth-style progress bar, and error notification.
    Designed with a clean 3-tier layout, robust performance throttling, and zero-flicker CSS caching.
    """

    def __init__(self, task_queue: TaskQueue | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GlobalTaskIndicator")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(380)
        self.setMaximumWidth(960)
        self.setMinimumHeight(62)

        self._queue: TaskQueue | None = None
        self._drawer: QWidget | None = None
        self._was_active = False
        self._last_failed_task: TaskQueueItem | None = None
        self._current_visual_state: str = ""

        # High-frequency progress throttling (cap UI redraws at ~30 FPS / 33ms)
        self._last_refresh_time: float = 0.0
        self._throttle_timer = QTimer(self)
        self._throttle_timer.setSingleShot(True)
        self._throttle_timer.timeout.connect(self._on_throttle_timeout)

        # Auto-hide timer after completion
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._on_hide_timeout)

        self._build_ui()
        self.setVisible(False)

        if task_queue is not None:
            self.attach_queue(task_queue)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(5)

        # 1. Hàng Trên (Top row): icon, stage badge, tên task
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        self.icon_label = QLabel(chr(0x27F3))  # ⟳ clock-wise open circle arrow
        self.icon_label.setObjectName("TaskIndicatorIcon")
        self.icon_label.setFixedWidth(16)
        self.icon_label.setFixedHeight(18)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px;")

        self.stage_badge = QLabel()
        self.stage_badge.setObjectName("TaskIndicatorStageBadge")
        self.stage_badge.setFixedHeight(18)
        self.stage_badge.setStyleSheet(
            "color: #38bdf8; background: #0c4a6e; border-radius: 4px; padding: 2px 7px; font-size: 9px; font-weight: bold;"
        )
        self.stage_badge.setVisible(False)

        self.text_label = ElidedLabel()
        self.text_label.setObjectName("TaskIndicatorText")
        self.text_label.setFixedHeight(18)
        self.text_label.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: 600;")
        self.text_label.setMinimumWidth(80)

        top_row.addWidget(self.icon_label)
        top_row.addWidget(self.stage_badge)
        top_row.addWidget(self.text_label, 1)

        # 2. Hàng Giữa (Middle row): thanh tiến trình Modrinth (dày 7px, bo góc đẹp)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("TaskIndicatorProgress")
        self.progress_bar.setFixedHeight(7)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.progress_bar.setTextVisible(False)

        # 3. Hàng Dưới (Bottom row): số liệu đầy đủ (dung lượng, tốc độ, %)
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(12)

        self.progress_detail_label = QLabel()
        self.progress_detail_label.setObjectName("TaskIndicatorDetailMetric")
        self.progress_detail_label.setFixedHeight(16)
        self.progress_detail_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 500;")

        self.speed_label = QLabel()
        self.speed_label.setObjectName("TaskIndicatorSpeed")
        self.speed_label.setFixedHeight(16)
        self.speed_label.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 500;")

        self.percent_label = QLabel()
        self.percent_label.setObjectName("TaskIndicatorPercent")
        self.percent_label.setFixedHeight(16)
        self.percent_label.setStyleSheet("color: #cbd5e1; font-size: 10px; font-weight: bold;")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        bottom_row.addWidget(self.progress_detail_label)
        bottom_row.addWidget(self.speed_label)
        bottom_row.addStretch(1)
        bottom_row.addWidget(self.percent_label)

        layout.addLayout(top_row)
        layout.addWidget(self.progress_bar)
        layout.addLayout(bottom_row)

        self._set_visual_state("normal")

    def _apply_normal_frame_style(self) -> None:
        self.setStyleSheet("""
            QFrame#GlobalTaskIndicator {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)

    def _apply_success_frame_style(self) -> None:
        self.setStyleSheet("""
            QFrame#GlobalTaskIndicator {
                background-color: #0b1914;
                border: 1px solid #166534;
                border-radius: 8px;
            }
        """)

    def _apply_error_frame_style(self) -> None:
        self.setStyleSheet("""
            QFrame#GlobalTaskIndicator {
                background-color: #1a0d10;
                border: 1px solid #ef4444;
                border-radius: 8px;
            }
        """)

    def _apply_normal_progress_style(self) -> None:
        self.progress_bar.setStyleSheet("""
            QProgressBar#TaskIndicatorProgress {
                background-color: #1e293b;
                border: none;
                border-radius: 3px;
            }
            QProgressBar#TaskIndicatorProgress::chunk {
                background-color: #00af5c;
                border-radius: 3px;
            }
        """)

    def _apply_success_progress_style(self) -> None:
        self.progress_bar.setStyleSheet("""
            QProgressBar#TaskIndicatorProgress {
                background-color: #14532d;
                border: none;
                border-radius: 3px;
            }
            QProgressBar#TaskIndicatorProgress::chunk {
                background-color: #00af5c;
                border-radius: 3px;
            }
        """)

    def _apply_error_progress_style(self) -> None:
        self.progress_bar.setStyleSheet("""
            QProgressBar#TaskIndicatorProgress {
                background-color: #3b181c;
                border: none;
                border-radius: 3px;
            }
            QProgressBar#TaskIndicatorProgress::chunk {
                background-color: #ef4444;
                border-radius: 3px;
            }
        """)

    def _set_visual_state(self, state: str) -> None:
        """Switch visual state only when changed to avoid costly Qt stylesheet re-polishing."""
        if self._current_visual_state == state:
            return
        self._current_visual_state = state

        if state == "normal":
            self._apply_normal_frame_style()
            self._apply_normal_progress_style()
            self.icon_label.setText(chr(0x27F3))
            self.icon_label.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px;")
            self.stage_badge.setStyleSheet(
                "color: #38bdf8; background: #0c4a6e; border-radius: 4px; padding: 2px 7px; font-size: 9px; font-weight: bold;"
            )
            self.text_label.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: 600;")
            self.progress_detail_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 500;")
            self.speed_label.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 500;")
            self.percent_label.setStyleSheet("color: #cbd5e1; font-size: 10px; font-weight: bold;")
        elif state == "success":
            self._apply_success_frame_style()
            self._apply_success_progress_style()
            self.icon_label.setText(chr(0x2713))
            self.icon_label.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 13px;")
            self.stage_badge.setStyleSheet(
                "color: #4ade80; background: #14532d; border-radius: 4px; padding: 2px 7px; font-size: 9px; font-weight: bold;"
            )
            self.text_label.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: 600;")
            self.progress_detail_label.setStyleSheet("color: #4ade80; font-size: 10px; font-weight: 500;")
            self.speed_label.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 500;")
            self.percent_label.setStyleSheet("color: #4ade80; font-size: 10px; font-weight: bold;")
        elif state == "error":
            self._apply_error_frame_style()
            self._apply_error_progress_style()
            self.icon_label.setText(chr(0x2715))
            self.icon_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px;")
            self.stage_badge.setStyleSheet(
                "color: #f87171; background: #451a1a; border-radius: 4px; padding: 2px 7px; font-size: 9px; font-weight: bold;"
            )
            self.text_label.setStyleSheet("color: #fca5a5; font-size: 11px; font-weight: 600;")
            self.progress_detail_label.setStyleSheet("color: #f87171; font-size: 10px; font-weight: 500;")
            self.speed_label.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 500;")
            self.percent_label.setStyleSheet("color: #f87171; font-size: 10px; font-weight: bold;")

    def attach_queue(self, queue: TaskQueue) -> None:
        if self._queue is not None:
            return
        self._queue = queue
        self._queue.task_enqueued.connect(self._on_task_enqueued)
        self._queue.queue_changed.connect(self._on_queue_changed)
        self._queue.task_updated.connect(self._on_task_updated)
        self._queue.task_completed.connect(self._on_task_completed)
        if self._drawer is not None and hasattr(self._drawer, "attach_queue"):
            self._drawer.attach_queue(queue)
        self.refresh()

    def refresh(self) -> None:
        if self._queue is None:
            self.setVisible(False)
            return
        active = self._queue.active_tasks()
        self._update_display(active)

    def retranslate_ui(self) -> None:
        self.refresh()

    @staticmethod
    def _format_percentage(value: int) -> str:
        return f"{value}%"

    @staticmethod
    def _extract_stage_text(task: TaskQueueItem) -> str:
        stage = getattr(task, "stage", "")
        if not stage:
            return ""
        clean = str(stage).lower().replace("progressstage.", "").strip()
        if clean in ProgressPresenter._STAGE_LABELS:
            return ProgressPresenter._STAGE_LABELS[clean]
        return clean.replace("_", " ").upper()

    def _update_display(self, active_tasks: list[TaskQueueItem]) -> None:
        if not active_tasks:
            if self._hide_timer.isActive():
                return
            if self._was_active:
                self._was_active = False

                # Check if the run finished with an error
                failed_tasks = [t for t in (self._queue.all_tasks() if self._queue else ()) if t.status == "failed"]
                failed_item = self._last_failed_task or (failed_tasks[-1] if failed_tasks else None)

                if failed_item is not None:
                    # Show Error State (Red)
                    self._set_visual_state("error")

                    self.stage_badge.setText(tr("progress.status.failed"))
                    self.stage_badge.setVisible(True)

                    err_text = tr(str(failed_item.error or failed_item.message or tr("tasks.indicator.failed")))
                    self.text_label.setText(f"{tr('tasks.indicator.failed')}: {err_text}")

                    self.progress_bar.setRange(0, 100)
                    self.progress_bar.setValue(100)

                    self.progress_detail_label.setText(err_text)
                    self.progress_detail_label.setVisible(True)
                    self.speed_label.setText("")
                    self.speed_label.setVisible(False)

                    self.percent_label.setText(tr("progress.status.failed"))

                    lines = [f"<b><font color='#ef4444'>{tr('tasks.indicator.failed')}</font></b>"]
                    if failed_item.message:
                        lines.append(f"• {tr(str(failed_item.message))}")
                    if failed_item.error and failed_item.error != failed_item.message:
                        lines.append(f"• {tr(str(failed_item.error))}")
                    self.setToolTip("<br/>".join(lines))

                    self._hide_timer.start(8000)
                else:
                    # Show Success State (Green)
                    self._set_visual_state("success")

                    self.stage_badge.setText(tr("common.status.ready"))
                    self.stage_badge.setVisible(True)

                    self.text_label.setText(tr("tasks.indicator.completed"))

                    self.progress_bar.setRange(0, 100)
                    self.progress_bar.setValue(100)

                    self.progress_detail_label.setText(tr("common.status.ready"))
                    self.progress_detail_label.setVisible(True)
                    self.speed_label.setText("")
                    self.speed_label.setVisible(False)

                    self.percent_label.setText(self._format_percentage(100))
                    self.setToolTip(tr("tasks.indicator.completed"))

                    self._hide_timer.start(2500)
            else:
                self.setVisible(False)
            return

        # Active tasks running
        self._hide_timer.stop()
        self._was_active = True
        self.setVisible(True)

        self._set_visual_state("normal")

        count = len(active_tasks)
        primary_task = active_tasks[0]
        percentage = primary_task.percentage

        # Stage Badge
        stage_text = self._extract_stage_text(primary_task)
        if stage_text:
            self.stage_badge.setText(stage_text)
            self.stage_badge.setVisible(True)
        else:
            self.stage_badge.setVisible(False)

        # 1. Hàng Trên (Top row): Tên task và chi tiết
        if count == 1:
            raw_msg = primary_task.message or tr("progress.task.working")
            msg = tr(str(raw_msg))
            raw_detail = getattr(primary_task, "detail", "")
            detail = tr(str(raw_detail)) if raw_detail else ""
            if detail and detail != msg and detail != raw_msg:
                display_msg = f"{msg} — {detail}"
            else:
                display_msg = msg
            self.text_label.setText(display_msg)
        else:
            self.text_label.setText(tr("tasks.indicator.active_multiple", count=count, percent="").strip())

        # 2. Hàng Giữa (Middle row): Thanh tiến trình
        if percentage is not None:
            self.progress_bar.setRange(0, 100)
            val = max(0, min(100, int(percentage)))
            self.progress_bar.setValue(val)
        else:
            self.progress_bar.setRange(0, 0)

        # 3. Hàng Dưới (Bottom row): Số liệu đầy đủ (tiến lượng, tốc độ, tỷ lệ %)
        if primary_task.progress_text:
            self.progress_detail_label.setText(f"📥 {primary_task.progress_text}")
            self.progress_detail_label.setVisible(True)
        elif count > 1:
            self.progress_detail_label.setText(f"{count} tasks")
            self.progress_detail_label.setVisible(True)
        else:
            self.progress_detail_label.setText("")
            self.progress_detail_label.setVisible(False)

        if primary_task.speed_text:
            self.speed_label.setText(f"⚡ {primary_task.speed_text}")
            self.speed_label.setVisible(True)
        else:
            self.speed_label.setText("")
            self.speed_label.setVisible(False)

        if percentage is not None:
            val = max(0, min(100, int(percentage)))
            self.percent_label.setText(self._format_percentage(val))
        else:
            self.percent_label.setText("")

        # Tooltip
        title = tr("tasks.indicator.tooltip_title")
        lines = [f"<b>{title} ({count})</b>"]
        for task in active_tasks:
            pct = f" ({int(task.percentage)}%)" if task.percentage is not None else ""
            speed = f" • {task.speed_text}" if task.speed_text else ""
            prog = f" [{task.progress_text}]" if task.progress_text else ""
            raw_tmsg = task.message or tr("progress.task.working")
            t_msg = tr(str(raw_tmsg))
            raw_tdet = getattr(task, "detail", "")
            t_det = tr(str(raw_tdet)) if raw_tdet else ""
            det = f" — {t_det}" if t_det and t_det != t_msg and t_det != raw_tmsg else ""
            lines.append(f"• {t_msg}{det}{prog}{speed}{pct}")
        self.setToolTip("<br/>".join(lines))

    def _on_task_enqueued(self, _item: TaskQueueItem) -> None:
        self._throttle_timer.stop()
        self._last_failed_task = None
        self._last_refresh_time = 0.0
        self.refresh()

    def _on_queue_changed(self, _all_tasks: list[TaskQueueItem]) -> None:
        self._throttle_timer.stop()
        if self._queue and self._queue.active_tasks():
            self._last_failed_task = None
        self._last_refresh_time = 0.0
        self.refresh()

    def _on_task_updated(self, _item: TaskQueueItem) -> None:
        now = time.monotonic()
        if now - self._last_refresh_time >= 0.033:
            self._last_refresh_time = now
            self.refresh()
        elif not self._throttle_timer.isActive():
            wait_ms = max(1, int((0.033 - (now - self._last_refresh_time)) * 1000))
            self._throttle_timer.start(wait_ms)

    def _on_throttle_timeout(self) -> None:
        self._last_refresh_time = time.monotonic()
        self.refresh()

    def _on_task_completed(self, item: TaskQueueItem) -> None:
        self._throttle_timer.stop()
        self._last_refresh_time = time.monotonic()
        if getattr(item, "status", "") == "failed":
            self._last_failed_task = item
        self.refresh()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_drawer()
            event.accept()
            return
        super().mousePressEvent(event)

    def _toggle_drawer(self) -> None:
        if self._drawer is None:
            from src.gui.widget.task_drawer_popover import TaskDrawerPopover

            self._drawer = TaskDrawerPopover(self._queue)
        if self._drawer.isVisible():
            self._drawer.hide()
        else:
            self._drawer.show_below(self)

    def _on_hide_timeout(self) -> None:
        if self._drawer and self._drawer.isVisible():
            self._hide_timer.start(1500)
            return
        if self._queue and not self._queue.active_tasks():
            self._last_failed_task = None
            self._current_visual_state = ""
            self.setVisible(False)
