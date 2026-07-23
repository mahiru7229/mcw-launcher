import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from pathlib import Path

from src.gui.pages.mods_page import ModsPage
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthFile, ModrinthVersion


def _project() -> ModrinthProject:
    return ModrinthProject(
        project_id="project",
        slug="example",
        title="Example Mod",
        description="Example description",
        project_type="mod",
        author="Tester",
        downloads=123,
        date_modified="2026-07-20T00:00:00Z",
    )


def _version(version_id: str, loader: str, game_version: str = "1.21.1") -> ModrinthVersion:
    return ModrinthVersion(
        version_id=version_id,
        project_id="project",
        name=version_id,
        version_number="1.0.0",
        version_type="release",
        game_versions=(game_version,),
        loaders=(loader,),
        files=(ModrinthFile(url="https://example.invalid/mod.jar", filename="mod.jar", sha1="a", sha512="b", size=1, primary=True),),
    )


def test_mods_page_filters_versions_by_loader_and_requests_instance_choice(gui_app):
    page = ModsPage()
    emitted = []
    page.install_requested.connect(lambda version, loader, channels: emitted.append((version, loader, tuple(channels))))

    page.set_search_result(ModrinthSearchResult(projects=(_project(),), total_hits=1, offset=0, limit=25), "fabric")
    page.set_versions("project", [_version("fabric-version", "fabric"), _version("forge-version", "forge")], "fabric")

    assert page.version_combo.count() == 1
    assert page.version_combo.currentData() == "fabric-version"
    assert "Minecraft 1.21.1" in page.version_combo.currentText()

    page._request_install()

    assert len(emitted) == 1
    assert emitted[0][0].version_id == "fabric-version"
    assert emitted[0][1] == "fabric"
    assert emitted[0][2] == ("release",)


def test_mods_page_ignores_results_for_another_loader(gui_app):
    page = ModsPage()
    page.loader_combo.setCurrentIndex(page.loader_combo.findData("forge"))

    page.set_search_result(ModrinthSearchResult(projects=(_project(),), total_hits=1, offset=0, limit=25), "fabric")

    assert page.results_table.rowCount() == 0


def test_channel_checkbox_updates_before_deferred_reload(gui_app):
    from PySide6.QtTest import QTest

    page = ModsPage()
    emitted = []
    page.channel_preferences_changed.connect(lambda beta, alpha: emitted.append((beta, alpha)))

    page.include_beta_checkbox.setChecked(True)

    assert page.include_beta_checkbox.isChecked() is True
    assert emitted == []

    QTest.qWait(40)
    gui_app.processEvents()

    assert emitted == [(True, False)]
