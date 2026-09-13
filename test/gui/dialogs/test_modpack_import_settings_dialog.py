from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from mcw_core.api.instance.settings_manager import SettingsManager
from mcw_core.api.java.jvm_presets import JvmPresetId, get_preset_flags
from mcw_core.api.language.language_manager import tr
from src.gui.dialogs.modpack_import_settings_dialog import ModpackImportSettingsDialog
from src.models.package.provider_modpack_preview import ProviderModpackPreview


def _modpack_preview(has_settings: bool = False, settings: dict | None = None) -> ProviderModpackPreview:
    return ProviderModpackPreview(
        package_path=Path("sample.mrpack"),
        provider="modrinth",
        package_format="mrpack",
        name="Sample Modpack",
        version_id="1.0.0",
        version_label="1.0.0",
        version_id_source="modrinth",
        version_id_is_provider_native=True,
        minecraft_version="1.20.4",
        mod_loader=("fabric", "0.16.14"),
        file_count=24,
        settings=settings or {},
        has_package_settings=has_settings,
    )


def test_modpack_import_dialog_jvm_preset_selection(gui_app) -> None:
    launcher_defaults = SettingsManager.default_dict()
    dialog = ModpackImportSettingsDialog(_modpack_preview(), launcher_defaults)

    assert dialog.instance_name == "Sample Modpack"
    assert dialog.install_optional_files is True

    # Select Aikar preset
    aikar_idx = dialog.jvm_preset_combo.findData(JvmPresetId.AIKAR)
    assert aikar_idx >= 0
    dialog.jvm_preset_combo.setCurrentIndex(aikar_idx)

    selected = dialog.selected_settings_override
    assert selected["java"]["arguments"] == get_preset_flags(JvmPresetId.AIKAR)
    assert dialog.jvm_preset_combo.currentData() == JvmPresetId.AIKAR

    # Select ZGC preset
    zgc_idx = dialog.jvm_preset_combo.findData(JvmPresetId.ZGC)
    assert zgc_idx >= 0
    dialog.jvm_preset_combo.setCurrentIndex(zgc_idx)
    assert dialog.selected_settings_override["java"]["arguments"] == get_preset_flags(JvmPresetId.ZGC)


def test_modpack_import_dialog_detects_existing_preset(gui_app) -> None:
    settings = SettingsManager.default_dict()
    settings["java"]["arguments"] = get_preset_flags(JvmPresetId.SHENANDOAH)
    preview = _modpack_preview(has_settings=True, settings=settings)

    dialog = ModpackImportSettingsDialog(preview, SettingsManager.default_dict())

    assert dialog.jvm_preset_combo.currentData() == JvmPresetId.SHENANDOAH
    assert dialog.selected_settings_override["java"]["arguments"] == get_preset_flags(JvmPresetId.SHENANDOAH)
