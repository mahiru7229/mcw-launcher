import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from mcw_core.api.language.language_manager import language_manager
from src.gui.pages.instances_page import InstancesPage
from src.models.modloader.fabric_loader_version import FabricLoaderVersion


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def make_instance(name="Fabric", version_id="1.21.1", mod_loader=("fabric", "0.18.6")):
    return SimpleNamespace(name=name, version_id=version_id, instance_dir=f"instances/{name}", mod_loader=mod_loader)


def test_advanced_instance_page_does_not_expose_create_instance_controls(app):
    page = InstancesPage()

    assert not hasattr(page, "create_name_input")
    assert not hasattr(page, "version_combo")
    assert not hasattr(page, "create_loader_combo")
    assert not hasattr(page, "snapshot_checkbox")
    assert not hasattr(page, "create_requested")
    assert not hasattr(page, "browse_modpacks_button")
    assert not hasattr(page, "import_modpack_package_button")


def test_selected_instance_updates_manage_loader_controls(app):
    page = InstancesPage()
    requested = []
    page.fabric_versions_requested.connect(requested.append)

    page.set_instances([make_instance()], "Fabric")

    assert page.manage_loader_combo.currentText() == "Fabric"
    assert requested == ["1.21.1"]


def test_manage_loader_prefers_current_fabric_version(app):
    page = InstancesPage()
    instance = make_instance()
    page.set_instances([instance], instance.name)
    page.set_fabric_versions(
        instance.version_id,
        [
            FabricLoaderVersion(version="0.19.3", stable=True),
            FabricLoaderVersion(version="0.18.6", stable=True),
        ],
    )

    assert page.manage_loader_version_combo.currentData() == "0.18.6"
    assert page.apply_loader_button.isEnabled() is True


def test_manage_loader_uses_stable_version_when_applying_fabric_to_vanilla(app):
    page = InstancesPage()
    instance = make_instance(name="Vanilla", mod_loader=("vanilla", "-1"))
    page.set_instances([instance], instance.name)
    page._fabric_versions[instance.version_id] = [
        FabricLoaderVersion(version="0.20.0-beta", stable=False),
        FabricLoaderVersion(version="0.19.3", stable=True),
    ]

    page.manage_loader_combo.setCurrentText("Fabric")

    assert page.manage_loader_version_combo.currentData() == "0.19.3"
    assert page.selected_manage_loader() == ("fabric", "0.19.3")


def test_repair_fabric_is_only_available_for_fabric_instances(app):
    page = InstancesPage()
    fabric = make_instance()
    page.set_instances([fabric], fabric.name)
    emitted = []
    page.repair_loader_requested.connect(emitted.append)

    assert page.repair_loader_button.isEnabled() is True
    page._request_loader_repair()
    assert emitted == [fabric.name]

    vanilla = make_instance(name="Vanilla", mod_loader=("vanilla", "-1"))
    page.set_instances([vanilla], vanilla.name)
    assert page.repair_loader_button.isEnabled() is False


def test_modpack_repair_button_emits_and_recovers_after_busy(app, monkeypatch, tmp_path):
    instance_dir = tmp_path / "Pack"
    registry = instance_dir / ".mcw" / "modrinth-pack.json"
    registry.parent.mkdir(parents=True)
    registry.write_text("{}", encoding="utf-8")
    instance = SimpleNamespace(name="Pack", version_id="1.21.1", instance_dir=instance_dir, mod_loader=("fabric", "0.18.6"))
    page = InstancesPage()
    page.set_instances([instance], instance.name)
    emitted = []
    page.repair_modpack_requested.connect(emitted.append)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)

    assert page.repair_modpack_button.isEnabled() is True
    page.set_modpack_busy(True)
    assert page.repair_modpack_button.isEnabled() is False
    page.set_modpack_busy(False)
    assert page.repair_modpack_button.isEnabled() is True

    page._confirm_modpack_repair()
    assert emitted == ["Pack"]


