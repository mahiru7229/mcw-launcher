from pathlib import Path

from src.core.fs.paths import Paths
from src.core.modloader.forge.forge_version_manager import ForgeVersionManager
from src.models.minecraft.version import Version


def make_version(tmp_path: Path) -> Version:
    raw = {
        "id": "1.20.1",
        "arguments": {"game": ["--demo"], "jvm": ["-Dbase=true"]},
        "libraries": [{"name": "com.example:base:1.0"}],
        "downloads": {"client": {"url": "https://example/client.jar", "sha1": "a" * 40, "size": 1}},
        "assetIndex": {"id": "1.20", "url": "https://example/assets.json", "sha1": "b" * 40, "size": 1},
        "assets": "1.20",
        "mainClass": "net.minecraft.client.main.Main",
        "javaVersion": {"majorVersion": 17},
    }
    return Version(
        id="1.20.1",
        arguments=raw["arguments"],
        minecraft_arguments=None,
        libraries=raw["libraries"],
        downloads=raw["downloads"],
        asset_index=raw["assetIndex"],
        assets=raw["assets"],
        main_class=raw["mainClass"],
        java_version=raw["javaVersion"],
        raw_json=raw,
        path=tmp_path / "1.20.1.json",
        type="release",
    )


def test_merge_profiles_keeps_base_and_adds_forge() -> None:
    base = make_version(Path(".")).raw_json
    profile = {
        "mainClass": "cpw.mods.bootstraplauncher.BootstrapLauncher",
        "arguments": {"game": ["--fml.forgeVersion", "47.3.0"], "jvm": ["-Dforge=true"]},
        "libraries": [{"name": "net.minecraftforge:forge:1.20.1-47.3.0"}],
    }

    merged = ForgeVersionManager._merge_profiles(base, profile, "1.20.1", "47.3.0")

    assert merged["mainClass"] == profile["mainClass"]
    assert merged["inheritsFrom"] == "1.20.1"
    assert len(merged["libraries"]) == 2
    assert merged["arguments"]["game"][-2:] == ["--fml.forgeVersion", "47.3.0"]
    assert merged["forge"]["loaderVersion"] == "47.3.0"


def test_prepare_staging_writes_launcher_layout(monkeypatch, tmp_path: Path) -> None:
    version = make_version(tmp_path)
    cached_client = tmp_path / "cache" / "1.20.1.jar"
    cached_client.parent.mkdir()
    cached_client.write_bytes(b"client")
    monkeypatch.setattr(Paths, "client", staticmethod(lambda current: cached_client))

    staging = tmp_path / "staging"
    staging.mkdir()
    ForgeVersionManager._prepare_staging(version, staging)

    assert (staging / "launcher_profiles.json").is_file()
    assert (staging / "versions" / "1.20.1" / "1.20.1.json").is_file()
    assert (staging / "versions" / "1.20.1" / "1.20.1.jar").read_bytes() == b"client"


def test_run_installer_imports_legacy_without_starting_java(monkeypatch, tmp_path: Path) -> None:
    import hashlib
    import json
    import zipfile

    installer = tmp_path / "forge-installer.jar"
    library = b"legacy-forge"
    coordinate = "net.minecraftforge:forge:1.8.9-11.15.1.2318-1.8.9:universal"
    profile_id = "1.8.9-Forge11.15.1.2318-1.8.9"
    profile = {
        "install": {"target": profile_id, "path": coordinate},
        "versionInfo": {
            "id": profile_id,
            "mainClass": "net.minecraft.launchwrapper.Launch",
            "libraries": [{"name": coordinate, "checksums": [hashlib.sha1(library, usedforsecurity=False).hexdigest()]}],
        },
    }
    with zipfile.ZipFile(installer, "w") as archive:
        archive.writestr("install_profile.json", json.dumps(profile))
        archive.writestr("forge-1.8.9-11.15.1.2318-1.8.9-universal.jar", library)

    forge_root = tmp_path / "forge-root"
    monkeypatch.setattr(Paths, "forge_root", staticmethod(lambda: forge_root))
    monkeypatch.setattr("src.core.modloader.forge.forge_version_manager.JavaResolver.resolve", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Java must not run for a legacy profile")))
    monkeypatch.setattr("src.core.modloader.forge.forge_version_manager.subprocess.run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess must not run for a legacy profile")))

    ForgeVersionManager._run_installer(make_version(tmp_path), "11.15.1.2318-1.8.9", installer, tmp_path / "staging", None)

    assert (tmp_path / "staging" / "versions" / profile_id / f"{profile_id}.json").is_file()
    assert "Legacy Forge installer imported" in (forge_root / "logs" / "forge-1.20.1-11.15.1.2318-1.8.9.log").read_text(encoding="utf-8")


