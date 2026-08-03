import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QSizePolicy

from src.gui.dialogs.curseforge_browser_dialog import CurseForgeBrowserDialog
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.project import CurseForgeProject, CurseForgeSearchResult


def _project() -> CurseForgeProject:
    return CurseForgeProject(
        project_id=11,
        name="Fabric Pack",
        slug="fabric-pack",
        summary="A Fabric test pack",
        download_count=100,
        authors=("Author",),
        logo_url="",
        class_id=4471,
        date_modified="2026-07-28T00:00:00Z",
        project_url="https://www.curseforge.com/minecraft/modpacks/fabric-pack",
        game_versions=("1.20.1",),
        loaders=("fabric",),
    )


def _file(loader: str) -> CurseForgeFile:
    return CurseForgeFile(
        file_id=22,
        project_id=11,
        display_name=f"{loader.title()} Pack 1.0",
        file_name=f"{loader}-pack.zip",
        release_type="release",
        file_date="2026-07-28T00:00:00Z",
        file_length=100,
        download_url="https://example.invalid/pack.zip",
        sha1="a" * 40,
        game_versions=("1.20.1",),
        dependencies=(),
        loaders=(loader,),
    )


def test_modpack_dialog_selects_fabric_or_forge_loader(gui_app) -> None:
    dialog = CurseForgeBrowserDialog("modpack")

    assert dialog.loader == "fabric"
    assert "Fabric" in dialog.context_label.text()

    dialog.loader_combo.setCurrentIndex(dialog.loader_combo.findData("forge"))

    assert dialog.loader == "forge"
    assert "Forge" in dialog.context_label.text()


def test_modpack_dialog_ignores_stale_loader_results_and_emits_selected_loader(gui_app) -> None:
    dialog = CurseForgeBrowserDialog("modpack")
    dialog.loader_combo.setCurrentIndex(dialog.loader_combo.findData("forge"))
    result = CurseForgeSearchResult(projects=(_project(),), total_count=1, index=0, page_size=25)

    dialog.set_search_result(result, "fabric")
    assert dialog.results_table.rowCount() == 0

    dialog.set_search_result(result, "forge")
    assert dialog.results_table.rowCount() == 1

    dialog.set_files(11, [_file("fabric")], "fabric")
    assert dialog.file_combo.count() == 0

    dialog.set_files(11, [_file("forge")], "forge")
    emitted = []
    dialog.install_modpack_requested.connect(lambda *args: emitted.append(args))
    dialog._request_install()

    assert dialog.file_combo.count() == 1
    assert dialog.install_button.isEnabled() is False
    assert emitted == []
    gui_app.processEvents()
    assert emitted
    assert emitted[0][-1] == "forge"


def test_modpack_dialog_keeps_long_install_controls_on_separate_rows(gui_app) -> None:
    dialog = CurseForgeBrowserDialog("modpack")

    assert dialog.detail_panel.minimumWidth() >= 500
    assert dialog.detail_panel.actions_layout.count() == 3
    assert dialog.file_combo.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
    assert dialog.instance_name_input.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
    assert dialog.install_button.minimumWidth() >= 220


def test_project_detail_metadata_wraps_into_short_rows(gui_app) -> None:
    html = CurseForgeBrowserDialog("modpack").detail_panel._metadata_html(
        {"Downloads": "1", "Updated": "2", "Minecraft": "3", "Loader": "4", "Categories": "5"}
    )

    assert html.count("<br>") == 2


def test_dialog_is_wide_and_description_is_opt_in(gui_app) -> None:
    dialog = CurseForgeBrowserDialog("modpack")

    assert dialog.width() >= dialog.height()
    assert dialog.width() <= 1240
    assert dialog.height() <= 620
    assert dialog.maximumWidth() == dialog.width()
    assert dialog.maximumHeight() == dialog.height()
    assert dialog.detail_panel.description_visible is False

    dialog.set_show_project_descriptions(True)
    assert dialog.detail_panel.description_visible is True


def test_clear_cache_feedback_is_visible_before_dispatch(gui_app) -> None:
    dialog = CurseForgeBrowserDialog("modpack")
    emitted = []
    dialog.clear_cache_requested.connect(lambda: emitted.append(True))

    dialog._request_clear_cache()

    assert dialog.clear_cache_button.isEnabled() is False
    assert emitted == []
    gui_app.processEvents()
    assert emitted == [True]
