from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtCore import QObject, Signal

from src.gui.core.app_state import AppState
from src.gui.core.gui_context import GuiContext, get_default_gui_context, set_default_gui_context
from src.gui.core.task_queue import TaskQueue, TaskQueueItem


class DummyInstance:
    def __init__(self, name: str) -> None:
        self.name = name


class DummyAccount:
    def __init__(self, account_id: str, username: str) -> None:
        self.account_id = account_id
        self.username = username


class DummyRunner(QObject):
    task_started = Signal(str, str, bool)
    task_progress = Signal(str, object)
    task_succeeded = Signal(str, object)
    task_failed = Signal(str, object)
    task_cancelled = Signal(str)

    def cancel_task(self, task_id: str) -> bool:
        return task_id == "cancellable"


def test_app_state_instances():
    state = AppState()
    received_instances = []
    received_selected_name = []

    state.instances_changed.connect(lambda insts, sel: (received_instances.append(insts), received_selected_name.append(sel)))

    inst1 = DummyInstance("Inst1")
    inst2 = DummyInstance("Inst2")

    state.set_instances([inst1, inst2], "Inst2")
    assert state.instances == [inst1, inst2]
    assert state.selected_instance_name == "Inst2"
    assert len(received_instances) == 1
    assert received_selected_name[-1] == "Inst2"

    selected_signal_payloads = []
    state.selected_instance_changed.connect(selected_signal_payloads.append)
    state.set_selected_instance(inst1)
    assert state.selected_instance == inst1
    assert state.selected_instance_name == "Inst1"
    assert selected_signal_payloads == [inst1]


def test_app_state_accounts_and_connectivity():
    state = AppState()
    acc1 = DummyAccount("acc-1", "Steve")
    acc2 = DummyAccount("acc-2", "Alex")

    received_accounts = []
    state.accounts_changed.connect(lambda accs, sel: received_accounts.append((accs, sel)))

    state.set_accounts([acc1, acc2], "acc-1")
    assert state.accounts == [acc1, acc2]
    assert state.selected_account_id == "acc-1"
    assert len(received_accounts) == 1

    state.set_selected_account(acc2)
    assert state.selected_account == acc2
    assert state.selected_account_id == "acc-2"

    online_events = []
    state.connectivity_changed.connect(online_events.append)
    state.set_online(False)
    assert not state.is_online
    state.set_online(True)
    assert state.is_online
    assert online_events == [False, True]


def test_task_queue_lifecycle():
    runner = DummyRunner()
    queue = TaskQueue(runner=runner)

    enqueued = []
    updated = []
    completed = []

    queue.task_enqueued.connect(enqueued.append)
    queue.task_updated.connect(updated.append)
    queue.task_completed.connect(completed.append)

    runner.task_started.emit("task-1", "Downloading asset", False)
    assert len(enqueued) == 1
    assert enqueued[0].task_id == "task-1"
    assert enqueued[0].status == "running"
    assert len(queue.active_tasks()) == 1

    progress_mock = MagicMock()
    progress_mock.percentage = 45.0
    progress_mock.message = "Downloading 45%"
    progress_mock.stage = "download"

    runner.task_progress.emit("task-1", progress_mock)
    assert len(updated) == 1
    assert updated[0].percentage == 45.0
    assert updated[0].message == "Downloading 45%"

    runner.task_succeeded.emit("task-1", None)
    assert len(completed) == 1
    assert completed[0].status == "succeeded"
    assert len(queue.active_tasks()) == 0

    assert queue.cancel_task("cancellable")
    assert not queue.cancel_task("other")

    queue.clear_completed()
    assert len(queue.all_tasks()) == 0


def test_gui_context_controller_registration_and_wiring():
    runner = DummyRunner()
    context = GuiContext(task_runner=runner)

    class DummyInstanceController(QObject):
        instances_changed = Signal(list, str)
        selected_instance_changed = Signal(object)
        running_instances_changed = Signal(list)
        health_reports_changed = Signal(list)

    ctrl = DummyInstanceController()
    context.register_controller("instances", ctrl)

    assert context.instances is ctrl
    assert context.controller("instances") is ctrl

    inst = DummyInstance("Alpha")
    ctrl.instances_changed.emit([inst], "Alpha")
    assert context.state.instances == [inst]
    assert context.state.selected_instance_name == "Alpha"

    ctrl.selected_instance_changed.emit(inst)
    assert context.state.selected_instance == inst

    set_default_gui_context(context)
    assert get_default_gui_context() is context
    set_default_gui_context(None)
    assert get_default_gui_context() is None
