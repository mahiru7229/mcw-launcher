from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from mcw_core.api.language.language_manager import language_manager
from src.gui.pages.instance_workspace_page import InstanceWorkspacePage


def make_instance(name: str, loader=("vanilla", "-1"), version: str = "1.20.1") -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        version_id=version,
        instance_dir=f"instances/{name}",
        mod_loader=loader,
        icon="",
    )


def test_workspace_builds_instance_library_and_keeps_selected_instance(gui_app):
    page = InstanceWorkspacePage()
    vanilla = make_instance("Vanilla")
    quilt = make_instance("Quilt Pack", ("quilt", "0.30.1"), "1.21.1")

    page.set_instances([vanilla, quilt], quilt.name)

    assert page.instance_list.count() == 2
    assert page.current_instance_name() == "Quilt Pack"
    assert page.instance_name_label.text() == "Quilt Pack"
    assert page.manage_mods_button.isEnabled() is True


def test_workspace_search_filters_by_loader_and_version(gui_app):
    page = InstanceWorkspacePage()
    page.set_instances(
        [
            make_instance("Old Vanilla", version="1.12.2"),
            make_instance("Modern Quilt", ("quilt", "0.30.1"), "1.21.1"),
        ],
        "Old Vanilla",
    )

    page.search_input.setText("quilt")

    visible = [
        page.instance_list.item(index).data(page.ITEM_NAME_ROLE)
        for index in range(page.instance_list.count())
        if not page.instance_list.item(index).isHidden()
    ]
    assert visible == ["Modern Quilt"]
    assert page.current_instance_name() == "Modern Quilt"


def test_workspace_selection_emits_instance_name(gui_app):
    page = InstanceWorkspacePage()
    first = make_instance("First")
    second = make_instance("Second", ("fabric", "0.16.14"))
    page.set_instances([first, second], first.name)
    emitted: list[str] = []
    page.selected_instance_changed.connect(emitted.append)

    second_item = next(
        page.instance_list.item(index)
        for index in range(page.instance_list.count())
        if page.instance_list.item(index).data(page.ITEM_NAME_ROLE) == second.name
    )
    page.instance_list.setCurrentItem(second_item)

    assert emitted[-1] == "Second"
    assert page.current_instance_name() == "Second"


def test_workspace_create_dialog_emits_public_create_contract(gui_app):
    page = InstanceWorkspacePage()
    page.set_versions([SimpleNamespace(id="1.21.1", type="release")])
    emitted: list[tuple[str, str, str]] = []
    page.create_requested.connect(lambda name, version, loader: emitted.append((name, version, loader)))

    page.create_dialog.name_input.setText("New Quilt")
    page.create_dialog.loader_combo.setCurrentIndex(page.create_dialog.loader_combo.findData("quilt"))
    page.create_dialog._request_create()

    assert emitted == [("New Quilt", "1.21.1", "quilt")]
    assert not hasattr(page.advanced_page, "create_name_input")
    assert not hasattr(page.advanced_page, "create_requested")


def test_workspace_exposes_content_pack_management_for_selected_instance(gui_app):
    page = InstanceWorkspacePage()
    instance = make_instance("Visual Pack", ("fabric", "0.16.14"), "1.21.1")
    emitted: list[str] = []
    page.manage_content_packs_requested.connect(emitted.append)

    page.set_instances([instance], instance.name)
    page.manage_content_packs_button.click()

    assert page.manage_content_packs_button.isEnabled() is True
    assert emitted == ["Visual Pack"]


def test_advanced_dialog_title_and_content_follow_vietnamese_language(gui_app):
    previous = language_manager.current_locale
    language_manager.set_language("vi-VN", notify=False)
    try:
        page = InstanceWorkspacePage()
        page.advanced_dialog.set_instance_name("Latest")

        assert page.advanced_dialog.windowTitle() == "Quản lý instance nâng cao — Latest"
        assert page.advanced_page.refresh_instances_button.text() == "Làm mới danh sách instance"
        assert page.advanced_dialog.close_button is not None
        assert page.advanced_dialog.close_button.text() == "Đóng"
    finally:
        language_manager.set_language(previous, notify=False)
