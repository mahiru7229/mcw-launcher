from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import Event, Thread
from time import monotonic
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QObject, Qt, Signal, Slot

from mcw_core.api.language.language_manager import tr


class TaskCancelledError(RuntimeError):
    """Raised by cooperative launcher tasks after cancellation is requested."""


class TaskConflictPolicy(StrEnum):
    """How a task should behave when another task in the same group is active."""

    REJECT = "reject"
    REPLACE = "replace"
    PARALLEL = "parallel"


class TaskState(StrEnum):
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TaskCancellationToken:
    """Thread-safe cooperative cancellation primitive for launcher work."""

    def __init__(self) -> None:
        self._cancelled = Event()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def cancel(self) -> None:
        self._cancelled.set()

    def checkpoint(self) -> None:
        if self.cancelled:
            raise TaskCancelledError("Launcher task cancelled.")

    def wait(self, seconds: float) -> None:
        if self._cancelled.wait(max(0.0, float(seconds))):
            self.checkpoint()


@dataclass(slots=True)
class TaskContext:
    context_id: str
    task_id: str
    group: str
    thread: Thread
    token: TaskCancellationToken
    blocking: bool
    cooperative: bool
    state: TaskState = TaskState.RUNNING
    superseded: bool = False
    started_at: float = 0.0


