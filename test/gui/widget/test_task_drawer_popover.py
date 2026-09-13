from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject, QPointF, Qt, Signal
from PySide6.QtGui import QMouseEvent

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.core.task_queue import TaskQueue
from src.gui.widget.global_task_indicator import GlobalTaskIndicator
from src.gui.widget.task_drawer_popover import TaskDrawerPopover


class MockRunner(QObject):
    task_started = Signal(str, str, bool)
    task_progress = Signal(str, object)
    task_succeeded = Signal(str, object)
    task_failed = Signal(str, object)
    task_cancelled = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.cancelled_tasks: list[str] = []

    def cancel_task(self, task_id: str) -> bool:
        self.cancelled_tasks.append(task_id)
        self.task_cancelled.emit(task_id)
        return True


def test_task_drawer_popover_empty_state(gui_app) -> None:
    runner = MockRunner()
    queue = TaskQueue(runner)
    drawer = TaskDrawerPopover(queue)

    assert not drawer.no_active_label.isHidden()
    assert not drawer.no_completed_label.isHidden()


def test_task_drawer_popover_active_and_completed_tasks(gui_app) -> None:
    runner = MockRunner()
    queue = TaskQueue(runner)
    drawer = TaskDrawerPopover(queue)

    # Start an active task
    runner.task_started.emit("task-1", "Exporting .mrpack", False)
    mock_progress = MagicMock()
    mock_progress.percentage = 45.0
    mock_progress.message = "Writing index"
    mock_progress.stage = "export"
    runner.task_progress.emit("task-1", mock_progress)

    drawer.refresh()
    assert drawer.active_container.count() > 0

    # Complete a second task
    runner.task_started.emit("task-2", "Downloading mod", False)
    runner.task_succeeded.emit("task-2", None)

    drawer.refresh()
    assert drawer.completed_container.count() > 0

    # Cancel task-1 via runner
    assert runner.cancel_task("task-1")
    drawer.refresh()

    # Now both tasks are in completed
    assert len(queue.active_tasks()) == 0
    assert len(queue.all_tasks()) == 2

    # Clear history
    drawer.clear_button.click()
    assert len(queue.all_tasks()) == 0


def test_global_task_indicator_toggle_drawer(gui_app) -> None:
    runner = MockRunner()
    queue = TaskQueue(runner)
    indicator = GlobalTaskIndicator(queue)

    # Click on indicator to toggle drawer
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(10, 10),
        QPointF(10, 10),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    indicator.mousePressEvent(press_event)

    assert indicator._drawer is not None
    assert indicator._drawer.isVisible()

    # Click again to close
    indicator.mousePressEvent(press_event)
    assert not indicator._drawer.isVisible()
