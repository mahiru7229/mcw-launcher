from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from src.core.instance.settings_manager import SettingsManager
from src.core.language.language_manager import tr
from src.gui.dialogs.instance_import_settings_dialog import InstanceImportSettingsDialog
from src.gui.dialogs.instance_settings_editor_dialog import InstanceSettingsEditorDialog
from src.models.package.instance_package_preview import InstancePackagePreview
from src.models.package.package_metadata import PackageMetadata


def _settings(max_memory: int) -> dict:
    data = SettingsManager.default_dict()
    data["java"]["min_memory"] = 1024
    data["java"]["max_memory"] = max_memory
    return data


def _preview(has_settings: bool = True) -> InstancePackagePreview:
    return InstancePackagePreview(
        package_path=Path("pack.mcwpack"),
        name="Pack",
        version_id="1.20.4",
        mod_loader=("fabric", "0.16.14"),
        icon="grass_block",
        settings=_settings(4096),
        has_package_settings=has_settings,
        package_metadata=PackageMetadata(
            format="mcwpack",
            format_version=1,
            package_type="instance",
            launcher_name="mcw-launcher",
            launcher_version="v0.10.0-beta.1",
            created_at="2026-07-28T00:00:00+00:00",
            include_saves=False,
        ),
    )


def test_settings_editor_round_trips_every_instance_setting(gui_app) -> None:
    source = _settings(4096)
    source["java"]["path"] = "C:/Java/bin/javaw.exe"
    source["java"]["arguments"] = ["-XX:+UseG1GC"]
    source["window"] = {"width": 1920, "height": 1080, "fullscreen": True}
    source["launch"].update({
        "game_arguments": ["--demo"],
        "lan_auth_mode": "private_offline",
        "lan_connection_provider": "e4mc",
        "modrinth_failure_policy": "allow",
        "curseforge_failure_policy": "block",
        "forge_preflight_failure_policy": "allow",
    })

    dialog = InstanceSettingsEditorDialog(source, total_memory_mb=8192)

    assert dialog.settings_data == SettingsManager.normalize_dict(source)
    assert "4 GB" in dialog.summary(source)
    assert dialog.cancel_button.text() == tr("common.cancel")


def test_import_defaults_to_overwriting_with_launcher_defaults(gui_app) -> None:
    launcher_defaults = _settings(6144)
    dialog = InstanceImportSettingsDialog(_preview(), launcher_defaults)

    assert dialog.selected_mode == dialog.MODE_LAUNCHER_DEFAULTS
    assert dialog.selected_settings_override == SettingsManager.normalize_dict(launcher_defaults)
    assert dialog.cancel_button.text() == tr("common.cancel")


def test_import_can_keep_or_review_package_settings(gui_app) -> None:
    dialog = InstanceImportSettingsDialog(_preview(), _settings(6144))

    dialog.keep_package_radio.setChecked(True)
    assert dialog.selected_mode == dialog.MODE_KEEP_PACKAGE
    assert dialog.selected_settings_override is None

    dialog.review_radio.setChecked(True)
    dialog._review_settings = _settings(7168)
    dialog._review_confirmed = True
    assert dialog.selected_mode == dialog.MODE_REVIEW
    assert dialog.selected_settings_override == SettingsManager.normalize_dict(_settings(7168))


def test_keep_package_mode_is_disabled_when_settings_are_missing(gui_app) -> None:
    dialog = InstanceImportSettingsDialog(_preview(has_settings=False), _settings(6144))

    assert dialog.keep_package_radio.isEnabled() is False
    assert dialog.selected_mode == dialog.MODE_LAUNCHER_DEFAULTS
