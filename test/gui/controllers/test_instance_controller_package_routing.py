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

    def run(self, task_id: str, task: object, _message: str, blocking: bool = True) -> bool:
        try:
            result = task()
        except Exception as error:
            self.task_failed.emit(task_id, error)
        else:
            self.task_succeeded.emit(task_id, result)
        return True


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


def test_library_metadata_update_uses_public_instance_service_and_refreshes(gui_app, monkeypatch: pytest.MonkeyPatch) -> None:
    class _LibraryInstances(_Instances):
        def set_library_metadata(self, name: str, **changes):
            self.updated = (name, changes)
            return SimpleNamespace(name=name)

    instances = _LibraryInstances()
    controller = _controller(instances)
    refreshed: list[str] = []
    monkeypatch.setattr(controller, "refresh", lambda selected_name="": refreshed.append(selected_name))

    controller.set_favorite("ATM9", True)

    assert instances.updated == ("ATM9", {"favorite": True})
    assert refreshed == ["ATM9"]


def test_selected_instance_loads_runtime_profile_through_public_service(gui_app) -> None:
    profile = SimpleNamespace(instance_name="Test", required_java_major=17)

    class _RuntimeInstances(_Instances):
        def load(self, name: str) -> object:
            return SimpleNamespace(name=name)

        def runtime_profile(self, name: str) -> object:
            assert name == "Test"
            return profile

    controller = _controller(_RuntimeInstances())
    selected: list[object] = []
    profiles: list[object] = []
    controller.selected_instance_changed.connect(selected.append)
    controller.runtime_profile_changed.connect(profiles.append)

    controller.select("Test")

    assert [item.name for item in selected] == ["Test"]
    assert profiles == [profile]


def test_java_runtime_update_uses_public_instance_service(gui_app, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = SimpleNamespace(instance_name="ATM9", required_java_major=17)

    class _RuntimeInstances(_Instances):
        def set_java_runtime(self, name: str, path: str) -> object:
            self.updated = (name, path)
            return profile

    instances = _RuntimeInstances()
    controller = _controller(instances)
    refreshed: list[str] = []
    profiles: list[object] = []
    monkeypatch.setattr(controller, "refresh", lambda selected_name="": refreshed.append(selected_name))
    controller.runtime_profile_changed.connect(profiles.append)

    controller.set_java_runtime("ATM9", r"C:\Java17\bin\javaw.exe")

    assert instances.updated == ("ATM9", r"C:\Java17\bin\javaw.exe")
    assert profiles == [profile]
    assert refreshed == ["ATM9"]
