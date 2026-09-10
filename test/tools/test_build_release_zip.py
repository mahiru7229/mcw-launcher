from pathlib import Path
import json
import subprocess
import sys
import zipfile

import pytest

from src.config import VERSION_ID
from tools.build_release_zip import build_release_zip, validate_platform, validate_release_version


def test_validate_release_version_accepts_current_release() -> None:
    assert validate_release_version(f"v{VERSION_ID}") == VERSION_ID


def test_validate_release_version_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        validate_release_version("0.5.1")


def test_validate_platform_accepts_release_targets() -> None:
    assert validate_platform("windows-x64") == "windows-x64"
    assert validate_platform("LINUX-X64") == "linux-x64"


def test_validate_platform_rejects_unknown_target() -> None:
    with pytest.raises(ValueError, match="Unsupported release platform"):
        validate_platform("macos-arm64")


def test_build_release_zip_writes_schema2_manifest_and_bundled_updater(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("readme", encoding="utf-8")
    (project / "LICENSE").write_text("license", encoding="utf-8")
    for directory in ("lang", "themes", "docs"):
        (project / directory).mkdir()
        (project / directory / "keep.txt").write_text(directory, encoding="utf-8")
    executable = tmp_path / "MCW Launcher.exe"
    executable.write_bytes(b"fake-exe")
    updater = tmp_path / "MCW Updater.exe"
    updater.write_bytes(b"fake-updater")
    output = project / "release" / f"MCW-Launcher-v{VERSION_ID}-windows-x64.zip"

    build_release_zip(project, executable, updater, VERSION_ID, output)

    with zipfile.ZipFile(output) as archive:
        root = f"MCW-Launcher-v{VERSION_ID}-windows-x64"
        manifest = json.loads(archive.read(f"{root}/mcw-update.json"))
        assert manifest["schema_version"] == 2
        assert manifest["version"] == VERSION_ID
        assert manifest["platform"] == "windows-x64"
        assert manifest["updater"] == "updater/MCW Updater.exe"
        assert f"{root}/MCW Launcher.exe" in archive.namelist()
        assert f"{root}/updater/MCW Updater.exe" in archive.namelist()
        assert "updater/MCW Updater.exe" in manifest["files"]
        assert manifest["cleanup_paths"] == ["docs"]
        assert f"{root}/docs/keep.txt" not in archive.namelist()
    assert output.with_name(f"{output.name}.sha256").is_file()


def test_build_release_zip_requires_bundled_updater(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    executable = tmp_path / "MCW Launcher.exe"
    executable.write_bytes(b"fake-exe")
    output = project / "release.zip"

    with pytest.raises(FileNotFoundError, match="Bundled updater"):
        build_release_zip(project, executable, tmp_path / "missing-updater.exe", VERSION_ID, output)


def test_build_release_zip_writes_portable_lf_checksum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("readme", encoding="utf-8")
    (project / "LICENSE").write_text("license", encoding="utf-8")
    executable = project / "MCW Launcher.exe"
    executable.write_bytes(b"windows-binary")
    updater = project / "MCW Updater.exe"
    updater.write_bytes(b"updater")
    output = project / "release" / f"MCW-Launcher-v{VERSION_ID}-windows-x64.zip"
    original_write_text = Path.write_text

    def reject_text_mode_checksum(path: Path, *args, **kwargs):
        if path.name.endswith(".sha256"):
            raise AssertionError("Checksum must be written as bytes so Windows cannot emit CRLF")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", reject_text_mode_checksum)

    build_release_zip(project, executable, updater, VERSION_ID, output)

    checksum = output.with_name(f"{output.name}.sha256").read_bytes()
    assert checksum.endswith(b"\n")
    assert b"\r" not in checksum
    assert checksum.decode("utf-8").endswith(f"  {output.name}\n")


def test_build_linux_release_zip_writes_launcher_and_updater_executable_modes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("readme", encoding="utf-8")
    (project / "LICENSE").write_text("license", encoding="utf-8")
    executable = project / "mcw-launcher"
    executable.write_bytes(b"linux-binary")
    executable.chmod(0o644)
    updater = project / "mcw-updater"
    updater.write_bytes(b"linux-updater")
    updater.chmod(0o644)
    output = project / "release" / f"MCW-Launcher-v{VERSION_ID}-linux-x64.zip"

    build_release_zip(project, executable, updater, VERSION_ID, output, "linux-x64")

    with zipfile.ZipFile(output) as archive:
        root = f"MCW-Launcher-v{VERSION_ID}-linux-x64"
        manifest = json.loads(archive.read(f"{root}/mcw-update.json"))
        executable_info = archive.getinfo(f"{root}/mcw-launcher")
        updater_info = archive.getinfo(f"{root}/updater/mcw-updater")
        assert manifest["platform"] == "linux-x64"
        assert manifest["executable"] == "mcw-launcher"
        assert manifest["updater"] == "updater/mcw-updater"
        assert executable_info.create_system == 3
        assert executable_info.external_attr >> 16 & 0o777 == 0o755
        assert updater_info.create_system == 3
        assert updater_info.external_attr >> 16 & 0o777 == 0o755


def test_release_script_runs_directly_from_any_working_directory(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    executable = tmp_path / "MCW Launcher.exe"
    executable.write_bytes(b"fake-exe")
    updater = tmp_path / "MCW Updater.exe"
    updater.write_bytes(b"fake-updater")
    output = tmp_path / f"MCW-Launcher-v{VERSION_ID}-windows-x64.zip"

    result = subprocess.run([
        sys.executable,
        str(project_root / "tools" / "build_release_zip.py"),
        "--exe", str(executable),
        "--updater", str(updater),
        "--version", VERSION_ID,
        "--output", str(output),
    ], cwd=tmp_path, capture_output=True, text=True, timeout=30)

    assert result.returncode == 0, result.stderr
    assert output.is_file()
    assert output.with_name(f"{output.name}.sha256").is_file()
