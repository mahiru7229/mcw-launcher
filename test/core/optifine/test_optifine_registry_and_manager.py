from pathlib import Path
import json
import zipfile

import pytest

from src.core.fs.paths import Paths
from src.core.optifine.optifine_manager import OptiFineManager
from src.core.optifine.optifine_registry import OptiFineRegistry
from src.models.instance.instance import Instance
from src.models.minecraft.version import Version
from src.models.optifine.optifine_models import OptiFineVersion


def _instance(root: Path, loader: str = "forge") -> Instance:
    directory = root / "instances" / "Demo"
    directory.mkdir(parents=True)
    return Instance("id", "Demo", "1.12.2", directory, (loader, "14.23.5.2860" if loader == "forge" else "-1"))


def _jar(path: Path) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nMain-Class: optifine.Installer\n")
        archive.writestr("optifine/Installer.class", b"class")
    return path


def _selected() -> OptiFineVersion:
    return OptiFineVersion("1.12.2", "HD_U", "G5", "OptiFine_1.12.2_HD_U_G5.jar")


def test_forge_mode_installs_records_and_uninstalls(tmp_path: Path) -> None:
    previous = Paths.configure(tmp_path)
    try:
        instance = _instance(tmp_path)
        source = _jar(tmp_path / _selected().filename)
        result = OptiFineManager.install(instance, _selected(), source)
        assert result.mode == "forge_mod"
        assert result.installed_path.is_file()
        state = OptiFineRegistry.state(instance)
        assert state.installed and state.managed
        provenance = json.loads((instance.instance_dir / ".mcw" / "mod-provenance.json").read_text(encoding="utf-8"))
        entry = next(iter(provenance["mods"].values()))
        assert entry["provider"] == "optifine"
        assert entry["redistributionAllowed"] is False
        assert OptiFineManager.uninstall(instance) is True
        assert not result.installed_path.exists()
    finally:
        Paths.restore(previous)


def test_manager_rejects_optifine_mod_on_fabric(tmp_path: Path) -> None:
    previous = Paths.configure(tmp_path)
    try:
        instance = _instance(tmp_path, "fabric")
        source = _jar(tmp_path / _selected().filename)
        with pytest.raises(RuntimeError, match="Forge"):
            OptiFineManager.install(instance, _selected(), source)
    finally:
        Paths.restore(previous)


def test_apply_standalone_profile(tmp_path: Path) -> None:
    previous = Paths.configure(tmp_path)
    try:
        instance = _instance(tmp_path, "vanilla")
        profile = {
            "id": "optifine-1.12.2_HD_U_G5",
            "type": "release",
            "arguments": {"game": [], "jvm": []},
            "libraries": [],
            "downloads": {"client": {"url": "https://example.invalid/client.jar", "sha1": "a" * 40, "size": 1}},
            "assetIndex": {"id": "1.12", "url": "https://example.invalid/assets.json", "sha1": "b" * 40, "size": 1, "totalSize": 1},
            "assets": "1.12",
            "mainClass": "net.minecraft.launchwrapper.Launch",
            "javaVersion": {"majorVersion": 8},
            "optifine": {"mode": "standalone"},
        }
        path = Paths.optifine_profile(instance)
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(profile), encoding="utf-8")
        OptiFineRegistry.save(instance, {"installed": True, "mode": "standalone", "managed": True, "minecraftVersion": "1.12.2", "versionId": "1.12.2_HD_U_G5", "profilePath": str(path)})
        base = Version("1.12.2", tmp_path / "base.json", [], {}, {}, "1.12", "net.minecraft.client.main.Main", {"majorVersion": 8}, {}, "release", {}, None)
        selected = OptiFineManager.apply_to_version(instance, base)
        assert selected.main_class == "net.minecraft.launchwrapper.Launch"
    finally:
        Paths.restore(previous)


def test_compatibility_blocks_forge_na_and_warns_on_different_forge(tmp_path: Path) -> None:
    previous = Paths.configure(tmp_path)
    try:
        instance = _instance(tmp_path)
        unavailable = OptiFineVersion("1.12.2", "HD_U", "C5", "OptiFine_1.12.2_HD_U_C5.jar", forge_version="N/A")
        assert OptiFineManager.compatibility(instance, unavailable).state == "blocked"
        declared = OptiFineVersion("1.12.2", "HD_U", "G5", "OptiFine_1.12.2_HD_U_G5.jar", forge_version="2847")
        assert OptiFineManager.compatibility(instance, declared).state == "warning"
    finally:
        Paths.restore(previous)


def test_compatibility_accepts_matching_legacy_forge_build(tmp_path: Path) -> None:
    previous = Paths.configure(tmp_path)
    try:
        instance = _instance(tmp_path)
        instance.mod_loader = ("forge", "14.23.5.2847")
        selected = OptiFineVersion("1.12.2", "HD_U", "G5", "OptiFine_1.12.2_HD_U_G5.jar", forge_version="2847")
        assert OptiFineManager.compatibility(instance, selected).state == "compatible"
    finally:
        Paths.restore(previous)


def test_install_rolls_back_when_registry_commit_fails(tmp_path: Path, monkeypatch) -> None:
    previous_paths = Paths.configure(tmp_path)
    try:
        instance = _instance(tmp_path)
        first = _selected()
        first_source = _jar(tmp_path / first.filename)
        first_result = OptiFineManager.install(instance, first, first_source)
        first_bytes = first_result.installed_path.read_bytes()
        second = OptiFineVersion("1.12.2", "HD_U", "G6", "OptiFine_1.12.2_HD_U_G6.jar")
        second_source = _jar(tmp_path / second.filename)
        original_save = OptiFineRegistry.save

        def fail_for_second(target_instance, payload):
            if payload.get("versionId") == second.version_id:
                raise OSError("simulated registry failure")
            return original_save(target_instance, payload)

        monkeypatch.setattr(OptiFineRegistry, "save", fail_for_second)
        with pytest.raises(OSError, match="simulated registry failure"):
            OptiFineManager.install(instance, second, second_source)
        assert first_result.installed_path.read_bytes() == first_bytes
        assert not (instance.instance_dir / "mods" / second.filename).exists()
        assert OptiFineRegistry.state(instance).version_id == first.version_id
        assert not (instance.instance_dir / ".mcw" / "optifine-transaction.json").exists()
    finally:
        Paths.restore(previous_paths)
