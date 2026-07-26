from pathlib import Path
from types import SimpleNamespace
import hashlib
import json

import pytest

from src.core.curseforge.curseforge_pack_registry import CurseForgePackRegistry
from src.core.fs.paths import Paths
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.instance.settings_manager import SettingsManager
from src.core.java.java_selector import JavaSelector
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.core.modrinth.modrinth_pack_registry import ModrinthPackRegistry
from src.core.repair.repair_service import RepairService
from src.models.repair.repair_models import RepairComponent, RepairMode, RepairStatus


@pytest.fixture
def repair_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = tmp_path / "instance"
    root.mkdir()
    instance = SimpleNamespace(instance_id="repair-id", name="Repair", version_id="1.20.1", instance_dir=root, mod_loader=("vanilla", "-1"))

    client_bytes = b"client"
    library_bytes = b"library"
    asset_bytes = b"asset"
    index_bytes = json.dumps({"objects": {"minecraft/test": {"hash": hashlib.sha1(asset_bytes, usedforsecurity=False).hexdigest(), "size": len(asset_bytes)}}}).encode()
    client_sha1 = hashlib.sha1(client_bytes, usedforsecurity=False).hexdigest()
    library_sha1 = hashlib.sha1(library_bytes, usedforsecurity=False).hexdigest()
    index_sha1 = hashlib.sha1(index_bytes, usedforsecurity=False).hexdigest()
    asset_sha1 = hashlib.sha1(asset_bytes, usedforsecurity=False).hexdigest()

    version_path = tmp_path / "version.json"
    raw = {
        "id": "1.20.1",
        "downloads": {"client": {"url": "https://example/client", "sha1": client_sha1, "size": len(client_bytes)}},
        "libraries": [{"downloads": {"artifact": {"url": "https://example/library", "sha1": library_sha1, "size": len(library_bytes), "path": "group/library.jar"}}}],
        "assetIndex": {"url": "https://example/index", "sha1": index_sha1, "size": len(index_bytes), "id": "1.20"},
        "assets": "1.20",
        "mainClass": "net.minecraft.client.main.Main",
        "javaVersion": {"majorVersion": 17},
        "type": "release",
    }
    version_path.write_text(json.dumps(raw), encoding="utf-8")
    version = VersionManager._parse_version(raw, version_path)
    assert version is not None

    client_path = tmp_path / "cache" / "client.jar"
    libraries_root = tmp_path / "cache" / "libraries"
    index_path = tmp_path / "cache" / "assets" / "indexes" / "1.20.json"
    asset_path = tmp_path / "cache" / "assets" / "objects" / asset_sha1[:2] / asset_sha1
    settings_path = root / "settings.json"
    settings_path.write_text(json.dumps(SettingsManager.DEFAULT_SETTINGS), encoding="utf-8")
    (root / "instance.json").write_text(json.dumps({"name": "Repair", "version_id": "1.20.1"}), encoding="utf-8")

    monkeypatch.setattr(InstanceRunLock, "is_active", classmethod(lambda cls, received: False))
    monkeypatch.setattr(VersionManifestManager, "get", staticmethod(lambda: []))
    monkeypatch.setattr(VersionManager, "load", staticmethod(lambda version_id: version))
    monkeypatch.setattr(JavaSelector, "select_java", staticmethod(lambda major: Path("C:/Java17/javaw.exe")))
    monkeypatch.setattr(ModrinthPackRegistry, "load", staticmethod(lambda received: {}))
    monkeypatch.setattr(CurseForgePackRegistry, "load", staticmethod(lambda received: {}))
    monkeypatch.setattr(SettingsManager, "load", staticmethod(lambda received: SimpleNamespace(lan_auth_mode="microsoft_only")))
    monkeypatch.setattr(Paths, "client", staticmethod(lambda received: client_path))
    monkeypatch.setattr(Paths, "libraries", staticmethod(lambda: libraries_root))
    monkeypatch.setattr(Paths, "asset_index", staticmethod(lambda received: index_path))
    monkeypatch.setattr(Paths, "asset_object", staticmethod(lambda asset: asset_path))
    monkeypatch.setattr(Paths, "instance_settings_path", staticmethod(lambda received: settings_path))
    monkeypatch.setattr(Paths, "instance_repair_cache", staticmethod(lambda received: root / ".mcw" / "repair-cache.json"))
    monkeypatch.setattr(Paths, "instance_repair_scan_report", staticmethod(lambda received: root / ".mcw" / "repair-scan.json"))
    monkeypatch.setattr(Paths, "instance_repair_execution_report", staticmethod(lambda received: root / ".mcw" / "repair-result.json"))

    return SimpleNamespace(
        instance=instance,
        version=version,
        client_path=client_path,
        library_path=libraries_root / "group" / "library.jar",
        index_path=index_path,
        asset_path=asset_path,
        client_bytes=client_bytes,
        library_bytes=library_bytes,
        index_bytes=index_bytes,
        asset_bytes=asset_bytes,
    )


def test_full_scan_detects_missing_files_and_then_reports_healthy(repair_fixture) -> None:
    fixture = repair_fixture
    components = (RepairComponent.CLIENT, RepairComponent.LIBRARIES, RepairComponent.ASSETS, RepairComponent.JAVA, RepairComponent.MOD_LOADER, RepairComponent.MODPACK, RepairComponent.SETTINGS)

    missing = RepairService.scan(fixture.instance, RepairMode.FULL, components)
    assert missing.component(RepairComponent.CLIENT).status is RepairStatus.BROKEN
    assert missing.component(RepairComponent.LIBRARIES).status is RepairStatus.BROKEN
    assert missing.component(RepairComponent.ASSETS).status is RepairStatus.BROKEN
    plan = RepairService.build_plan(missing)
    assert plan.can_repair
    assert plan.estimated_download_bytes > 0

    fixture.client_path.parent.mkdir(parents=True)
    fixture.client_path.write_bytes(fixture.client_bytes)
    fixture.library_path.parent.mkdir(parents=True)
    fixture.library_path.write_bytes(fixture.library_bytes)
    fixture.index_path.parent.mkdir(parents=True)
    fixture.index_path.write_bytes(fixture.index_bytes)
    fixture.asset_path.parent.mkdir(parents=True)
    fixture.asset_path.write_bytes(fixture.asset_bytes)

    healthy = RepairService.scan(fixture.instance, RepairMode.FULL, components)
    assert healthy.healthy
    assert healthy.component(RepairComponent.CLIENT).status is RepairStatus.HEALTHY
    assert healthy.component(RepairComponent.LIBRARIES).status is RepairStatus.HEALTHY
    assert healthy.component(RepairComponent.ASSETS).status is RepairStatus.HEALTHY
    assert healthy.hashed_files >= 4


def test_quick_scan_reuses_full_verification_cache(repair_fixture) -> None:
    fixture = repair_fixture
    fixture.client_path.parent.mkdir(parents=True)
    fixture.client_path.write_bytes(fixture.client_bytes)
    components = (RepairComponent.CLIENT,)

    full = RepairService.scan(fixture.instance, RepairMode.FULL, components)
    quick = RepairService.scan(fixture.instance, RepairMode.QUICK, components)

    assert full.hashed_files == 1
    assert quick.hashed_files == 0
    assert quick.cache_hits == 1


def test_scan_is_blocked_while_game_runs(monkeypatch: pytest.MonkeyPatch, repair_fixture) -> None:
    monkeypatch.setattr(InstanceRunLock, "is_active", classmethod(lambda cls, received: True))
    with pytest.raises(RuntimeError, match="Close Minecraft"):
        RepairService.scan(repair_fixture.instance)
