from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
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


class TaskDrawerPopover(QFrame):
    """Floating popover drawer showing active background tasks and recent completed history."""

    def __init__(self, task_queue: TaskQueue | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("TaskDrawerPopover")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._queue: TaskQueue | None = None
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
                background-color: #38bdf8;
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
        # Clear existing active widgets
        while self.active_container.count() > 0:
            item = self.active_container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not active_tasks:
            self.no_active_label = QLabel(tr("tasks.drawer.no_active"))
            self.no_active_label.setObjectName("TaskDrawerMuted")
            self.active_container.addWidget(self.no_active_label)
            return

        for task in active_tasks:
            card = self._create_active_task_card(task)
            self.active_container.addWidget(card)

    def _create_active_task_card(self, task: TaskQueueItem) -> QFrame:
        card = QFrame()
        card.setObjectName("TaskItemCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        # Message and Cancel button row
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        msg_text = task.message or tr("progress.task.working")
        msg_label = QLabel(msg_text)
        msg_label.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: bold;")
        msg_label.setWordWrap(True)
        top_row.addWidget(msg_label, 1)

        cancel_button = QPushButton(tr("tasks.drawer.cancel"))
        cancel_button.setObjectName("TaskDrawerCancelButton")
        task_id = task.task_id
        cancel_button.clicked.connect(lambda: self._cancel_task(task_id))
        top_row.addWidget(cancel_button)
        layout.addLayout(top_row)

        # Progress bar and percentage row
        prog_row = QHBoxLayout()
        prog_row.setSpacing(6)
        pbar = QProgressBar()
        pbar.setObjectName("TaskDrawerItemProgress")
        pbar.setFixedHeight(6)
        pbar.setTextVisible(False)

        pct_label = QLabel()
        pct_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        pct_label.setFixedWidth(32)

        if task.percentage is not None:
            pbar.setRange(0, 100)
            val = max(0, min(100, int(task.percentage)))
            pbar.setValue(val)
            pct_label.setText(f"{val}%")
        else:
            pbar.setRange(0, 0)
            pct_label.setText("")

        prog_row.addWidget(pbar, 1)
        prog_row.addWidget(pct_label)
        layout.addLayout(prog_row)

        return card

    def _render_completed_tasks(self, completed_tasks: list[TaskQueueItem]) -> None:
        # Clear existing completed widgets
        while self.completed_container.count() > 0:
            item = self.completed_container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not completed_tasks:
            self.no_completed_label = QLabel(tr("tasks.drawer.no_completed"))
            self.no_completed_label.setObjectName("TaskDrawerMuted")
            self.completed_container.addWidget(self.no_completed_label)
            return

        for task in completed_tasks[:20]:  # limit to last 20 in drawer view
            card = self._create_completed_task_card(task)
            self.completed_container.addWidget(card)

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

    def _clear_history(self) -> None:
        if self._queue is not None:
            self._queue.clear_completed()
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

    def _on_queue_changed(self, _all_tasks: list[TaskQueueItem]) -> None:
        if self.isVisible():
            self.refresh()

    def _on_task_updated(self, _item: TaskQueueItem) -> None:
        if self.isVisible():
            self.refresh()

    def _on_task_completed(self, _item: TaskQueueItem) -> None:
        if self.isVisible():
            self.refresh()
