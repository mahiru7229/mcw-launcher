from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from src.gui.widget.compact_progress_widget import CompactProgressWidget
from src.gui.widget.launch_control_widget import LaunchControlWidget
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_stage import ProgressStage
from src.models.progress.progress_state import ProgressState


def test_launch_control_widget_fast_path_only_updates_speed(gui_app, monkeypatch: pytest.MonkeyPatch) -> None:
    widget = LaunchControlWidget()
    ev1 = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_ASSETS,
        state=ProgressState.RUNNING,
        message="Downloading assets",
        detail="10 MB / 100 MB",
        current=10_000_000,
        total=100_000_000,
        unit="bytes",
        bytes_per_second=1_000_000.0,
    )
    widget.set_progress_event(ev1)

    status_calls = []
    stage_calls = []
    progress_bar_calls = []

    monkeypatch.setattr(widget.status_label, "setText", lambda text: status_calls.append(text))
    monkeypatch.setattr(widget.stage_label, "setText", lambda text: stage_calls.append(text))
    monkeypatch.setattr(widget.progress_bar, "setValue", lambda val: progress_bar_calls.append(val))

    # Event 2 has ONLY different bytes_per_second: 2.5 MiB/s
    ev2 = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_ASSETS,
        state=ProgressState.RUNNING,
        message="Downloading assets",
        detail="10 MB / 100 MB",
        current=10_000_000,
        total=100_000_000,
        unit="bytes",
        bytes_per_second=2.5 * 1024 * 1024,
    )
    widget.set_progress_event(ev2)

    # status_label, stage_label, progress_bar should NOT have been called in fast-path
    assert len(status_calls) == 0
    assert len(stage_calls) == 0
    assert len(progress_bar_calls) == 0

    # detail_label should have updated to include the new speed
    assert "2.5 MB" in widget.detail_label.text()


def test_compact_progress_widget_fast_path_only_updates_speed(gui_app, monkeypatch: pytest.MonkeyPatch) -> None:
    widget = CompactProgressWidget()
    ev1 = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_ASSETS,
        state=ProgressState.RUNNING,
        message="Downloading assets",
        detail="10 MB / 100 MB",
        current=10_000_000,
        total=100_000_000,
        unit="bytes",
        bytes_per_second=1_000_000.0,
    )
    widget.set_progress_event(ev1)

    stage_calls = []
    status_calls = []
    bar_calls = []

    monkeypatch.setattr(widget.stage_label, "setText", lambda t: stage_calls.append(t))
    monkeypatch.setattr(widget.status_label, "setText", lambda t: status_calls.append(t))
    monkeypatch.setattr(widget.progress_bar, "setValue", lambda v: bar_calls.append(v))

    ev2 = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_ASSETS,
        state=ProgressState.RUNNING,
        message="Downloading assets",
        detail="10 MB / 100 MB",
        current=10_000_000,
        total=100_000_000,
        unit="bytes",
        bytes_per_second=3.0 * 1024 * 1024,
    )
    widget.set_progress_event(ev2)

    assert len(stage_calls) == 0
    assert len(status_calls) == 0
    assert len(bar_calls) == 0
    assert "3.0 MB/s" in widget.speed_label.text()
