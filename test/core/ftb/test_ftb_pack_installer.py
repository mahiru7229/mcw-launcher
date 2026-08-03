from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.ftb.ftb_client import FTBClient
from src.core.ftb.ftb_pack_installer import FTBPackInstaller
from src.core.ftb.ftb_pack_registry import FTBPackRegistry
from src.core.instance.instance_artwork_manager import InstanceArtworkManager
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.version_manager import VersionManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.models.ftb.project import FTBProject
from src.models.ftb.version import FTBFile, FTBTarget, FTBVersion
from src.models.instance.instance import Instance


def ftb_file(file_id: int, name: str, path: str = "mods", *, optional: bool = False, server_only: bool = False) -> FTBFile:
    return FTBFile(
        file_id=file_id,
        name=name,
        path=path,
        version="1.0",
        file_type="mod",
        urls=(f"https://primary.example/{name}", f"https://mirror.example/{name}"),
        sha1=f"{file_id:x}".rjust(40, "0"),
        size=10,
        optional=optional,
        server_only=server_only,
    )


def ftb_version(files: tuple[FTBFile, ...]) -> FTBVersion:
    return FTBVersion(
        project_id=25,
        version_id=101,
        name="1.0.0",
        release_type="release",
        files=files,
        targets=(
            FTBTarget(1, "game", "minecraft", "1.20.1"),
            FTBTarget(2, "modloader", "forge", "47.4.0"),
        ),
        recommended_memory_mb=6144,
    )


def test_select_files_skips_server_and_optional_files() -> None:
    required = ftb_file(1, "required.jar")
    optional = ftb_file(2, "optional.jar", optional=True)
    server = ftb_file(3, "server.jar", server_only=True)

    selected, skipped_optional, skipped_server = FTBPackInstaller._select_files(ftb_version((required, optional, server)), False)

    assert selected == (required,)
    assert skipped_optional == 1
    assert skipped_server == 1


def test_select_files_rejects_unsafe_and_duplicate_destinations() -> None:
    with pytest.raises(RuntimeError, match="Unsafe path"):
        FTBPackInstaller._select_files(ftb_version((ftb_file(1, "evil.jar", "../mods"),)), True)

    with pytest.raises(RuntimeError, match="same destination"):
        FTBPackInstaller._select_files(ftb_version((ftb_file(1, "same.jar"), ftb_file(2, "same.jar"))), True)

    with pytest.raises(RuntimeError, match="Unsafe path"):
        FTBPackInstaller._select_files(ftb_version((ftb_file(1, "../evil.jar"),)), True)


def test_download_uses_primary_and_mirror_with_hash_verification(monkeypatch, tmp_path: Path) -> None:
    requests = []
    file = ftb_file(1, "example.jar")

    def download(request, **_kwargs):
        requests.append(request)
        request.destination.parent.mkdir(parents=True, exist_ok=True)
        request.destination.write_bytes(b"file")
        return SimpleNamespace(path=request.destination)

    monkeypatch.setattr("src.core.ftb.ftb_pack_installer.artifact_download_service.download", download)

    FTBPackInstaller._download_files(25, 101, (file,), tmp_path, None)

    assert len(requests) == 1
    request = requests[0]
    assert request.urls == file.urls
    assert request.hashes == {"sha1": file.sha1}
    assert request.destination == tmp_path / "mods" / "example.jar"
    assert request.provider == "ftb"


def test_install_creates_registry_and_rolls_back_on_post_create_failure(monkeypatch, tmp_path: Path) -> None:
    project = FTBProject(project_id=25, name="FTB Example", icon_url="https://cdn.example/icon.png")
    version = ftb_version((ftb_file(1, "example.jar"),))
    created = Instance("id", "FTB Example", "1.20.1", tmp_path / "instance", ("forge", "47.4.0"))
    deleted: list[str] = []
    saved: list[dict] = []

    monkeypatch.setattr(FTBClient, "get_project", staticmethod(lambda _project_id: project))
    monkeypatch.setattr(FTBClient, "get_version", staticmethod(lambda _project_id, _version_id: version))
    monkeypatch.setattr(InstanceManager, "is_instance_exist", staticmethod(lambda _name: False))
    monkeypatch.setattr(VersionManager, "load", staticmethod(lambda version_id: SimpleNamespace(id=version_id)))
    monkeypatch.setattr(ModLoaderManager, "resolve", staticmethod(lambda *_args: ("forge", "47.4.0")))
    monkeypatch.setattr(ModLoaderManager, "prepare", staticmethod(lambda *_args, **_kwargs: None))
    def create_instance(**kwargs):
        instance = Instance("id", kwargs["name"], "1.20.1", tmp_path / kwargs["name"], ("forge", "47.4.0"))
        instance.instance_dir.mkdir(parents=True, exist_ok=True)
        return instance

    monkeypatch.setattr(InstanceManager, "create", staticmethod(create_instance))
    monkeypatch.setattr(InstanceManager, "delete_instance", staticmethod(lambda name: deleted.append(name) or True))
    monkeypatch.setattr(InstanceManager, "load", staticmethod(lambda _name: created))
    monkeypatch.setattr(InstanceArtworkManager, "apply_provider_artwork", staticmethod(lambda *_args, **_kwargs: False))

    def download_files(_project_id, _version_id, _files, staging, _reporter):
        path = staging / "mods" / "example.jar"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"mod")

    monkeypatch.setattr(FTBPackInstaller, "_download_files", staticmethod(download_files))
    monkeypatch.setattr(FTBPackRegistry, "save", staticmethod(lambda _instance, data: saved.append(data)))
    monkeypatch.setattr("src.core.ftb.ftb_pack_installer.Paths.ftb_root", staticmethod(lambda: tmp_path / "ftb"))

    result = FTBPackInstaller.install(25, 101, "FTB Example")

    assert result.instance.name == "FTB Example"
    assert (result.instance.instance_dir / "mods" / "example.jar").read_bytes() == b"mod"
    assert saved[0]["projectId"] == 25
    assert saved[0]["managedFiles"][0]["urls"] == list(version.files[0].urls)
    assert deleted == []

    monkeypatch.setattr(FTBPackRegistry, "save", staticmethod(lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("registry failed"))))
    with pytest.raises(OSError, match="registry failed"):
        FTBPackInstaller.install(25, 101, "FTB Example 2")
    assert deleted[-1] == "FTB Example 2"
