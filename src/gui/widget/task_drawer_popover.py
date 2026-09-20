from __future__ import annotations

from collections.abc import Callable
import time

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.language.language_manager import tr
from src.gui.core.task_queue import TaskQueue, TaskQueueItem


class ActiveTaskCard(QFrame):
    """Reusable card widget representing an active task in the drawer.

    Updates in-place without widget allocations to ensure high-performance rendering.
    """

    def __init__(self, task: TaskQueueItem, on_cancel: Callable[[str], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TaskItemCard")
        self.task_id = task.task_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        # Message and Cancel button row
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        self.msg_label = QLabel()
        self.msg_label.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: bold;")
        self.msg_label.setWordWrap(True)
        top_row.addWidget(self.msg_label, 1)

        self.cancel_button = QPushButton(tr("tasks.drawer.cancel"))
        self.cancel_button.setObjectName("TaskDrawerCancelButton")
        self.cancel_button.clicked.connect(lambda: on_cancel(self.task_id))
        top_row.addWidget(self.cancel_button)
        layout.addLayout(top_row)

        # Progress bar and percentage row
        prog_row = QHBoxLayout()
        prog_row.setSpacing(6)
        self.pbar = QProgressBar()
        self.pbar.setObjectName("TaskDrawerItemProgress")
        self.pbar.setFixedHeight(6)
        self.pbar.setTextVisible(False)

        self.pct_label = QLabel()
        self.pct_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.pct_label.setFixedWidth(32)

        prog_row.addWidget(self.pbar, 1)
        prog_row.addWidget(self.pct_label)
        layout.addLayout(prog_row)

        # Detail row
        self.detail_row = QHBoxLayout()
        self.detail_row.setSpacing(6)
        self.prog_text_label = QLabel()
        self.prog_text_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.detail_row.addWidget(self.prog_text_label)
        self.detail_row.addStretch(1)

        self.speed_text_label = QLabel()
        self.speed_text_label.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: bold;")
        self.detail_row.addWidget(self.speed_text_label)
        layout.addLayout(self.detail_row)

        self.update_data(task)

    def update_data(self, task: TaskQueueItem) -> None:
        raw_msg = task.message or tr("progress.task.working")
        msg = tr(str(raw_msg))
        raw_detail = getattr(task, "detail", "")
        detail = tr(str(raw_detail)) if raw_detail else ""
        if detail and detail != msg and detail != raw_msg:
            display_msg = f"{msg} — {detail}"
        else:
            display_msg = msg

        if self.msg_label.text() != display_msg:
            self.msg_label.setText(display_msg)

        if task.percentage is not None:
            self.pbar.setRange(0, 100)
            val = max(0, min(100, int(task.percentage)))
            self.pbar.setValue(val)
            pct_str = f"{val}%"
            if self.pct_label.text() != pct_str:
                self.pct_label.setText(pct_str)
        else:
            self.pbar.setRange(0, 0)
            if self.pct_label.text():
                self.pct_label.setText("")

        prog_text = task.progress_text or ""
        if self.prog_text_label.text() != prog_text:
            self.prog_text_label.setText(prog_text)
        self.prog_text_label.setVisible(bool(prog_text))

        speed_text = task.speed_text or ""
        if self.speed_text_label.text() != speed_text:
            self.speed_text_label.setText(speed_text)
        self.speed_text_label.setVisible(bool(speed_text))


class TaskDrawerPopover(QFrame):
    """Floating popover drawer showing active background tasks and recent completed history."""

    def __init__(self, task_queue: TaskQueue | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("TaskDrawerPopover")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._queue: TaskQueue | None = None
        self._active_cards: dict[str, ActiveTaskCard] = {}
        self._rendered_completed_ids: list[str] = []
        self._last_refresh_time: float = 0.0

        self._throttle_timer = QTimer(self)
        self._throttle_timer.setSingleShot(True)
        self._throttle_timer.timeout.connect(self._on_throttle_timeout)

        self.setFixedWidth(380)
        self.setMinimumHeight(240)
        self.setMaximumHeight(500)

        self._build_ui()

        if task_queue is not None:
            self.attach_queue(task_queue)

    def _build_ui(self) -> None:
        self.setStyleSheet("""
            QFrame#TaskDrawerPopover {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QLabel#TaskDrawerTitle {
                font-size: 14px;
                font-weight: bold;
                color: #f8fafc;
            }
            QLabel#TaskDrawerSectionHeader {
                font-size: 11px;
                font-weight: bold;
                color: #94a3b8;
                margin-top: 4px;
            }
            QLabel#TaskDrawerMuted {
                font-size: 11px;
                color: #64748b;
                padding: 4px 0;
            }
            QPushButton#TaskDrawerClearButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                color: #94a3b8;
                font-size: 11px;
                padding: 3px 8px;
            }
            QPushButton#TaskDrawerClearButton:hover {
                background-color: #334155;
                color: #f1f5f9;
            }
            QPushButton#TaskDrawerCancelButton {
                background-color: #3b181e;
                border: 1px solid #7f1d1d;
                border-radius: 4px;
                color: #fca5a5;
                font-size: 10px;
                padding: 2px 6px;
            }
            QPushButton#TaskDrawerCancelButton:hover {
                background-color: #991b1b;
                color: #ffffff;
            }
            QFrame#TaskItemCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
            }
            QProgressBar#TaskDrawerItemProgress {
                background-color: #0f172a;
                border: none;
                border-radius: 3px;
            }
            QProgressBar#TaskDrawerItemProgress::chunk {
                background-color: #00af5c;
                border-radius: 3px;
            }
        """)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.title_label = QLabel(tr("tasks.drawer.title"))
        self.title_label.setObjectName("TaskDrawerTitle")
        self.clear_button = QPushButton(tr("tasks.drawer.clear_completed"))
        self.clear_button.setObjectName("TaskDrawerClearButton")
        self.clear_button.clicked.connect(self._clear_history)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.clear_button)
        root_layout.addLayout(header_layout)

        # Scroll area for task list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("QWidget { background: transparent; }")
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(0, 0, 4, 0)
        self.content_layout.setSpacing(6)

        # Active tasks header
        self.active_header = QLabel(tr("tasks.drawer.active_header"))
        self.active_header.setObjectName("TaskDrawerSectionHeader")
        self.content_layout.addWidget(self.active_header)

        self.active_container = QVBoxLayout()
        self.active_container.setSpacing(6)
        self.content_layout.addLayout(self.active_container)

        self.no_active_label = QLabel(tr("tasks.drawer.no_active"))
        self.no_active_label.setObjectName("TaskDrawerMuted")
        self.active_container.addWidget(self.no_active_label)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #334155; margin: 4px 0;")
        self.content_layout.addWidget(divider)

        # Completed tasks header
        self.completed_header = QLabel(tr("tasks.drawer.completed_header"))
        self.completed_header.setObjectName("TaskDrawerSectionHeader")
        self.content_layout.addWidget(self.completed_header)

        self.completed_container = QVBoxLayout()
        self.completed_container.setSpacing(6)
        self.content_layout.addLayout(self.completed_container)

        self.no_completed_label = QLabel(tr("tasks.drawer.no_completed"))
        self.no_completed_label.setObjectName("TaskDrawerMuted")
        self.completed_container.addWidget(self.no_completed_label)

        self.content_layout.addStretch(1)
        self.scroll_area.setWidget(self.scroll_content)
        root_layout.addWidget(self.scroll_area, 1)

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
            return

        active = self._queue.active_tasks()
        all_items = self._queue.all_tasks()
        completed = [item for item in all_items if not item.is_active]
        completed.reverse()  # most recent first

        self._render_active_tasks(active)
        self._render_completed_tasks(completed)

    def _render_active_tasks(self, active_tasks: list[TaskQueueItem]) -> None:
        active_ids = {t.task_id for t in active_tasks}

        # Remove cards that are no longer active
        for task_id in list(self._active_cards.keys()):
            if task_id not in active_ids:
                card = self._active_cards.pop(task_id)
                self.active_container.removeWidget(card)
                card.deleteLater()

        if not active_tasks:
            self.no_active_label.setVisible(True)
            return

        self.no_active_label.setVisible(False)

        # Update existing or add new cards
        for task in active_tasks:
            if task.task_id in self._active_cards:
                self._active_cards[task.task_id].update_data(task)
            else:
                card = ActiveTaskCard(task, on_cancel=self._cancel_task, parent=self.scroll_content)
                self.active_container.addWidget(card)
                self._active_cards[task.task_id] = card

    def _create_completed_task_card(self, task: TaskQueueItem) -> QFrame:
        card = QFrame()
        card.setObjectName("TaskItemCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        msg_text = task.message or tr("progress.task.working")
        msg_label = QLabel(msg_text)
        msg_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)

        status_label = QLabel()
        if task.status == "succeeded":
            status_label.setText(tr("tasks.drawer.status_success"))
            status_label.setStyleSheet("color: #4ade80; font-size: 11px; font-weight: bold;")
        elif task.status == "failed":
            status_label.setText(tr("tasks.drawer.status_failed"))
            status_label.setStyleSheet("color: #f87171; font-size: 11px; font-weight: bold;")
            if task.error:
                status_label.setToolTip(str(task.error))
        else:
            status_label.setText(tr("tasks.drawer.status_cancelled"))
            status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")

        layout.addWidget(status_label)
        return card

    def _render_completed_tasks(self, completed_tasks: list[TaskQueueItem]) -> None:
        target_tasks = completed_tasks[:20]  # limit to last 20 in drawer view
        target_ids = [t.task_id for t in target_tasks]

        if target_ids == self._rendered_completed_ids:
            return

        self._rendered_completed_ids = target_ids

        # Clear existing completed cards (keep no_completed_label intact)
        for i in reversed(range(self.completed_container.count())):
            item = self.completed_container.itemAt(i)
            widget = item.widget()
            if widget is not None and widget is not self.no_completed_label:
                self.completed_container.removeWidget(widget)
                widget.deleteLater()

        if not target_tasks:
            self.no_completed_label.setVisible(True)
            return

        self.no_completed_label.setVisible(False)

        for task in target_tasks:
            card = self._create_completed_task_card(task)
            self.completed_container.addWidget(card)

    def _clear_history(self) -> None:
        if self._queue is not None:
            self._queue.clear_completed()
        self._rendered_completed_ids = []
        self.refresh()

    def _cancel_task(self, task_id: str) -> None:
        if self._queue is not None:
            self._queue.cancel_task(task_id)

    def show_below(self, anchor: QWidget) -> None:
        self.refresh()
        anchor_rect = anchor.rect()
        top_left = anchor.mapToGlobal(QPoint(0, anchor_rect.height() + 4))
        # Align right edge of popover with right edge of anchor
        x = top_left.x() + anchor_rect.width() - self.width()
        x = max(10, x)
        y = top_left.y()
        self.move(x, y)
        self.show()
        self.raise_()

    def hideEvent(self, event: object) -> None:
        self._throttle_timer.stop()
        super().hideEvent(event)

    def _on_queue_changed(self, _all_tasks: list[TaskQueueItem]) -> None:
        if self.isVisible():
            self._throttle_timer.stop()
            self._last_refresh_time = 0.0
            self.refresh()

    def _on_task_updated(self, item: TaskQueueItem) -> None:
        if not self.isVisible():
            return
        now = time.monotonic()
        if now - self._last_refresh_time >= 0.033:
            self._last_refresh_time = now
            if item.task_id in self._active_cards:
                self._active_cards[item.task_id].update_data(item)
            elif self._queue:
                self._render_active_tasks(self._queue.active_tasks())
        elif not self._throttle_timer.isActive():
            wait_ms = max(1, int((0.033 - (now - self._last_refresh_time)) * 1000))
            self._throttle_timer.start(wait_ms)

    def _on_throttle_timeout(self) -> None:
        if not self.isVisible() or self._queue is None:
            return
        self._last_refresh_time = time.monotonic()
        self._render_active_tasks(self._queue.active_tasks())

    def _on_task_completed(self, _item: TaskQueueItem) -> None:
        if self.isVisible():
            self._throttle_timer.stop()
            self._last_refresh_time = 0.0
            self.refresh()
