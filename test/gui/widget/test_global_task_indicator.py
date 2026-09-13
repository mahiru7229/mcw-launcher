from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject, Signal

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.core.task_queue import TaskQueue
from src.gui.widget.global_task_indicator import GlobalTaskIndicator


class MockRunner(QObject):
    task_started = Signal(str, str, bool)
    task_progress = Signal(str, object)
    task_succeeded = Signal(str, object)
    task_failed = Signal(str, object)
    task_cancelled = Signal(str)

    def cancel_task(self, task_id: str) -> bool:
        return True


def test_global_task_indicator_initial_state(gui_app) -> None:
    indicator = GlobalTaskIndicator()
    assert not indicator.isVisible()

    runner = MockRunner()
    queue = TaskQueue(runner)
    indicator.attach_queue(queue)
    assert not indicator.isVisible()


def test_global_task_indicator_single_task_progress(gui_app) -> None:
    runner = MockRunner()
    queue = TaskQueue(runner)
    indicator = GlobalTaskIndicator(queue)

    assert not indicator.isVisible()

    # Start a task
    runner.task_started.emit("task-1", "Exporting .mrpack", False)
    assert indicator.isVisible()
    assert "Exporting" in indicator.text_label.text()

    # Progress update
    mock_progress = MagicMock()
    mock_progress.percentage = 65.0
    mock_progress.message = "Compressing files"
    mock_progress.stage = "export"

    runner.task_progress.emit("task-1", mock_progress)
    assert indicator.isVisible()
    assert indicator.progress_bar.value() == 65
    assert indicator.percent_label.text() == "65%"
    assert "Compressing files" in indicator.text_label.text()
    assert "Compressing files" in indicator.toolTip()


def test_global_task_indicator_multiple_tasks(gui_app) -> None:
    runner = MockRunner()
    queue = TaskQueue(runner)
    indicator = GlobalTaskIndicator(queue)

    runner.task_started.emit("task-1", "First Task", False)
    runner.task_started.emit("task-2", "Second Task", False)

    assert indicator.isVisible()
    tooltip = indicator.toolTip()
    assert "First Task" in tooltip
    assert "Second Task" in tooltip


def test_global_task_indicator_completion_and_hide(gui_app) -> None:
    runner = MockRunner()
    queue = TaskQueue(runner)
    indicator = GlobalTaskIndicator(queue)

    runner.task_started.emit("task-1", "Task to complete", False)
    assert indicator.isVisible()

    runner.task_succeeded.emit("task-1", None)
    assert indicator.isVisible()
    assert indicator.percent_label.text() == "100%"
    assert indicator._hide_timer.isActive()

    # Simulate timeout
    indicator._on_hide_timeout()
    assert not indicator.isVisible()


def test_global_task_indicator_retranslate(gui_app) -> None:
    runner = MockRunner()
    queue = TaskQueue(runner)
    indicator = GlobalTaskIndicator(queue)

    runner.task_started.emit("task-1", "Localizable Task", False)
    indicator.retranslate_ui()
    assert indicator.isVisible()
