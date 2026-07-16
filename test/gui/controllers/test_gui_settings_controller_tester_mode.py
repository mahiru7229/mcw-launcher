from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.gui.controllers.gui_settings_controller import GuiSettingsController


def _controller(path: Path) -> GuiSettingsController:
    controller = GuiSettingsController()
    controller._settings = LauncherSettingsManager(path)
    return controller


def test_tester_mode_maps_to_beta_channel(tmp_path: Path) -> None:
    settings_path = tmp_path / "launcher_settings.json"
    controller = _controller(settings_path)
    data = controller.load()

    data["tester_mode"] = True
    controller.save(data)

    assert controller.current["tester_mode"] is True
    assert controller.current["update_channel"] == "beta"
    assert LauncherSettingsManager(settings_path).load()["updates"]["channel"] == "beta"


def test_disabling_tester_mode_returns_to_stable(tmp_path: Path) -> None:
    settings_path = tmp_path / "launcher_settings.json"
    controller = _controller(settings_path)
    data = controller.load()
    data["tester_mode"] = True
    controller.save(data)

    data = controller.current
    data["tester_mode"] = False
    controller.save(data)

    assert controller.current["tester_mode"] is False
    assert controller.current["update_channel"] == "stable"
    assert LauncherSettingsManager(settings_path).load()["updates"]["channel"] == "stable"
