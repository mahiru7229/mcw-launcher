from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal

from mcw_core import LaunchResult
from mcw_core import facade
from src.gui.controllers import launch_controller as launch_controller_module
from src.gui.controllers.launch_controller import LaunchController
from src.models.account.account import Account
from src.models.account.account_source import AccountSource
from src.models.auth.authentication import Authentication


class FakeOperations:
    def __init__(self) -> None:
        self.begin_count = 0
        self.checkpoint_count = 0
        self.finish_count = 0

    def begin(self) -> None:
        self.begin_count += 1

    def checkpoint(self) -> None:
        self.checkpoint_count += 1

    def finish(self) -> None:
        self.finish_count += 1


class FakeCore:
    def __init__(self) -> None:
        self.operations = FakeOperations()
        self.request = None
        self.identity = None

    def launch(self, request):
        self.request = request
        self.identity = facade.MCWCore._resolve_identity(request)
        return LaunchResult(
            java_path=Path("javaw.exe"),
            minecraft_java_major_version=17,
            minecraft_version="1.20.1",
        )


class FakeTaskRunner(QObject):
    task_succeeded = Signal(str, object)
    task_failed = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.result = None

    def is_task_active(self, task_id: str) -> bool:
        return False

    def run(self, task_id: str, task, message: str, blocking: bool = True) -> bool:
        self.result = task()
        return True


def test_launch_controller_uses_account_authentication_dispatcher(monkeypatch: pytest.MonkeyPatch) -> None:
    account = Account(
        account_id="microsoft-account",
        account_type=AccountSource.MICROSOFT,
        username="Player",
        uuid="1234567890abcdef1234567890abcdef",
    )
    authentication = Authentication(
        player_name="Player",
        uuid=account.uuid,
        access_token="token",
        xuid="xuid",
        client_id="client-id",
        user_type="msa",
    )
    dispatched: list[Account] = []
    core = FakeCore()
    runner = FakeTaskRunner()

    monkeypatch.setattr(launch_controller_module, "get_default_core", lambda: core)
    monkeypatch.setattr(
        facade.AccountAuthentication,
        "authenticate",
        lambda selected: dispatched.append(selected) or authentication,
    )

    controller = LaunchController(runner)
    controller.set_instance(SimpleNamespace(name="Example"))
    controller.set_account(account)
    controller.launch()

    assert core.request is not None
    assert core.request.account is account
    assert dispatched == [account]
    assert core.identity == (account, authentication)
    assert runner.result["minecraftVersion"] == "1.20.1"
    assert core.operations.begin_count == 1
    assert core.operations.checkpoint_count == 1
    assert core.operations.finish_count == 1
