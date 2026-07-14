from pathlib import Path
import json
import zipfile

from src.core.fs.paths import Paths
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.modrinth.modrinth_client import ModrinthClient
from src.core.modrinth.modrinth_downloader import ModrinthDownloader
from src.core.modrinth.modrinth_mod_installer import ModrinthModInstaller
from src.models.instance.instance import Instance
from src.models.modrinth.project import ModrinthProject
from src.models.modrinth.version import ModrinthDependency, ModrinthFile, ModrinthVersion


def make_version(version_id: str, project_id: str, filename: str, dependencies=()) -> ModrinthVersion:
    return ModrinthVersion(version_id=version_id, project_id=project_id, name=version_id, version_number=version_id, version_type="release", game_versions=("1.20.1",), loaders=("fabric",), files=(ModrinthFile(url=f"https://cdn.modrinth.com/{filename}", filename=filename, sha1="a", sha512="b", size=1, primary=True),), dependencies=tuple(dependencies), featured=True)


def write_fabric_mod(path: Path, mod_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("fabric.mod.json", json.dumps({"schemaVersion": 1, "id": mod_id, "name": mod_id.title(), "version": "1.0.0", "environment": "client"}))


def test_installs_required_dependencies_and_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(Paths, "CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(InstanceRunLock, "is_active", lambda instance: False)
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    instance = Instance(instance_id="id", name="Fabric", version_id="1.20.1", instance_dir=instance_dir, mod_loader=("fabric", "0.16.0"))

    dependency = make_version("dep-version", "dep-project", "dependency.jar")
    root = make_version("root-version", "root-project", "root.jar", dependencies=(ModrinthDependency(dependency_type="required", project_id="dep-project"),))
    projects = {
        "root-project": ModrinthProject(project_id="root-project", slug="root", title="Root Mod", description="", project_type="mod", client_side="required"),
        "dep-project": ModrinthProject(project_id="dep-project", slug="dep", title="Dependency", description="", project_type="mod", client_side="required"),
    }

    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: root)
    monkeypatch.setattr(ModrinthClient, "select_version", lambda project_id, game_version, loader="fabric", version_types=None: dependency)
    monkeypatch.setattr(ModrinthClient, "get_project", lambda project_id: projects[project_id])

    def fake_download(file, destination, force=False):
        mod_id = "dependency" if file.filename.startswith("dependency") else "root"
        write_fabric_mod(destination, mod_id)
        return destination

    monkeypatch.setattr(ModrinthDownloader, "download_file", fake_download)

    result = ModrinthModInstaller.install(instance, "root-version")

    assert result.installed_projects == ("Dependency", "Root Mod")
    assert (instance_dir / "mods" / "dependency.jar").is_file()
    assert (instance_dir / "mods" / "root.jar").is_file()
    registry = json.loads((instance_dir / ".mcw" / "modrinth.json").read_text(encoding="utf-8"))
    assert set(registry["mods"]) == {"dep-project", "root-project"}


def test_required_dependency_respects_enabled_release_channels(tmp_path, monkeypatch):
    monkeypatch.setattr(Paths, "CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(InstanceRunLock, "is_active", lambda instance: False)
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    instance = Instance(instance_id="id", name="Fabric", version_id="1.20.1", instance_dir=instance_dir, mod_loader=("fabric", "0.16.0"))

    alpha_dependency = ModrinthVersion(version_id="dep-alpha", project_id="dep-project", name="Alpha", version_number="1.0-alpha", version_type="alpha", game_versions=("1.20.1",), loaders=("fabric",), files=(ModrinthFile(url="https://cdn.modrinth.com/dependency.jar", filename="dependency.jar", sha1="a", sha512="b", size=1, primary=True),), dependencies=(), featured=False)
    root = make_version("root-version", "root-project", "root.jar", dependencies=(ModrinthDependency(dependency_type="required", version_id="dep-alpha", project_id="dep-project"),))
    projects = {
        "root-project": ModrinthProject(project_id="root-project", slug="root", title="Root Mod", description="", project_type="mod", client_side="required"),
        "dep-project": ModrinthProject(project_id="dep-project", slug="dep", title="Dependency", description="", project_type="mod", client_side="required"),
    }

    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: root if version_id == "root-version" else alpha_dependency)
    monkeypatch.setattr(ModrinthClient, "get_project", lambda project_id: projects[project_id])

    import pytest
    with pytest.raises(RuntimeError, match="disabled alpha channel"):
        ModrinthModInstaller.install(instance, "root-version", allowed_version_types=("release",))
