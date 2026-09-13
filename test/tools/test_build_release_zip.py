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


def test_build_release_zip_supports_onedir_directory_target(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("readme", encoding="utf-8")
    (project / "LICENSE").write_text("license", encoding="utf-8")
    for directory in ("lang", "themes"):
        (project / directory).mkdir()
        (project / directory / "file.txt").write_text(directory, encoding="utf-8")

    app_dir = tmp_path / "dist" / "MCW Launcher"
    app_dir.mkdir(parents=True)
    exe_file = app_dir / "MCW Launcher.exe"
    exe_file.write_bytes(b"stub-exe-content")

    internal_dir = app_dir / "_internal"
    internal_dir.mkdir()
    (internal_dir / "python312.dll").write_bytes(b"python-dll")
    pyside_dir = internal_dir / "PySide6"
    pyside_dir.mkdir()
    (pyside_dir / "QtCore.pyd").write_bytes(b"qt-core-pyd")

    updater = tmp_path / "MCW Updater.exe"
    updater.write_bytes(b"updater-exe-content")

    output = project / "release" / f"MCW-Launcher-v{VERSION_ID}-windows-x64.zip"
    build_release_zip(project, app_dir, updater, VERSION_ID, output, "windows-x64")

    with zipfile.ZipFile(output) as archive:
        root = f"MCW-Launcher-v{VERSION_ID}-windows-x64"
        names = set(archive.namelist())
        assert f"{root}/MCW Launcher.exe" in names
        assert f"{root}/_internal/python312.dll" in names
        assert f"{root}/_internal/PySide6/QtCore.pyd" in names
        assert f"{root}/updater/MCW Updater.exe" in names
        assert f"{root}/lang/file.txt" in names
        assert f"{root}/themes/file.txt" in names

        manifest = json.loads(archive.read(f"{root}/mcw-update.json"))
        assert manifest["schema_version"] == 2
        assert manifest["executable"] == "MCW Launcher.exe"
        assert manifest["updater"] == "updater/MCW Updater.exe"
        assert "_internal/python312.dll" in manifest["files"]
        assert "_internal/PySide6/QtCore.pyd" in manifest["files"]
        assert "MCW Launcher.exe" in manifest["files"]


def test_build_release_zip_supports_onedir_executable_path_target(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("readme", encoding="utf-8")
    (project / "LICENSE").write_text("license", encoding="utf-8")

    app_dir = tmp_path / "dist" / "MCW Launcher"
    app_dir.mkdir(parents=True)
    exe_file = app_dir / "MCW Launcher.exe"
    exe_file.write_bytes(b"stub-exe-content")

    internal_dir = app_dir / "_internal"
    internal_dir.mkdir()
    (internal_dir / "python312.dll").write_bytes(b"python-dll")

    updater = tmp_path / "MCW Updater.exe"
    updater.write_bytes(b"updater-exe")

    output = project / "release" / f"MCW-Launcher-v{VERSION_ID}-windows-x64.zip"
    # Pass path directly to the executable file inside the onedir folder
    build_release_zip(project, exe_file, updater, VERSION_ID, output, "windows-x64")

    with zipfile.ZipFile(output) as archive:
        root = f"MCW-Launcher-v{VERSION_ID}-windows-x64"
        names = set(archive.namelist())
        assert f"{root}/MCW Launcher.exe" in names
        assert f"{root}/_internal/python312.dll" in names
        manifest = json.loads(archive.read(f"{root}/mcw-update.json"))
        assert "_internal/python312.dll" in manifest["files"]


def test_onedir_package_upgrades_legacy_onefile_installation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core.update.update_applier import UpdateApplier, UpdateApplyRequest

    # 1. Simulate legacy 1.5.1 installation (single onefile .exe)
    installation = tmp_path / "installed_app"
    installation.mkdir()
    legacy_exe = installation / "MCW Launcher.exe"
    legacy_exe.write_bytes(b"legacy-100mb-exe-content")
    (installation / "mcw-update.json").write_text(json.dumps({
        "schema_version": 2,
        "version": "1.5.1",
        "platform": "windows-x64",
        "executable": "MCW Launcher.exe",
        "updater": "updater/MCW Updater.exe",
        "files": ["MCW Launcher.exe", "updater/MCW Updater.exe", "mcw-update.json"],
        "cleanup_paths": ["docs"],
    }), encoding="utf-8")

    # 2. Build onedir release ZIP for 1.6
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("readme-1.6", encoding="utf-8")
    (project / "LICENSE").write_text("license", encoding="utf-8")

    app_dir = tmp_path / "dist" / "MCW Launcher"
    app_dir.mkdir(parents=True)
    new_exe = app_dir / "MCW Launcher.exe"
    new_exe.write_bytes(b"new-onedir-stub-300kb")
    internal_dir = app_dir / "_internal"
    internal_dir.mkdir()
    (internal_dir / "python312.dll").write_bytes(b"runtime-dll")
    (internal_dir / "Qt6Core.dll").write_bytes(b"qt6-core-dll")

    updater = tmp_path / "MCW Updater.exe"
    updater.write_bytes(b"bundled-updater-v2")

    release_zip = project / f"MCW-Launcher-v{VERSION_ID}-windows-x64.zip"
    build_release_zip(project, app_dir, updater, VERSION_ID, release_zip, "windows-x64")

    # 3. Simulate downloading and unpacking to staging
    staging = tmp_path / "staging"
    staging.mkdir()
    with zipfile.ZipFile(release_zip) as archive:
        archive.extractall(staging)
    source_dir = staging / f"MCW-Launcher-v{VERSION_ID}-windows-x64"

    # 4. Run UpdateApplier
    updater_dir = tmp_path / "updater_temp"
    updater_dir.mkdir()
    request = UpdateApplyRequest(
        parent_pid=9999,
        source_directory=source_dir,
        destination_directory=installation,
        executable_name="MCW Launcher.exe",
        updater_directory=updater_dir,
        staging_directory=staging,
        persistent_log_path=installation / "logs" / "updater.log",
        target_version=VERSION_ID,
    )
    applier = UpdateApplier(request)
    started: list[bool] = []
    monkeypatch.setattr(applier, "_wait_for_process_exit", lambda _pid: None)
    monkeypatch.setattr(applier, "_wait_for_launcher_release", lambda: None)
    monkeypatch.setattr(applier, "_start_launcher", lambda **_kw: started.append(True))

    exit_code = applier.run()
    assert exit_code == 0
    assert started == [True]

    # 5. Verify upgraded directory structure
    assert (installation / "MCW Launcher.exe").read_bytes() == b"new-onedir-stub-300kb"
    assert (installation / "_internal" / "python312.dll").read_bytes() == b"runtime-dll"
    assert (installation / "_internal" / "Qt6Core.dll").read_bytes() == b"qt6-core-dll"
    assert (installation / "README.md").read_text(encoding="utf-8") == "readme-1.6"

