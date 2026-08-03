from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

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