class TaskRunner(QObject):
    """Run launcher tasks on daemon worker threads with cooperative lifecycle control.

    v1.4 deliberately uses daemon Python worker threads instead of parenting a QThread
    to the main window. Closing the launcher therefore cannot be held hostage by a slow
    metadata request. Cooperative tasks still receive a cancellation token so they can
    release resources before the process exits.
    """

    task_started = Signal(str, str, bool)
    task_succeeded = Signal(str, object)
    task_failed = Signal(str, object)
    task_cancel_requested = Signal(str)
    task_cancelled = Signal(str)
    busy_changed = Signal(bool)
    task_rejected = Signal(str)
    task_settled = Signal(str, bool, object)
    shutdown_started = Signal()

    _worker_settled = Signal(str, bool, object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._contexts: dict[str, TaskContext] = {}
        self._blocking_tasks = 0
        self._shutting_down = False
        self._worker_settled.connect(self._finish_worker, Qt.ConnectionType.QueuedConnection)

    @property
    def is_busy(self) -> bool:
        return self._blocking_tasks > 0

    @property
    def is_shutting_down(self) -> bool:
        return self._shutting_down

    @property
    def has_active_tasks(self) -> bool:
        return bool(self._contexts)

    @property
    def active_task_ids(self) -> tuple[str, ...]:
        # Keep the public contract unique even while an obsolete generation drains.
        return tuple(dict.fromkeys(context.task_id for context in self._contexts.values()))

    def is_task_active(self, task_id: str) -> bool:
        normalized = str(task_id).strip()
        return any(context.task_id == normalized for context in self._contexts.values())

    def run(
        self,
        task_id: str,
        task: Callable[..., Any],
        message: str,
        blocking: bool = True,
        *,
        group: str | None = None,
        conflict_policy: TaskConflictPolicy | str = TaskConflictPolicy.REJECT,
        cooperative: bool = False,
    ) -> bool:
        normalized_id = str(task_id).strip()
        if not normalized_id:
            raise ValueError("A task id is required.")
        if self._shutting_down:
            self.task_rejected.emit(tr("task.shutting_down"))
            return False

        normalized_group = str(group or normalized_id).strip() or normalized_id
        policy = TaskConflictPolicy(conflict_policy)
        conflicts = [
            context
            for context in self._contexts.values()
            if context.group == normalized_group and not context.superseded
        ]

        if conflicts and policy is TaskConflictPolicy.REJECT:
            if any(context.task_id == normalized_id for context in conflicts):
                self.task_rejected.emit(tr("task.already_running", task_id=normalized_id))
            else:
                self.task_rejected.emit(tr("task.group_running", group=normalized_group))
            return False

        if conflicts and policy is TaskConflictPolicy.REPLACE:
            for context in conflicts:
                self._request_cancel_context(context, superseded=True)

        if blocking and self.is_busy and policy is not TaskConflictPolicy.PARALLEL:
            # Blocking mutations remain conservative in Beta 1. Resource-aware queuing
            # for unrelated instance mutations is intentionally deferred to Beta 2.
            active_blocking = [
                context for context in self._contexts.values()
                if context.blocking and not context.superseded
            ]
            if active_blocking:
                self.task_rejected.emit(tr("task.busy"))
                return False

        context_id = uuid4().hex
        token = TaskCancellationToken()

        def worker_entry() -> None:
            try:
                token.checkpoint()
                result = task(token) if cooperative else task()
                token.checkpoint()
            except Exception as error:
                try:
                    self._worker_settled.emit(context_id, False, error)
                except RuntimeError:
                    pass
                return
            try:
                self._worker_settled.emit(context_id, True, result)
            except RuntimeError:
                pass

        thread = Thread(
            target=worker_entry,
            name=f"mcw-task-{normalized_id[:48]}",
            daemon=True,
        )
        context = TaskContext(
            context_id=context_id,
            task_id=normalized_id,
            group=normalized_group,
            thread=thread,
            token=token,
            blocking=bool(blocking),
            cooperative=bool(cooperative),
            started_at=monotonic(),
        )
        self._contexts[context_id] = context

        if blocking:
            self._blocking_tasks += 1
            if self._blocking_tasks == 1:
                self.busy_changed.emit(True)

        self.task_started.emit(normalized_id, str(message), bool(blocking))
        try:
            thread.start()
        except Exception as error:
            self._contexts.pop(context_id, None)
            self._release_blocking(context)
            self.task_failed.emit(normalized_id, error)
            self.task_settled.emit(normalized_id, False, error)
            return False
        return True

    def cancel(self, task_id: str) -> bool:
        normalized = str(task_id).strip()
        contexts = [
            context for context in self._contexts.values()
            if context.task_id == normalized and context.state is TaskState.RUNNING
        ]
        for context in contexts:
            self._request_cancel_context(context)
        return bool(contexts)

    def cancel_group(self, group: str) -> int:
        normalized = str(group).strip()
        contexts = [
            context for context in self._contexts.values()
            if context.group == normalized and context.state is TaskState.RUNNING
        ]
        for context in contexts:
            self._request_cancel_context(context)
        return len(contexts)

    def cancel_all(self) -> tuple[str, ...]:
        cancelled: list[str] = []
        for context in tuple(self._contexts.values()):
            if context.state is not TaskState.RUNNING:
                continue
            self._request_cancel_context(context)
            cancelled.append(context.task_id)
        return tuple(dict.fromkeys(cancelled))

    def begin_shutdown(self) -> tuple[str, ...]:
        if self._shutting_down:
            return ()
        self._shutting_down = True
        self.shutdown_started.emit()
        return self.cancel_all()

    def close(self) -> None:
        # v1.3 refused to close while work was active. v1.4 makes shutdown a
        # cancellation boundary instead; daemon workers cannot keep the app alive.
        self.begin_shutdown()

    def _request_cancel_context(self, context: TaskContext, *, superseded: bool = False) -> None:
        if context.state is not TaskState.RUNNING:
            return
        context.state = TaskState.CANCEL_REQUESTED
        context.superseded = bool(superseded)
        context.token.cancel()
        self.task_cancel_requested.emit(context.task_id)

    @Slot(str, bool, object)
    def _finish_worker(self, context_id: str, succeeded: bool, payload: object) -> None:
        context = self._contexts.pop(context_id, None)
        if context is None:
            return
        self._release_blocking(context)

        cancelled = (
            context.token.cancelled
            or context.superseded
            or isinstance(payload, TaskCancelledError)
        )
        if cancelled:
            context.state = TaskState.CANCELLED
            self.task_cancelled.emit(context.task_id)
            self.task_settled.emit(
                context.task_id,
                False,
                payload if isinstance(payload, Exception) else TaskCancelledError("Launcher task cancelled."),
            )
            return

        if succeeded:
            context.state = TaskState.SUCCEEDED
            self.task_succeeded.emit(context.task_id, payload)
            self.task_settled.emit(context.task_id, True, payload)
            return

        context.state = TaskState.FAILED
        error = payload if isinstance(payload, Exception) else RuntimeError(str(payload))
        self.task_failed.emit(context.task_id, error)
        self.task_settled.emit(context.task_id, False, error)

    def _release_blocking(self, context: TaskContext) -> None:
        if not context.blocking:
            return
        self._blocking_tasks = max(0, self._blocking_tasks - 1)
        if self._blocking_tasks == 0:
            self.busy_changed.emit(False)