def test_normalize_legacy_library_builds_download_metadata(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "libraries"
    monkeypatch.setattr(Paths, "libraries", staticmethod(lambda: root))
    sha1 = "a" * 40
    profile = {
        "libraries": [
            {
                "name": "com.example:legacy:1.0",
                "url": "https://repo.example/maven/",
                "checksums": [sha1],
            }
        ]
    }

    normalized = ForgeVersionManager._normalize_libraries(profile)
    artifact = normalized["libraries"][0]["downloads"]["artifact"]

    assert artifact["path"] == "com/example/legacy/1.0/legacy-1.0.jar"
    assert artifact["url"] == "https://repo.example/maven/com/example/legacy/1.0/legacy-1.0.jar"
    assert artifact["sha1"] == sha1
    assert artifact["size"] == 0


def test_detects_unsupported_install_client_error() -> None:
    output = "joptsimple.UnrecognizedOptionException: 'installClient' is not a recognized option"

    assert ForgeVersionManager._is_unsupported_install_client(output) is True


def test_repair_restores_previous_profile_when_reinstall_fails(monkeypatch, tmp_path: Path) -> None:
    base = make_version(tmp_path)
    cache = tmp_path / "forge-profile.json"
    previous = b'{"old": true}\n'
    cache.write_bytes(previous)
    forge_root = tmp_path / "forge"
    monkeypatch.setattr(Paths, "forge_version_json", staticmethod(lambda game, loader: cache))
    monkeypatch.setattr(Paths, "forge_root", staticmethod(lambda: forge_root))
    monkeypatch.setattr(ForgeVersionManager, "install", staticmethod(lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("installer failed"))))

    import pytest
    with pytest.raises(RuntimeError, match="installer failed"):
        ForgeVersionManager.repair(base, "47.3.0")

    assert cache.read_bytes() == previous
    assert "previous cached profile was restored" in (forge_root / "logs" / "forge-repair-1.20.1-47.3.0.log").read_text(encoding="utf-8")


def test_validate_installation_checks_profile_and_library_files(monkeypatch, tmp_path: Path) -> None:
    import hashlib

    libraries = tmp_path / "libraries"
    artifact = libraries / "net/minecraftforge/forge/1.20.1-47.3.0/forge-1.20.1-47.3.0.jar"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"forge")
    sha1 = hashlib.sha1(b"forge", usedforsecurity=False).hexdigest()
    monkeypatch.setattr(Paths, "libraries", staticmethod(lambda: libraries))
    raw = make_version(tmp_path).raw_json
    raw = dict(raw)
    raw["id"] = "forge-1.20.1-47.3.0"
    raw["mainClass"] = "cpw.mods.bootstraplauncher.BootstrapLauncher"
    raw["forge"] = {"schemaVersion": 1, "gameVersion": "1.20.1", "loaderVersion": "47.3.0"}
    raw["libraries"] = [
        {
            "name": "net.minecraftforge:forge:1.20.1-47.3.0",
            "downloads": {
                "artifact": {
                    "path": "net/minecraftforge/forge/1.20.1-47.3.0/forge-1.20.1-47.3.0.jar",
                    "sha1": sha1,
                    "size": 5,
                }
            },
        }
    ]
    version = make_version(tmp_path)
    version.raw_json = raw
    version.main_class = raw["mainClass"]

    assert ForgeVersionManager.validate_installation(version, "1.20.1", "47.3.0", verify_files=True) == []

    artifact.write_bytes(b"broken")
    issues = ForgeVersionManager.validate_installation(version, "1.20.1", "47.3.0", verify_files=True)
    assert any("wrong size" in issue or "SHA-1" in issue for issue in issues)


def test_validate_installation_accepts_modern_forge_runtime_components(tmp_path: Path) -> None:
    raw = make_version(tmp_path).raw_json
    raw = dict(raw)
    raw["id"] = "forge-1.20.1-47.4.21"
    raw["mainClass"] = "cpw.mods.bootstraplauncher.BootstrapLauncher"
    raw["forge"] = {"schemaVersion": 1, "gameVersion": "1.20.1", "loaderVersion": "47.4.21"}
    raw["libraries"] = [{"name": "net.minecraftforge:fmlloader:1.20.1-47.4.21"}]
    version = make_version(tmp_path)
    version.raw_json = raw
    version.main_class = raw["mainClass"]

    assert ForgeVersionManager.validate_installation(version, "1.20.1", "47.4.21", verify_files=False) == []


