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
