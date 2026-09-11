from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any

from PySide6.QtCore import QObject, Signal

from src.gui.task_runner import TaskRunner


@dataclass(slots=True)
class TaskQueueItem:
    """Snapshot representation of a background or download task."""

    task_id: str
    message: str
    stage: str = ""
    percentage: float | None = None
    status: str = "running"  # running, succeeded, failed, cancelled
    error: str | None = None
    blocking: bool = False
    created_at: float = field(default_factory=time.time)

    @property
    def is_active(self) -> bool:
        return self.status == "running"


class TaskQueue(QObject):
    """Central task and download queue manager for the GUI.

    Bridges TaskRunner events into a unified task drawer / queue representation,
    similar to Modrinth App's global download and background task drawer.
    """

    task_enqueued = Signal(object)
    task_updated = Signal(object)
    task_completed = Signal(object)
    queue_changed = Signal(list)

    MAX_HISTORY = 50

    def __init__(self, runner: TaskRunner | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._runner: TaskRunner | None = None
        self._items: dict[str, TaskQueueItem] = {}
        if runner is not None:
            self.attach_runner(runner)

    def attach_runner(self, runner: TaskRunner) -> None:
        if self._runner is not None:
            return
        self._runner = runner
        if hasattr(self._runner, "task_started"):
            self._runner.task_started.connect(self._on_task_started)
        if hasattr(self._runner, "task_progress"):
            self._runner.task_progress.connect(self._on_task_progress)
        if hasattr(self._runner, "task_succeeded"):
            self._runner.task_succeeded.connect(self._on_task_succeeded)
        if hasattr(self._runner, "task_failed"):
            self._runner.task_failed.connect(self._on_task_failed)
        if hasattr(self._runner, "task_cancelled"):
            self._runner.task_cancelled.connect(self._on_task_cancelled)

    def active_tasks(self) -> list[TaskQueueItem]:
        return [item for item in self._items.values() if item.is_active]

    def all_tasks(self) -> list[TaskQueueItem]:
        return list(self._items.values())

    def get_task(self, task_id: str) -> TaskQueueItem | None:
        return self._items.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        if self._runner is not None:
            if hasattr(self._runner, "cancel_task"):
                return bool(self._runner.cancel_task(task_id))
            if hasattr(self._runner, "cancel"):
                return bool(self._runner.cancel(task_id))
        return False

    def update_progress(self, task_id: str, event: Any) -> None:
        self._on_task_progress(task_id, event)

    def clear_completed(self) -> None:
        self._items = {k: v for k, v in self._items.items() if v.is_active}
        self.queue_changed.emit(self.all_tasks())

    def _on_task_started(self, task_id: str, message: str, blocking: bool) -> None:
        item = TaskQueueItem(
            task_id=task_id,
            message=message,
            blocking=blocking,
            status="running",
        )
        self._items[task_id] = item
        self._prune_history()
        self.task_enqueued.emit(item)
        self.queue_changed.emit(self.all_tasks())

    def _on_task_progress(self, task_id: str, event: Any) -> None:
        item = self._items.get(task_id)
        if item is None:
            return

        percentage = getattr(event, "percentage", None)
        message = getattr(event, "message", "")
        stage = getattr(event, "stage", None)
        stage_name = getattr(stage, "value", str(stage)) if stage is not None else ""

        if percentage is not None:
            item.percentage = float(percentage)
        if message:
            item.message = str(message)
        if stage_name:
            item.stage = stage_name

        self.task_updated.emit(item)
        self.queue_changed.emit(self.all_tasks())

    def _on_task_succeeded(self, task_id: str, _result: Any) -> None:
        item = self._items.get(task_id)
        if item is None:
            return
        item.status = "succeeded"
        item.percentage = 100.0
        self.task_completed.emit(item)
        self.queue_changed.emit(self.all_tasks())

    def _on_task_failed(self, task_id: str, error: Any) -> None:
        item = self._items.get(task_id)
        if item is None:
            return
        item.status = "failed"
        item.error = str(error)
        self.task_completed.emit(item)
        self.queue_changed.emit(self.all_tasks())

    def _on_task_cancelled(self, task_id: str) -> None:
        item = self._items.get(task_id)
        if item is None:
            return
        item.status = "cancelled"
        self.task_completed.emit(item)
        self.queue_changed.emit(self.all_tasks())

    def _prune_history(self) -> None:
        if len(self._items) <= self.MAX_HISTORY:
            return
        # Keep all active tasks, prune oldest completed
        completed = [k for k, v in self._items.items() if not v.is_active]
        to_remove = len(self._items) - self.MAX_HISTORY
        for k in completed[:to_remove]:
            del self._items[k]