def test_validate_installation_ignores_libraries_for_other_operating_systems(monkeypatch, tmp_path: Path) -> None:
    libraries = tmp_path / "libraries"
    forge_path = libraries / "net/minecraftforge/fmlloader/1.20.1-47.4.21/fmlloader-1.20.1-47.4.21.jar"
    forge_path.parent.mkdir(parents=True)
    forge_path.write_bytes(b"forge-runtime")
    monkeypatch.setattr(Paths, "libraries", staticmethod(lambda: libraries))
    monkeypatch.setattr(
        "src.core.minecraft.library_rule_manager.LibraryRuleManager._get_current_os",
        staticmethod(lambda: "windows"),
    )
    monkeypatch.setattr(
        "src.core.minecraft.library_rule_manager.LibraryRuleManager._get_current_arch",
        staticmethod(lambda: "x64"),
    )

    raw = make_version(tmp_path).raw_json
    raw = dict(raw)
    raw["id"] = "forge-1.20.1-47.4.21"
    raw["mainClass"] = "cpw.mods.bootstraplauncher.BootstrapLauncher"
    raw["forge"] = {"schemaVersion": 1, "gameVersion": "1.20.1", "loaderVersion": "47.4.21"}
    raw["libraries"] = [
        {
            "name": "net.minecraftforge:fmlloader:1.20.1-47.4.21",
            "downloads": {
                "artifact": {
                    "path": "net/minecraftforge/fmlloader/1.20.1-47.4.21/fmlloader-1.20.1-47.4.21.jar",
                    "sha1": "",
                    "size": len(b"forge-runtime"),
                }
            },
        },
        {
            "name": "ca.weblite:java-objc-bridge:1.1",
            "rules": [{"action": "allow", "os": {"name": "osx"}}],
            "downloads": {
                "artifact": {
                    "path": "ca/weblite/java-objc-bridge/1.1/java-objc-bridge-1.1.jar",
                    "sha1": "",
                    "size": 1,
                }
            },
        },
        {
            "name": "org.lwjgl:lwjgl-glfw:3.3.1:natives-linux",
            "rules": [{"action": "allow", "os": {"name": "linux"}}],
            "downloads": {
                "artifact": {
                    "path": "org/lwjgl/lwjgl-glfw/3.3.1/lwjgl-glfw-3.3.1-natives-linux.jar",
                    "sha1": "",
                    "size": 1,
                }
            },
        },
    ]
    version = make_version(tmp_path)
    version.raw_json = raw
    version.main_class = raw["mainClass"]

    assert ForgeVersionManager.validate_installation(version, "1.20.1", "47.4.21", verify_files=True) == []


def test_validate_installation_still_reports_missing_current_os_library(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Paths, "libraries", staticmethod(lambda: tmp_path / "libraries"))
    monkeypatch.setattr(
        "src.core.minecraft.library_rule_manager.LibraryRuleManager._get_current_os",
        staticmethod(lambda: "windows"),
    )
    monkeypatch.setattr(
        "src.core.minecraft.library_rule_manager.LibraryRuleManager._get_current_arch",
        staticmethod(lambda: "x64"),
    )

    raw = make_version(tmp_path).raw_json
    raw = dict(raw)
    raw["id"] = "forge-1.20.1-47.4.21"
    raw["mainClass"] = "cpw.mods.bootstraplauncher.BootstrapLauncher"
    raw["forge"] = {"schemaVersion": 1, "gameVersion": "1.20.1", "loaderVersion": "47.4.21"}
    raw["libraries"] = [
        {"name": "net.minecraftforge:fmlloader:1.20.1-47.4.21"},
        {
            "name": "com.example:windows-only:1.0",
            "rules": [{"action": "allow", "os": {"name": "windows"}}],
            "downloads": {
                "artifact": {
                    "path": "com/example/windows-only/1.0/windows-only-1.0.jar",
                    "sha1": "",
                    "size": 1,
                }
            },
        },
    ]
    version = make_version(tmp_path)
    version.raw_json = raw
    version.main_class = raw["mainClass"]

    issues = ForgeVersionManager.validate_installation(version, "1.20.1", "47.4.21", verify_files=True)

    assert issues == ["Missing required library: com/example/windows-only/1.0/windows-only-1.0.jar"]