def test_manage_neoforge_versions_and_repair_are_available(app):
    from src.models.modloader.neoforge_loader_version import NeoForgeLoaderVersion

    page = InstancesPage()
    instance = make_instance(name="NeoForge", version_id="1.21.1", mod_loader=("neoforge", "21.1.200"))
    page.set_instances([instance], instance.name)
    page.set_neoforge_versions(
        instance.version_id,
        [
            NeoForgeLoaderVersion("1.21.1", "21.1.201"),
            NeoForgeLoaderVersion("1.21.1", "21.1.200"),
        ],
    )

    assert page.manage_loader_combo.currentData() == "neoforge"
    assert page.manage_loader_version_combo.currentData() == "21.1.200"
    assert page.selected_manage_loader() == ("neoforge", "21.1.200")
    assert page.manage_mods_button.isEnabled() is True
    assert page.repair_loader_button.isEnabled() is True
    assert page.export_forge_diagnostics_button.isEnabled() is True


def test_advanced_instance_page_is_fully_retranslated_to_vietnamese(app):
    previous = language_manager.current_locale
    language_manager.set_language("vi-VN", notify=False)
    try:
        page = InstancesPage()

        assert page.title_label.text() == "Instance"
        assert page.subtitle_label.text() == "Quản lý instance Minecraft đã chọn, mod loader, công cụ bảo trì, bản sao lưu và trạng thái modpack được quản lý."
        assert page.refresh_instances_button.text() == "Làm mới danh sách instance"
        assert page.apply_loader_button.text() == "Áp dụng mod loader"
        assert not hasattr(page, "create_name_input")
    finally:
        language_manager.set_language(previous, notify=False)


def test_mod_loader_layout_reflows_for_wide_medium_and_narrow_widths(app):
    page = InstancesPage()

    page._sync_responsive_layout(width=900, force=True)
    assert page.loader_fields_layout.getItemPosition(page.loader_fields_layout.indexOf(page.manage_loader_label)) == (0, 0, 1, 1)
    assert page.loader_fields_layout.getItemPosition(page.loader_fields_layout.indexOf(page.manage_loader_version_label)) == (0, 1, 1, 1)
    assert page.loader_actions_layout.getItemPosition(page.loader_actions_layout.indexOf(page.restore_forge_button)) == (0, 2, 1, 1)
    assert page._compact is False

    page._sync_responsive_layout(width=620, force=True)
    assert page.loader_fields_layout.getItemPosition(page.loader_fields_layout.indexOf(page.manage_loader_combo)) == (1, 0, 1, 1)
    assert page.loader_fields_layout.getItemPosition(page.loader_fields_layout.indexOf(page.manage_loader_version_label)) == (2, 0, 1, 1)
    assert page.loader_actions_layout.getItemPosition(page.loader_actions_layout.indexOf(page.restore_forge_button)) == (1, 0, 1, 1)
    assert page.instance_actions_layout.getItemPosition(page.instance_actions_layout.indexOf(page.delete_button)) == (1, 0, 1, 1)
    assert page._compact is True

    page._sync_responsive_layout(width=480, force=True)
    assert page.loader_actions_layout.getItemPosition(page.loader_actions_layout.indexOf(page.repair_loader_button)) == (1, 0, 1, 1)
    assert page.instance_actions_layout.getItemPosition(page.instance_actions_layout.indexOf(page.clone_button)) == (1, 0, 1, 1)
    assert page.instance_actions_layout.getItemPosition(page.instance_actions_layout.indexOf(page.repair_instance_button)) == (6, 0, 1, 1)


def test_mod_loader_comboboxes_can_shrink_without_horizontal_overflow(app):
    from PySide6.QtWidgets import QComboBox, QSizePolicy

    page = InstancesPage()

    assert page.manage_loader_combo.sizeAdjustPolicy() == QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
    assert page.manage_loader_version_combo.sizeAdjustPolicy() == QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
    assert page.manage_loader_combo.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
    assert page.manage_loader_version_combo.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
