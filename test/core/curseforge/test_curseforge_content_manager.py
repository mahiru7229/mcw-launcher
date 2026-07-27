from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.curseforge.curseforge_content_manager import CurseForgeContentManager
from src.core.curseforge.curseforge_downloader import CurseForgeDownloader
from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.fs.paths import Paths
from src.core.mod.mod_manager import ModManager
from src.models.curseforge.file import CurseForgeFile
from src.models.instance.instance import Instance


def test_download_round_forwards_launch_lock_token_to_managed_mod_install(tmp_path, monkeypatch):
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    instance = Instance(instance_id="id", name="Pack", version_id="1.18.2", instance_dir=instance_dir, mod_loader=("forge", "40.2.0"))
    cache_path = tmp_path / "cache" / "example.jar"
    received = {}
    file = CurseForgeFile(
        file_id=2,
        project_id=1,
        display_name="Example",
        file_name="example.jar",
        release_type="release",
        file_date="",
        file_length=3,
        download_url="https://example.invalid/example.jar",
        sha1="a" * 40,
        game_versions=("1.18.2",),
        dependencies=(),
        loaders=("forge",),
    )

    monkeypatch.setattr(CurseForgeClient, "get_file", staticmethod(lambda *args, **kwargs: file))
    monkeypatch.setattr(Paths, "curseforge_file_cache", staticmethod(lambda *args: cache_path))

    def fake_download(_file, destination, **kwargs):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"jar")
        return destination

    def fake_add_mods(current_instance, source_paths, replace=False, launch_lock_token=None, allow_unverified=False):
        received["instance"] = current_instance
        received["paths"] = list(source_paths)
        received["replace"] = replace
        received["token"] = launch_lock_token
        received["allow_unverified"] = allow_unverified
        return [SimpleNamespace(file_name="example.jar")]

    monkeypatch.setattr(CurseForgeDownloader, "download_file", staticmethod(fake_download))
    monkeypatch.setattr(ModManager, "add_mods", staticmethod(fake_add_mods))

    entry = {
        "projectId": 1,
        "fileId": 2,
        "fileName": "example.jar",
        "path": "mods/example.jar",
        "sha1": "",
        "size": 0,
    }
    missing = [{"kind": "pack", "key": "pack:1:2", "path": "mods/example.jar", "entry": entry}]

    result = CurseForgeContentManager._download_round(instance, missing, None, 1, "owned-token")

    assert result["errors"] == {}
    assert result["downloaded"] == 1
    assert received == {
        "instance": instance,
        "paths": [cache_path],
        "replace": True,
        "token": "owned-token",
        "allow_unverified": True,
    }
    assert entry["pendingDownload"] is False
    assert entry["lastDownloadError"] == ""


def test_manual_download_errors_are_grouped_without_request_ids():
    first = CurseForgeContentManager._normalized_error(
        "This CurseForge file must be downloaded manually because third-party distribution is unavailable. Request ID: abcdefab-1234-1234-1234-abcdefabcdef."
    )
    second = CurseForgeContentManager._normalized_error(
        "This CurseForge file must be downloaded manually because third-party distribution is unavailable. Request ID: 01234567-89ab-cdef-0123-456789abcdef."
    )

    assert first == second
    assert "Manual download is required" in first
    assert "Request ID" not in first


def test_launch_failure_exposes_manual_import_requirements(tmp_path, monkeypatch):
    from src.core.curseforge.curseforge_content_manager import CurseForgeManagedFilesRequired
    from src.core.curseforge.curseforge_pack_registry import CurseForgePackRegistry

    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    instance = Instance(instance_id="id", name="Manual Pack", version_id="1.18.2", instance_dir=instance_dir, mod_loader=("forge", "40.2.0"))
    CurseForgePackRegistry.save(
        instance,
        {
            "managedFiles": [
                {
                    "projectId": 101,
                    "fileId": 202,
                    "fileName": "restricted.jar",
                    "path": "mods/restricted.jar",
                    "displayName": "Restricted Mod",
                    "sha1": "b" * 40,
                    "size": 123,
                    "pendingDownload": True,
                    "lastDownloadError": "This CurseForge file must be downloaded manually because third-party distribution is unavailable.",
                    "retryableDownload": False,
                }
            ]
        },
    )
    project = SimpleNamespace(name="Restricted Mod", project_url="https://www.curseforge.com/minecraft/mc-mods/restricted-mod")
    monkeypatch.setattr(CurseForgeClient, "get_projects_batch", staticmethod(lambda ids: {101: project}))

    with pytest.raises(CurseForgeManagedFilesRequired) as captured:
        CurseForgeContentManager.ensure(instance, block_launch_on_failure=True)

    error = captured.value
    assert error.instance_name == "Manual Pack"
    assert error.instance_dir == instance_dir
    assert len(error.requirements) == 1
    requirement = error.requirements[0]
    assert requirement.managed_kind == "pack"
    assert requirement.managed_path == "mods/restricted.jar"
    assert requirement.project_url == "https://www.curseforge.com/minecraft/mc-mods/restricted-mod/files/202"
    assert requirement.sha1 == "b" * 40
