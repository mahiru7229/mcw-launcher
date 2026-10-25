from __future__ import annotations

import time
from unittest.mock import MagicMock

from src.core.network.download_manager import DownloadManager, SPEED_REPORT_INTERVAL_SECONDS
from src.core.network.download_models import DownloadRequest
from src.core.progress.file_batch_progress import FileBatchProgress
from src.models.progress.progress_stage import ProgressStage


def test_file_batch_progress_update_speed_retains_token_on_none_or_zero() -> None:
    fbp = FileBatchProgress(None, ProgressStage.DOWNLOADING_ASSETS, "Downloading...", 10, min_emit_interval_seconds=0.0)
    token = "file1"

    # Set speed to 500 KB/s
    fbp.update_speed(token, 500_000.0)
    assert token in fbp._rates
    assert fbp._rates[token][0] == 500_000.0

    # Passing None should not pop the token
    fbp.update_speed(token, None)
    assert token in fbp._rates
    assert fbp._rates[token][0] == 500_000.0

    # Passing <= 0 should also not pop the token
    fbp.update_speed(token, 0.0)
    assert token in fbp._rates
    assert fbp._rates[token][0] == 500_000.0


def test_file_batch_progress_complete_clears_speed_at_total() -> None:
    reporter = MagicMock()
    reporter.bytes = lambda *args, **kwargs: None
    fbp = FileBatchProgress(reporter, ProgressStage.DOWNLOADING_ASSETS, "Downloading...", 1, min_emit_interval_seconds=0.0)
    token = "file1"
    fbp.update_speed(token, 1_000_000.0)

    # Monkeypatch _emit to inspect
    emitted = []
    fbp._emit = lambda current, bytes_per_second=None, force=False: emitted.append((current, bytes_per_second))

    fbp.complete(token)
    assert len(emitted) == 1
    # When completed reached total, speed must be None
    assert emitted[0][0] == 1
    assert emitted[0][1] is None


def test_stream_reports_speed_at_time_intervals(tmp_path) -> None:
    dm = DownloadManager()
    reported_speeds = []

    reporter = MagicMock()
    reporter.bytes = lambda *args, **kwargs: reported_speeds.append(kwargs.get("bytes_per_second"))

    request = DownloadRequest(
        urls=("https://example.com/large.zip",),
        destination=tmp_path / "large.zip",
        expected_size=10_000,
        display_name="large.zip",
    )

    # Chunks where percentage stays at 0% for first 3 chunks, with delay exceeding SPEED_REPORT_INTERVAL_SECONDS
    def iter_bytes(chunk_size):
        for _ in range(3):
            time.sleep(SPEED_REPORT_INTERVAL_SECONDS + 0.02)
            yield b"x" * 10
        yield b"x" * (10_000 - 30)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_bytes = iter_bytes
    mock_response.headers = {"content-length": "10000"}

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__enter__.return_value = mock_response
    mock_stream_ctx.__exit__.return_value = None

    mock_client = MagicMock()
    mock_client.stream.return_value = mock_stream_ctx

    dm._stream(
        request,
        "https://example.com/large.zip",
        reporter,
        ProgressStage.DOWNLOADING_ASSETS,
        "Downloading...",
        client_provider=lambda: mock_client,
    )

    # We should have received multiple reports due to time intervals even though percentage stayed at 0%
    assert len(reported_speeds) >= 2
