from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject, Signal

from mcw_core.api.language.language_manager import tr
from mcw_core.api.security.sensitive_data_redactor import SensitiveDataRedactor
from src.gui.network_retry import NetworkRetryPolicy, is_retryable_network_error, run_with_network_retries
from src.gui.task_runner import TaskRunner


@dataclass(frozen=True, slots=True)
class _NetworkTaskRegistration:
    task_runner: TaskRunner
    task: Callable[[], Any]
    message: str
    blocking: bool


class BaseController(QObject):
    status_changed = Signal(str)
    log_created = Signal(str)
    error_created = Signal(str, str)
    network_retry_available = Signal(str, str, str)

    NETWORK_RETRY_POLICY = NetworkRetryPolicy()
    MAX_REMEMBERED_NETWORK_TASKS = 64

    def __init__(self) -> None:
        super().__init__()
        self._network_tasks: OrderedDict[str, _NetworkTaskRegistration] = OrderedDict()

    def _run_network_task(
        self,
        task_runner: TaskRunner,
        task_id: str,
        task: Callable[[], Any],
        message: str,
        *,
        blocking: bool = False,
    ) -> bool:
        normalized_id = str(task_id).strip()
        if not normalized_id:
            raise ValueError("A network task id is required.")

        self._network_tasks[normalized_id] = _NetworkTaskRegistration(
            task_runner=task_runner,
            task=task,
            message=str(message),
            blocking=bool(blocking),
        )
        self._network_tasks.move_to_end(normalized_id)
        while len(self._network_tasks) > self.MAX_REMEMBERED_NETWORK_TASKS:
            self._network_tasks.popitem(last=False)

        return task_runner.run(
            normalized_id,
            self._network_task(normalized_id, task),
            str(message),
            blocking=blocking,
        )

    def retry_network_task(self, task_id: str) -> bool:
        normalized_id = str(task_id).strip()
        registration = self._network_tasks.get(normalized_id)
        if registration is None:
            self._emit_error(tr("network.retry.manual.title"), tr("network.retry.manual.expired"))
            return False
        if registration.task_runner.is_task_active(normalized_id):
            self.status_changed.emit(tr("network.retry.manual.already_running"))
            return False

        self.status_changed.emit(tr("network.retry.manual.starting"))
        self.log_created.emit(tr("network.retry.manual.log", task=normalized_id))
        return registration.task_runner.run(
            normalized_id,
            self._network_task(normalized_id, registration.task),
            registration.message,
            blocking=registration.blocking,
        )

    def _network_task(self, task_id: str, task: Callable[[], Any]) -> Callable[[], Any]:
        def on_retry(next_attempt: int, max_attempts: int, error: Exception, delay: float) -> None:
            message = tr("network.retry.auto", attempt=next_attempt, max_attempts=max_attempts)
            self.status_changed.emit(message)
            raw_error = SensitiveDataRedactor.redact_text(str(error) or type(error).__name__)
            self.log_created.emit(
                tr(
                    "network.retry.log",
                    task=task_id,
                    attempt=next_attempt,
                    max_attempts=max_attempts,
                    delay=f"{delay:.1f}",
                    error=raw_error,
                )
            )

        return lambda: run_with_network_retries(
            task,
            policy=self.NETWORK_RETRY_POLICY,
            on_retry=on_retry,
        )

    def _offer_network_retry(self, task_id: str, title: str, error: Exception) -> bool:
        normalized_id = str(task_id).strip()
        if normalized_id not in self._network_tasks or not is_retryable_network_error(error):
            return False

        raw_message = str(error) or type(error).__name__
        message = SensitiveDataRedactor.redact_text(raw_message)
        self.status_changed.emit(tr("network.retry.manual.available"))
        self.log_created.emit(
            tr(
                "network.retry.manual.available_log",
                task=normalized_id,
                error=message,
            )
        )
        self.network_retry_available.emit(normalized_id, str(title), message)
        return True

    def _emit_error(self, title: str, error: Exception | str) -> None:
        raw_message = str(error) if isinstance(error, str) else f"{type(error).__name__}: {error}"
        message = SensitiveDataRedactor.redact_text(raw_message)
        self.log_created.emit(message)
        self.error_created.emit(title, message)
