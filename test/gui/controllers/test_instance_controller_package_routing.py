from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.controllers.instance_controller import InstanceController


class _Signal:
    def __init__(self) -> None:
        self._slots: list[object] = []

    def connect(self, slot: object) -> None:
        self._slots.append(slot)

    def emit(self, *args: object) -> None:
        for slot in tuple(self._slots):
            slot(*args)


class _TaskRunner:
    def __init__(self) -> None:
        self.task_succeeded = _Signal()
        self.task_failed = _Signal()

    def run(self, task_id: str, task: object, _message: str) -> None:
        try:
            result = task()
        except Exception as error:
            self.task_failed.emit(task_id, error)
        else:
            self.task_succeeded.emit(task_id, result)


class _Instances:
    def __init__(self, modpack_preview: object | None = None, instance_preview: object | None = None) -> None:
        self.modpack_preview = modpack_preview
        self.instance_preview = instance_preview
        self.modpack_calls = 0
        self.instance_calls = 0

    def inspect_modpack_package(self, _path: Path) -> object:
        self.modpack_calls += 1
        if self.modpack_preview is None:
            raise RuntimeError("Unsupported modpack package.")
        return self.modpack_preview

    def inspect_package(self, _path: Path) -> object:
        self.instance_calls += 1
        if self.instance_preview is None:
            raise RuntimeError("Invalid package: missing package.json.")
        return self.instance_preview


def _controller(instances: _Instances) -> InstanceController:
    controller = InstanceController(_TaskRunner())
    controller._core = SimpleNamespace(instances=instances)
    return controller


def test_generic_import_routes_provider_profile_to_modpack_preview(gui_app) -> None:
    preview = SimpleNamespace(name="Provider Pack", package_path=Path("profile.zip"))
    instances = _Instances(modpack_preview=preview)
    controller = _controller(instances)
    received: list[object] = []
    controller.modpack_import_preview_ready.connect(received.append)

    controller.inspect_package(Path("profile.zip"))

    assert received == [preview]
    assert instances.modpack_calls == 1
    assert instances.instance_calls == 0


def test_generic_import_falls_back_to_legacy_instance_package(gui_app) -> None:
    preview = SimpleNamespace(name="Legacy Instance", package_path=Path("instance.mcwpack"))
    instances = _Instances(instance_preview=preview)
    controller = _controller(instances)
    received: list[object] = []
    controller.import_preview_ready.connect(received.append)

    controller.inspect_package(Path("instance.mcwpack"))

    assert received == [preview]
    assert instances.modpack_calls == 1
    assert instances.instance_calls == 1
