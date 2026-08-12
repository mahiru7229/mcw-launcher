from __future__ import annotations

import pytest

from src.gui.network_retry import NetworkRetryPolicy, is_retryable_network_error, run_with_network_retries


def test_network_task_retries_twice_then_succeeds() -> None:
    calls = 0
    sleeps: list[float] = []
    retries: list[tuple[int, int, str, float]] = []

    def task() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TimeoutError("metadata request timed out")
        return "ok"

    result = run_with_network_retries(
        task,
        policy=NetworkRetryPolicy(max_attempts=3, initial_delay_seconds=0.25, backoff_multiplier=2.0),
        on_retry=lambda attempt, maximum, error, delay: retries.append((attempt, maximum, str(error), delay)),
        sleep=sleeps.append,
    )

    assert result == "ok"
    assert calls == 3
    assert sleeps == [0.25, 0.5]
    assert retries == [
        (2, 3, "metadata request timed out", 0.25),
        (3, 3, "metadata request timed out", 0.5),
    ]


def test_network_task_stops_after_bounded_attempts() -> None:
    calls = 0

    def task() -> None:
        nonlocal calls
        calls += 1
        raise ConnectionError("connection reset")

    with pytest.raises(ConnectionError, match="connection reset"):
        run_with_network_retries(task, policy=NetworkRetryPolicy(max_attempts=3, initial_delay_seconds=0), sleep=lambda _delay: None)

    assert calls == 3


def test_validation_error_is_not_retried() -> None:
    calls = 0

    def task() -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("Forge Maven metadata does not contain any versions.")

    with pytest.raises(RuntimeError, match="does not contain"):
        run_with_network_retries(task, policy=NetworkRetryPolicy(max_attempts=3, initial_delay_seconds=0), sleep=lambda _delay: None)

    assert calls == 1


def test_wrapped_network_error_is_retryable() -> None:
    try:
        raise TimeoutError("socket timed out")
    except TimeoutError as cause:
        error = RuntimeError("Could not load Minecraft Forge versions")
        error.__cause__ = cause

    assert is_retryable_network_error(error) is True


def test_ftb_contact_failure_without_cause_is_retryable() -> None:
    error = RuntimeError("Could not contact the FTB modpack service: 503 from endpoint")

    assert is_retryable_network_error(error) is True


def test_permanent_http_status_text_is_not_retryable() -> None:
    error = RuntimeError("Could not contact provider: 404 Not Found")

    assert is_retryable_network_error(error) is False


def test_missing_manifest_without_cache_is_retryable() -> None:
    assert is_retryable_network_error(RuntimeError("Minecraft version manifest is unavailable.")) is True


def test_checkpoint_can_cancel_before_retry_attempt() -> None:
    calls = 0
    checkpoints = 0

    def task() -> None:
        nonlocal calls
        calls += 1
        raise TimeoutError("metadata request timed out")

    def checkpoint() -> None:
        nonlocal checkpoints
        checkpoints += 1
        if checkpoints >= 2:
            raise RuntimeError("cancelled")

    with pytest.raises(RuntimeError, match="cancelled"):
        run_with_network_retries(
            task,
            policy=NetworkRetryPolicy(max_attempts=3, initial_delay_seconds=0),
            sleep=lambda _delay: None,
            checkpoint=checkpoint,
        )

    assert calls == 1
