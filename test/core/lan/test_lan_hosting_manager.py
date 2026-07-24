from pathlib import Path

import pytest

from src.core.lan.lan_hosting_manager import LanHostingManager
from src.core.modrinth.modrinth_client import ModrinthClient
from src.core.modrinth.modrinth_mod_installer import ModrinthModInstaller
from src.core.modrinth.modrinth_registry import ModrinthRegistry
from src.models.instance.instance import Instance
from src.models.modrinth.install_result import ModrinthModInstallResult
from src.models.modrinth.version import ModrinthFile, ModrinthVersion


def make_instance(tmp_path: Path, loader: str = "fabric") -> Instance:
    instance_dir = tmp_path / loader
    (instance_dir / "mods").mkdir(parents=True)
    return Instance(instance_id=loader, name=loader.title(), version_id="1.20.1", instance_dir=instance_dir, mod_loader=(loader, "test"))


def make_version(slug: str, loader: str) -> ModrinthVersion:
    return ModrinthVersion(
        version_id=f"{slug}-version",
        project_id=f"{slug}-project",
        name="1.0",
        version_number="1.0",
        version_type="release",
        game_versions=("1.20.1",),
        loaders=(loader,),
        files=(ModrinthFile(url="https://example.invalid/mod.jar", filename=f"{slug}.jar", sha1="a", sha512="b", size=1, primary=True),),
    )


def test_plan_separates_authentication_from_connection(tmp_path: Path) -> None:
    instance = make_instance(tmp_path)

    manual_friends = LanHostingManager.plan(instance, "friends", "manual")
    microsoft_e4mc = LanHostingManager.plan(instance, "microsoft_only", "e4mc")
    full = LanHostingManager.plan(instance, "friends", "e4mc")

    assert [component.project_slug for component in manual_friends.components] == ["lan-properties"]
    assert [component.project_slug for component in microsoft_e4mc.components] == ["e4mc"]
    assert [component.project_slug for component in full.components] == ["lan-properties", "e4mc"]


def test_plain_manual_microsoft_profile_does_not_require_a_mod_loader(tmp_path: Path) -> None:
    instance = make_instance(tmp_path, "vanilla")

    plan = LanHostingManager.plan(instance, "microsoft_only", "manual")

    assert plan.components == ()


def test_mod_based_profile_requires_fabric_or_forge(tmp_path: Path) -> None:
    instance = make_instance(tmp_path, "vanilla")

    with pytest.raises(RuntimeError, match="Fabric or Forge"):
        LanHostingManager.plan(instance, "friends", "manual")


def test_prepare_installs_release_components_and_marks_registry(tmp_path: Path, monkeypatch) -> None:
    instance = make_instance(tmp_path, "forge")
    registry = {"schemaVersion": 2, "mods": {}}
    selected: list[tuple[str, str, str, tuple[str, ...]]] = []

    def select_version(project_id: str, game_version: str, loader: str, version_types: tuple[str, ...]):
        selected.append((project_id, game_version, loader, version_types))
        return make_version(project_id, loader)

    def install(_instance, version_id: str, install_dependencies: bool, allowed_version_types: tuple[str, ...], reporter=None):
        slug = version_id.removesuffix("-version")
        project_id = f"{slug}-project"
        registry["mods"][project_id] = {
            "projectId": project_id,
            "versionId": version_id,
            "versionNumber": "1.0",
            "fileName": f"{slug}.jar",
            "title": "LAN Properties" if slug == "lan-properties" else "e4mc",
        }
        return ModrinthModInstallResult(installed_projects=(registry["mods"][project_id]["title"],), installed_files=(f"{slug}.jar",))

    monkeypatch.setattr(ModrinthClient, "select_version", staticmethod(select_version))
    monkeypatch.setattr(ModrinthModInstaller, "install", staticmethod(install))
    monkeypatch.setattr(ModrinthRegistry, "load", staticmethod(lambda _instance: registry))
    monkeypatch.setattr(ModrinthRegistry, "save", staticmethod(lambda _instance, _data: None))
    monkeypatch.setattr(LanHostingManager, "_entry_matches_installed_file", staticmethod(lambda *_args: False))
    monkeypatch.setattr(LanHostingManager, "_disable_unused_managed_components", staticmethod(lambda *_args: ()))

    result = LanHostingManager.prepare(instance, "friends", "e4mc")

    assert selected == [
        ("lan-properties", "1.20.1", "forge", ("release",)),
        ("e4mc", "1.20.1", "forge", ("release",)),
    ]
    assert result.installed_projects == ("LAN Properties", "e4mc")
    assert registry["mods"]["lan-properties-project"]["managedBy"] == LanHostingManager.MANAGED_BY
    assert registry["mods"]["lan-properties-project"]["lanHostingRole"] == LanHostingManager.ROLE_AUTH_BRIDGE
    assert registry["mods"]["e4mc-project"]["lanHostingRole"] == LanHostingManager.ROLE_CONNECTION
