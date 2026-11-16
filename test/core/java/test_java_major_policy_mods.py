from __future__ import annotations

from pathlib import Path
import struct
from types import SimpleNamespace
import zipfile

from src.core.java.java_major_policy import JavaMajorPolicy
from src.core.java.java_runtime import JavaRuntime


def _build_dummy_class(major_version: int) -> bytes:
    return struct.pack(">IHH", 0xCAFEBABE, 0, major_version) + b"\x00" * 16


def test_required_for_instance_upgrades_fabric_1_16_1_for_java16_bytecode_mod(tmp_path: Path) -> None:
    mods_dir = tmp_path / "mods"
    mods_dir.mkdir(parents=True)
    jar_path = mods_dir / "worldpreview-2.3.3+1.16.1.jar"
    with zipfile.ZipFile(jar_path, "w") as archive:
        archive.writestr(
            "fabric.mod.json",
            '{"schemaVersion": 1, "id": "worldpreview", "depends": {"fabricloader": ">=0.12.0"}}',
        )
        archive.writestr(
            "me/voidxwalker/worldpreview/mixin/server/ServerPlayerEntityMixin.class",
            _build_dummy_class(60),  # Java 16 bytecode (60.0)
        )

    instance = SimpleNamespace(
        version_id="1.16.1",
        mod_loader=("fabric", "0.20.1"),
        instance_dir=tmp_path,
    )

    required = JavaMajorPolicy.required_for_instance(instance, 8)
    assert required == 16
    assert JavaMajorPolicy.resolve(required) == 17


def test_required_for_instance_keeps_java8_for_legacy_forge(tmp_path: Path) -> None:
    mods_dir = tmp_path / "mods"
    mods_dir.mkdir(parents=True)
    jar_path = mods_dir / "custom-mod.jar"
    with zipfile.ZipFile(jar_path, "w") as archive:
        archive.writestr("com/example/Mod.class", _build_dummy_class(60))

    instance = SimpleNamespace(
        version_id="1.16.5",
        mod_loader=("forge", "36.2.39"),
        instance_dir=tmp_path,
    )

    assert JavaMajorPolicy.required_for_instance(instance, 8) == 8


def test_extract_required_java_major_from_unsupported_class_version_error() -> None:
    crash_log = (
        "Caused by: java.lang.UnsupportedClassVersionError: net/minecraft/class_3222 has been compiled by "
        "a more recent version of the Java Runtime (class file version 60.0), this version of the Java Runtime "
        "only recognizes class file versions up to 52.0"
    )
    assert JavaRuntime.extract_required_java_major(crash_log) == 16
    assert JavaMajorPolicy.resolve(JavaRuntime.extract_required_java_major(crash_log)) == 17
