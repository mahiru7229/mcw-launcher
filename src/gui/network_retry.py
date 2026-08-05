from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import errno
import re
import time
from typing import Any, TypeVar

try:
    import httpx
except ImportError:  # pragma: no cover - launcher runtime depends on httpx
    httpx = None

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class NetworkRetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 2.0

    def delay_before(self, next_attempt: int) -> float:
        exponent = max(0, int(next_attempt) - 2)
        delay = self.initial_delay_seconds * (self.backoff_multiplier ** exponent)
        return min(self.max_delay_seconds, max(0.0, float(delay)))


RetryCallback = Callable[[int, int, Exception, float], None]

_RETRYABLE_ERRNOS = {
    errno.ECONNABORTED,
    errno.ECONNREFUSED,
    errno.ECONNRESET,
    errno.EHOSTUNREACH,
    errno.ENETDOWN,
    errno.ENETRESET,
    errno.ENETUNREACH,
    errno.EPIPE,
    errno.ETIMEDOUT,
    10051,  # WSAENETUNREACH
    10052,  # WSAENETRESET
    10053,  # WSAECONNABORTED
    10054,  # WSAECONNRESET
    10060,  # WSAETIMEDOUT
    10061,  # WSAECONNREFUSED
    10065,  # WSAEHOSTUNREACH
}
_RETRYABLE_HTTP_STATUS = {408, 425, 429, 500, 502, 503, 504}
_PERMANENT_HTTP_STATUS_PATTERN = re.compile(r"\b(?:400|401|403|404|405|409|410|412|413|415|422)\b")
_RETRYABLE_TEXT = (
    "timed out",
    "timeout",
    "connection reset",
    "connection refused",
    "connection aborted",
    "connection closed",
    "server disconnected",
    "remote protocol",
    "network is unreachable",
    "host is unreachable",
    "name or service not known",
    "temporary failure in name resolution",
    "dns lookup",
    "could not connect",
    "could not contact",
    "unable to contact",
    "network unavailable",
    "network error",
    "manifest is unavailable",
    "temporarily unavailable",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "too many requests",
    "rate limit",
)
_PERMANENT_TEXT = (
    "invalid url",
    "unsupported protocol",
    "unsupported loader",
    "not available for minecraft",
    "does not contain any versions",
    "invalid metadata",
    "invalid response payload",
    "authentication failed",
    "unauthorized",
    "forbidden",
)


def run_with_network_retries(
    task: Callable[[], T],
    *,
    policy: NetworkRetryPolicy | None = None,
    on_retry: RetryCallback | None = None,
    sleep: Callable[[float], Any] = time.sleep,
) -> T:
    active_policy = policy or NetworkRetryPolicy()
    max_attempts = max(1, int(active_policy.max_attempts))

    for attempt in range(1, max_attempts + 1):
        try:
            return task()
        except Exception as error:
            if attempt >= max_attempts or not is_retryable_network_error(error):
                raise
            next_attempt = attempt + 1
            delay = active_policy.delay_before(next_attempt)
            if on_retry is not None:
                on_retry(next_attempt, max_attempts, error, delay)
            if delay > 0:
                sleep(delay)

    raise RuntimeError("Network retry loop ended unexpectedly.")


def is_retryable_network_error(error: BaseException) -> bool:
    chain = tuple(_exception_chain(error))

    for current in chain:
        if _is_permanent_http_error(current):
            return False

    for current in chain:
        if isinstance(current, (TimeoutError, ConnectionError)):
            return True
        if isinstance(current, OSError) and getattr(current, "errno", None) in _RETRYABLE_ERRNOS:
            return True
        if _is_retryable_http_error(current):
            return True

    combined = " | ".join(str(item).strip().casefold() for item in chain if str(item).strip())
    if not combined:
        return False
    if any(text in combined for text in _PERMANENT_TEXT):
        return False
    if _PERMANENT_HTTP_STATUS_PATTERN.search(combined):
        return False
    return any(text in combined for text in _RETRYABLE_TEXT) or any(str(code) in combined for code in _RETRYABLE_HTTP_STATUS)


def _exception_chain(error: BaseException):
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _is_retryable_http_error(error: BaseException) -> bool:
    if httpx is None:
        return False
    if isinstance(error, httpx.HTTPStatusError):
        response = getattr(error, "response", None)
        return int(getattr(response, "status_code", 0) or 0) in _RETRYABLE_HTTP_STATUS
    permanent_request_types = tuple(
        error_type
        for error_type in (
            getattr(httpx, "InvalidURL", None),
            getattr(httpx, "UnsupportedProtocol", None),
        )
        if isinstance(error_type, type)
    )
    if permanent_request_types and isinstance(error, permanent_request_types):
        return False
    request_error = getattr(httpx, "RequestError", None)
    return isinstance(request_error, type) and isinstance(error, request_error)


def _is_permanent_http_error(error: BaseException) -> bool:
    if httpx is None or not isinstance(error, getattr(httpx, "HTTPStatusError", ())):
        return False
    response = getattr(error, "response", None)
    status = int(getattr(response, "status_code", 0) or 0)
    return bool(status) and status not in _RETRYABLE_HTTP_STATUS
