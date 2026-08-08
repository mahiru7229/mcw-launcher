from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.gui.controllers.gui_settings_controller import GuiSettingsController


@pytest.fixture(autouse=True)
def isolate_curseforge_gateway_storage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("src.gui.controllers.gui_settings_controller.CurseForgeConfigManager.gateway_urls", lambda: ())
    monkeypatch.setattr("src.gui.controllers.gui_settings_controller.CurseForgeConfigManager.save_local", lambda *_args, **_kwargs: tmp_path / "curseforge.json")


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


def test_content_description_visibility_round_trips_through_gui_settings(tmp_path: Path) -> None:
    settings_path = tmp_path / "launcher_settings.json"
    controller = _controller(settings_path)
    data = controller.load()

    assert data["show_content_descriptions"] is False

    data["show_content_descriptions"] = True
    controller.save(data)

    assert controller.current["show_content_descriptions"] is True
    assert LauncherSettingsManager(settings_path).load()["gui"]["show_content_descriptions"] is True


def test_legacy_storage_notification_setting_round_trips(tmp_path: Path) -> None:
    settings_path = tmp_path / "launcher_settings.json"
    controller = _controller(settings_path)

    data = controller.load()
    assert data["notify_legacy_cache_cleanup"] is True

    controller.set_notify_legacy_cache_cleanup(False)

    assert controller.current["notify_legacy_cache_cleanup"] is False
    assert LauncherSettingsManager(settings_path).load()["storage"]["notify_legacy_cache_cleanup"] is False
