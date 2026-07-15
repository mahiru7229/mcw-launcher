import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.gui.dialogs.modrinth_browser_dialog import ModrinthBrowserDialog
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthFile, ModrinthVersion


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_modpack_dialog_sanitizes_instance_name_and_enables_install(app):
    dialog = ModrinthBrowserDialog("modpack")
    project = ModrinthProject(project_id="project", slug="pack", title='Pack: Test/Name', description="Description", project_type="modpack", author="Author")
    result = ModrinthSearchResult(projects=(project,), total_hits=1, offset=0, limit=25)
    version = ModrinthVersion(version_id="version", project_id="project", name="1.0", version_number="1.0", version_type="release", game_versions=("1.20.1",), loaders=("fabric",), files=(ModrinthFile(url="https://cdn.modrinth.com/pack.mrpack", filename="pack.mrpack", sha1="a", sha512="b", size=1, primary=True),))

    dialog.set_search_result(result)
    dialog.set_versions("project", [version])

    assert dialog.instance_name_input.text() == "Pack_ Test_Name"
    assert dialog.install_button.isEnabled()


def test_dialog_filters_versions_by_enabled_channels(app):
    dialog = ModrinthBrowserDialog("modpack")
    project = ModrinthProject(project_id="project", slug="pack", title="Pack", description="Description", project_type="modpack", author="Author")
    result = ModrinthSearchResult(projects=(project,), total_hits=1, offset=0, limit=25)

    def version(version_id: str, version_type: str) -> ModrinthVersion:
        return ModrinthVersion(version_id=version_id, project_id="project", name=version_id, version_number=version_id, version_type=version_type, game_versions=("1.20.1",), loaders=("fabric",), files=(ModrinthFile(url=f"https://cdn.modrinth.com/{version_id}.mrpack", filename=f"{version_id}.mrpack", sha1="a", sha512="b", size=1, primary=True),))

    dialog.set_search_result(result)
    dialog.set_versions("project", [version("release", "release"), version("beta", "beta"), version("alpha", "alpha")])

    assert dialog.allowed_version_types == ("release",)
    assert dialog.version_combo.count() == 1

    dialog.set_channel_preferences(include_beta=True, include_alpha=False)
    assert dialog.allowed_version_types == ("release", "beta")
    assert dialog.version_combo.count() == 2

    dialog.set_channel_preferences(include_beta=True, include_alpha=True)
    assert dialog.allowed_version_types == ("release", "beta", "alpha")
    assert dialog.version_combo.count() == 3
    assert "Beta: 1" in dialog.release_channel_label.text()
    assert "Alpha: 1" in dialog.release_channel_label.text()


def test_search_result_auto_selects_first_project_and_requests_versions(app):
    dialog = ModrinthBrowserDialog("modpack")
    requested: list[tuple[str, str, str]] = []
    dialog.versions_requested.connect(lambda project_type, project_id, game_version: requested.append((project_type, project_id, game_version)))

    first = ModrinthProject(project_id="first-project", slug="first", title="First Pack", description="First", project_type="modpack", author="Author")
    second = ModrinthProject(project_id="second-project", slug="second", title="Second Pack", description="Second", project_type="modpack", author="Author")

    dialog.set_search_result(ModrinthSearchResult(projects=(first,), total_hits=1, offset=0, limit=25))
    assert requested == [("modpack", "first-project", "")]
    assert dialog.instance_name_input.text() == "First Pack"
    assert "First Pack" in dialog.details_label.text()

    dialog.set_search_result(ModrinthSearchResult(projects=(second,), total_hits=1, offset=0, limit=25))
    assert requested == [("modpack", "first-project", ""), ("modpack", "second-project", "")]
    assert dialog.instance_name_input.text() == "Second Pack"
    assert "Second Pack" in dialog.details_label.text()


def test_empty_search_result_clears_auto_selected_project_state(app):
    dialog = ModrinthBrowserDialog("modpack")
    project = ModrinthProject(project_id="project", slug="pack", title="Temporary Pack", description="Description", project_type="modpack", author="Author")
    version = ModrinthVersion(version_id="version", project_id="project", name="1.0", version_number="1.0", version_type="release", game_versions=("1.20.1",), loaders=("fabric",), files=(ModrinthFile(url="https://cdn.modrinth.com/pack.mrpack", filename="pack.mrpack", sha1="a", sha512="b", size=1, primary=True),))

    dialog.set_search_result(ModrinthSearchResult(projects=(project,), total_hits=1, offset=0, limit=25))
    dialog.set_versions("project", [version])
    assert dialog.version_combo.count() == 1
    assert dialog.instance_name_input.text() == "Temporary Pack"

    dialog.set_search_result(ModrinthSearchResult(projects=(), total_hits=0, offset=0, limit=25))
    assert dialog.version_combo.count() == 0
    assert dialog.instance_name_input.text() == ""
    assert not dialog.install_button.isEnabled()
