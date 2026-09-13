from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QWidget

from mcw_core.api.language.language_manager import tr
from src.gui.core.task_queue import TaskQueue, TaskQueueItem


class GlobalTaskIndicator(QFrame):
    """Global task progress and status indicator pill for MainWindow.

    Connects to GuiTaskQueue to display background task status, mini progress bar,
    and detailed tooltip without blocking user interaction.
    """

    def __init__(self, task_queue: TaskQueue | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GlobalTaskIndicator")
        self._queue: TaskQueue | None = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._on_hide_timeout)
        self._was_active = False

        self._build_ui()
        self.setVisible(False)

        if task_queue is not None:
            self.attach_queue(task_queue)

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self.icon_label = QLabel(chr(0x27F3))  # ⟳ clock-wise open circle arrow
        self.icon_label.setObjectName("TaskIndicatorIcon")
        self.icon_label.setStyleSheet("color: #60a5fa; font-weight: bold; font-size: 13px;")

        self.text_label = QLabel()
        self.text_label.setObjectName("TaskIndicatorText")
        self.text_label.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        self.text_label.setMaximumWidth(220)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("TaskIndicatorProgress")
        self.progress_bar.setFixedWidth(64)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar#TaskIndicatorProgress {
                background-color: #1e293b;
                border: none;
                border-radius: 3px;
            }
            QProgressBar#TaskIndicatorProgress::chunk {
                background-color: #38bdf8;
                border-radius: 3px;
            }
        """)

        self.percent_label = QLabel()
        self.percent_label.setObjectName("TaskIndicatorPercent")
        self.percent_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold;")
        self.percent_label.setFixedWidth(32)

        self.setStyleSheet("""
            QFrame#GlobalTaskIndicator {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.percent_label)

    def attach_queue(self, queue: TaskQueue) -> None:
        if self._queue is not None:
            return
        self._queue = queue
        self._queue.queue_changed.connect(self._on_queue_changed)
        self._queue.task_updated.connect(self._on_task_updated)
        self._queue.task_completed.connect(self._on_task_completed)
        self.refresh()

    def refresh(self) -> None:
        if self._queue is None:
            self.setVisible(False)
            return
        active = self._queue.active_tasks()
        self._update_display(active)

    def retranslate_ui(self) -> None:
        self.refresh()

    def _update_display(self, active_tasks: list[TaskQueueItem]) -> None:
        if not active_tasks:
            if self._hide_timer.isActive():
                return
            if self._was_active:
                self._was_active = False
                self.icon_label.setText(chr(0x2713))  # ✓ check mark
                self.icon_label.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 13px;")
                self.text_label.setText(tr("tasks.indicator.completed"))
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
                self.percent_label.setText("100%")
                self.setToolTip(tr("tasks.indicator.completed"))
                self._hide_timer.start(2500)
            else:
                self.setVisible(False)
            return

        self._hide_timer.stop()
        self._was_active = True
        self.setVisible(True)

        self.icon_label.setText(chr(0x27F3))
        self.icon_label.setStyleSheet("color: #60a5fa; font-weight: bold; font-size: 13px;")

        count = len(active_tasks)
        primary_task = active_tasks[0]
        percentage = primary_task.percentage

        if count == 1:
            raw_msg = primary_task.message or tr("progress.task.working")
            display_msg = raw_msg if len(raw_msg) <= 30 else raw_msg[:28] + "..."
            self.text_label.setText(display_msg)
        else:
            pct_str = f"{int(percentage)}%" if percentage is not None else ""
            self.text_label.setText(tr("tasks.indicator.active_multiple", count=count, percent=pct_str).strip())

        if percentage is not None:
            self.progress_bar.setRange(0, 100)
            val = max(0, min(100, int(percentage)))
            self.progress_bar.setValue(val)
            self.percent_label.setText(f"{val}%")
        else:
            self.progress_bar.setRange(0, 0)
            self.percent_label.setText("")

        title = tr("tasks.indicator.tooltip_title")
        lines = [f"<b>{title} ({count})</b>"]
        for task in active_tasks:
            pct = f" ({int(task.percentage)}%)" if task.percentage is not None else ""
            lines.append(f"• {task.message}{pct}")
        self.setToolTip("<br/>".join(lines))

    def _on_queue_changed(self, _all_tasks: list[TaskQueueItem]) -> None:
        self.refresh()

    def _on_task_updated(self, _item: TaskQueueItem) -> None:
        self.refresh()

    def _on_task_completed(self, _item: TaskQueueItem) -> None:
        self.refresh()

    def _on_hide_timeout(self) -> None:
        if self._queue and not self._queue.active_tasks():
            self.setVisible(False)
