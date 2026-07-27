from pathlib import PurePosixPath

import pytest

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_pack_installer import CurseForgePackInstaller
from src.models.curseforge.file import CurseForgeFile


def test_parses_primary_forge_loader() -> None:
    manifest = {
        "minecraft": {
            "version": "1.20.1",
            "modLoaders": [
                {"id": "forge-47.3.0", "primary": True},
                {"id": "forge-47.2.0", "primary": False},
            ],
        }
    }

    assert CurseForgePackInstaller._parse_loader(manifest) == ("1.20.1", "47.3.0")


def test_rejects_non_forge_pack() -> None:
    manifest = {"minecraft": {"version": "1.20.1", "modLoaders": [{"id": "fabric-0.16.0", "primary": True}]}}

    with pytest.raises(RuntimeError, match="Only Forge CurseForge modpacks"):
        CurseForgePackInstaller._parse_loader(manifest)


@pytest.mark.parametrize("value", ["../outside", "/absolute", "C:/windows", "folder/../../escape", ""])
def test_rejects_unsafe_override_paths(value: str) -> None:
    with pytest.raises(RuntimeError, match="Unsafe"):
        CurseForgePackInstaller._safe_relative_path(value)


def test_accepts_safe_override_path() -> None:
    assert CurseForgePackInstaller._safe_relative_path("config/example.toml") == PurePosixPath("config/example.toml")


def test_resolve_files_keeps_advisory_loader_metadata(monkeypatch) -> None:
    file = CurseForgeFile(
        file_id=20,
        project_id=10,
        display_name="Universal build labelled as Fabric",
        file_name="universal.jar",
        release_type="release",
        file_date="2026-07-25T00:00:00Z",
        file_length=100,
        download_url="https://example.invalid/universal.jar",
        sha1="a" * 40,
        game_versions=(),
        dependencies=(),
        loaders=("fabric",),
    )
    monkeypatch.setattr(CurseForgeClient, "get_files_batch", staticmethod(lambda ids: {20: file}))

    files, skipped = CurseForgePackInstaller._resolve_files(
        {"files": [{"projectID": 10, "fileID": 20, "required": True}]},
        game_version="1.20.1",
        install_optional_files=True,
        reporter=None,
    )

    assert skipped == 0
    assert files[0]["declaredLoaders"] == ["fabric"]
    assert files[0]["fileName"] == "universal.jar"


def test_manual_modpack_download_becomes_resumable_request(monkeypatch, tmp_path) -> None:
    from types import SimpleNamespace

    from src.core.curseforge.curseforge_downloader import CurseForgeDownloader, CurseForgeManualDownloadRequired
    from src.core.curseforge.curseforge_pack_installer import CurseForgeModpackManualDownloadRequired
    from src.core.fs.paths import Paths
    from src.core.instance.instance_manager import InstanceManager
    from src.models.curseforge.manual_download import CurseForgeManualDownload

    project = SimpleNamespace(name="Restricted Pack", project_url="https://www.curseforge.com/minecraft/modpacks/restricted-pack")
    file = CurseForgeFile(
        file_id=22,
        project_id=11,
        display_name="Restricted Pack 1.0",
        file_name="restricted-pack.zip",
        release_type="release",
        file_date="2026-07-26T00:00:00Z",
        file_length=123,
        download_url="",
        sha1="a" * 40,
        game_versions=("1.18.2",),
        dependencies=(),
        is_available=False,
        loaders=("forge",),
    )
    requirement = CurseForgeManualDownload(
        project_id=11,
        file_id=22,
        project_name="Restricted Pack",
        file_name=file.file_name,
        file_size=file.file_length,
        sha1=file.sha1,
        project_url=project.project_url,
        reason="Manual download required",
    )
    monkeypatch.setattr(InstanceManager, "is_instance_exist", staticmethod(lambda _name: False))
    monkeypatch.setattr(CurseForgeClient, "normalize_release_types", staticmethod(lambda _values: ("release",)))
    monkeypatch.setattr(CurseForgeClient, "get_project", staticmethod(lambda _project_id: project))
    monkeypatch.setattr(CurseForgeClient, "get_file", staticmethod(lambda _project_id, _file_id: file))
    monkeypatch.setattr(Paths, "curseforge_pack_cache", staticmethod(lambda *_args: tmp_path / file.file_name))
    monkeypatch.setattr(CurseForgeDownloader, "download_file", staticmethod(lambda *_args, **_kwargs: (_ for _ in ()).throw(CurseForgeManualDownloadRequired(requirement))))

    with pytest.raises(CurseForgeModpackManualDownloadRequired) as raised:
        CurseForgePackInstaller.install(11, 22, "Restricted Pack", allowed_release_types=("release",))

    request = raised.value
    assert request.instance_name == "Restricted Pack"
    assert request.requirement.managed_kind == "modpack_archive"
    assert request.requirement.project_url.endswith("/files/22")
    assert request.allowed_release_types == ("release",)


def test_manual_modpack_archive_is_verified_cached_and_resumed(monkeypatch, tmp_path) -> None:
    from hashlib import sha1
    from types import SimpleNamespace

    from src.core.curseforge.curseforge_pack_installer import CurseForgeModpackManualDownloadRequired
    from src.core.fs.paths import Paths
    from src.models.curseforge.manual_download import CurseForgeManualDownload

    payload = b"downloaded CurseForge modpack"
    source = tmp_path / "downloaded-pack.zip"
    source.write_bytes(payload)
    project = SimpleNamespace(name="Restricted Pack", project_url="https://www.curseforge.com/minecraft/modpacks/restricted-pack")
    file = CurseForgeFile(
        file_id=22,
        project_id=11,
        display_name="Restricted Pack 1.0",
        file_name="restricted-pack.zip",
        release_type="release",
        file_date="2026-07-26T00:00:00Z",
        file_length=len(payload),
        download_url="",
        sha1=sha1(payload, usedforsecurity=False).hexdigest(),
        game_versions=("1.18.2",),
        dependencies=(),
        is_available=False,
        loaders=("forge",),
    )
    requirement = CurseForgeManualDownload(
        project_id=11,
        file_id=22,
        project_name=project.name,
        file_name=file.file_name,
        file_size=file.file_length,
        sha1=file.sha1,
        project_url=project.project_url + "/files/22",
        reason="Manual download required",
        managed_kind="modpack_archive",
    )
    request = CurseForgeModpackManualDownloadRequired(requirement, 11, 22, "Restricted Pack", True, ("release",))
    cache_path = tmp_path / "cache" / file.file_name
    sentinel = object()
    monkeypatch.setattr(CurseForgePackInstaller, "_prepare_install", staticmethod(lambda *_args, **_kwargs: ("Restricted Pack", ("release",), project, file)))
    monkeypatch.setattr(Paths, "curseforge_pack_cache", staticmethod(lambda *_args: cache_path))
    monkeypatch.setattr(CurseForgePackInstaller, "_install_from_archive", staticmethod(lambda *_args, **_kwargs: sentinel))

    result = CurseForgePackInstaller.install_manual_archive(request, source)

    assert result is sentinel
    assert cache_path.read_bytes() == payload
