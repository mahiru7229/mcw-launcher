from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import zipfile

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_ROOT = PROJECT_ROOT / "tools" / "update_bridge"
if str(BRIDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(BRIDGE_ROOT))

import update_bridge as bridge


def _contract(platform_id: str) -> bridge.PlatformContract:
    return bridge.platform_contract(platform_id)


def _write_package(
    root: Path,
    platform_id: str,
    version: str = bridge.TARGET_VERSION,
) -> tuple[Path, list[Path]]:
    contract = _contract(platform_id)
    content = root / f"MCW-Launcher-v{version}-{platform_id}"
    content.mkdir(parents=True)
    files = {
        contract.launcher_name: b"new executable",
        "README.md": b"new readme",
        contract.updater_relative: b"new updater",
        "mcw-update.json": b"",
    }
    manifest = {
        "schema_version": 2,
        "version": version,
        "platform": platform_id,
        "executable": contract.launcher_name,
        "updater": contract.updater_relative,
        "files": sorted(files),
    }
    files["mcw-update.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    for name, data in files.items():
        path = content / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return content, sorted((Path(name) for name in files), key=lambda path: path.as_posix().casefold())


@pytest.mark.parametrize("platform_id", ["windows-x64", "linux-x64"])
def test_select_release_package_requires_platform_checksum(platform_id: str) -> None:
    archive = f"MCW-Launcher-v{bridge.TARGET_VERSION}-{platform_id}.zip"
    payload = {
        "assets": [
            {"name": archive, "browser_download_url": "https://example.invalid/package", "size": 1234},
            {"name": archive + ".sha256", "browser_download_url": "https://example.invalid/checksum", "size": 100},
        ]
    }
    selected = bridge.select_release_package(payload, bridge.TARGET_TAG, platform_id)
    assert selected.archive.name == archive
    assert selected.checksum.name == archive + ".sha256"


def test_linux_release_selection_does_not_fall_back_to_windows_asset() -> None:
    archive = f"MCW-Launcher-v{bridge.TARGET_VERSION}-windows-x64.zip"
    payload = {
        "assets": [
            {"name": archive, "browser_download_url": "https://example.invalid/package", "size": 1234},
            {"name": archive + ".sha256", "browser_download_url": "https://example.invalid/checksum", "size": 100},
        ]
    }
    with pytest.raises(bridge.BridgeError, match="linux-x64"):
        bridge.select_release_package(payload, bridge.TARGET_TAG, "linux-x64")


def test_parse_checksum_accepts_sha256sum_format() -> None:
    digest = "a" * 64
    assert bridge.parse_checksum(f"{digest}  package.zip\n", "package.zip") == digest


@pytest.mark.parametrize("platform_id", ["windows-x64", "linux-x64"])
def test_validate_manifest_rejects_unlisted_file(tmp_path: Path, platform_id: str) -> None:
    content, _ = _write_package(tmp_path, platform_id)
    (content / "surprise.bin").write_bytes(b"unexpected")
    with pytest.raises(bridge.BridgeError, match="unlisted files"):
        bridge.validate_package_manifest(content, bridge.TARGET_TAG, platform_id)


@pytest.mark.parametrize("platform_id", ["windows-x64", "linux-x64"])
def test_validate_manifest_returns_managed_paths(tmp_path: Path, platform_id: str) -> None:
    content, expected = _write_package(tmp_path, platform_id)
    managed = bridge.validate_package_manifest(content, bridge.TARGET_TAG, platform_id)
    assert managed == expected


def test_linux_manifest_rejects_windows_contract(tmp_path: Path) -> None:
    content, _ = _write_package(tmp_path, "windows-x64")
    with pytest.raises(bridge.BridgeError, match="Linux x64"):
        bridge.validate_package_manifest(content, bridge.TARGET_TAG, "linux-x64")


def test_safe_extract_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "no")
    with pytest.raises(bridge.BridgeError, match="Unsafe path"):
        bridge.safe_extract_archive(archive, tmp_path / "out")


def test_safe_extract_resolves_single_wrapper_directory(tmp_path: Path) -> None:
    archive = tmp_path / "good.zip"
    wrapper = f"MCW-Launcher-v{bridge.TARGET_VERSION}-linux-x64"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(f"{wrapper}/mcw-launcher", "binary")
    content = bridge.safe_extract_archive(archive, tmp_path / "out")
    assert content.name == wrapper
    assert (content / "mcw-launcher").is_file()


@pytest.mark.parametrize("platform_id", ["windows-x64", "linux-x64"])
def test_install_package_replaces_executable_first_and_keeps_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    platform_id: str,
) -> None:
    contract = _contract(platform_id)
    install = tmp_path / "install"
    install.mkdir()
    (install / contract.launcher_name).write_bytes(b"old executable")
    (install / "README.md").write_bytes(b"old readme")
    content, managed = _write_package(tmp_path / "payload", platform_id)

    calls: list[str] = []
    original = bridge.replace_file_with_retry

    def recording_replace(source: Path, destination: Path, timeout_seconds: float = bridge.REPLACE_TIMEOUT_SECONDS) -> None:
        calls.append(destination.name)
        original(source, destination, timeout_seconds)

    monkeypatch.setattr(bridge, "replace_file_with_retry", recording_replace)
    backup = bridge.install_package(content, install, managed, lambda _: None, platform_id=platform_id)

    assert calls[0] == contract.launcher_name
    assert (install / contract.launcher_name).read_bytes() == b"new executable"
    assert (install / "README.md").read_bytes() == b"new readme"
    assert (backup / contract.launcher_name).read_bytes() == b"old executable"
    assert (backup / "README.md").read_bytes() == b"old readme"


@pytest.mark.skipif(os.name == "nt", reason="POSIX execute-bit semantics are required")
def test_linux_install_restores_launcher_and_updater_execute_bits(tmp_path: Path) -> None:
    contract = _contract("linux-x64")
    install = tmp_path / "install"
    install.mkdir()
    launcher = install / contract.launcher_name
    launcher.write_bytes(b"old executable")
    launcher.chmod(0o755)
    content, managed = _write_package(tmp_path / "payload", "linux-x64")
    # Simulate our safe ZIP extraction, which writes ordinary non-executable files.
    (content / contract.launcher_name).chmod(0o644)
    (content / contract.updater_relative).chmod(0o644)

    bridge.install_package(content, install, managed, lambda _: None, platform_id="linux-x64")

    assert os.access(install / contract.launcher_name, os.X_OK)
    assert os.access(install / contract.updater_relative, os.X_OK)


def test_install_package_rolls_back_only_changed_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = _contract("windows-x64")
    install = tmp_path / "install"
    install.mkdir()
    (install / contract.launcher_name).write_bytes(b"old executable")
    (install / "README.md").write_bytes(b"old readme")
    content, managed = _write_package(tmp_path / "payload", "windows-x64")

    original = bridge.replace_file_with_retry
    failed_once = False

    def fail_readme(source: Path, destination: Path, timeout_seconds: float = bridge.REPLACE_TIMEOUT_SECONDS) -> None:
        nonlocal failed_once
        if destination.name == "README.md" and not failed_once:
            failed_once = True
            raise bridge.BridgeError("simulated copy failure")
        original(source, destination, timeout_seconds)

    monkeypatch.setattr(bridge, "replace_file_with_retry", fail_readme)
    with pytest.raises(bridge.BridgeError, match="simulated copy failure"):
        bridge.install_package(content, install, managed, lambda _: None, platform_id="windows-x64")

    assert (install / contract.launcher_name).read_bytes() == b"old executable"
    assert (install / "README.md").read_bytes() == b"old readme"


def test_sha256_file(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"mcw bridge")
    assert bridge.sha256_file(path) == hashlib.sha256(b"mcw bridge").hexdigest()


def test_failed_executable_replace_does_not_rollback_unchanged_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _contract("windows-x64")
    install = tmp_path / "install"
    install.mkdir()
    (install / contract.launcher_name).write_bytes(b"old executable")
    content, managed = _write_package(tmp_path / "payload", "windows-x64")

    calls: list[tuple[str, str]] = []

    def always_locked(source: Path, destination: Path, timeout_seconds: float = bridge.REPLACE_TIMEOUT_SECONDS) -> None:
        calls.append((source.name, destination.name))
        raise bridge.BridgeError("simulated WinError 5")

    monkeypatch.setattr(bridge, "replace_file_with_retry", always_locked)
    with pytest.raises(bridge.BridgeError, match="simulated WinError 5"):
        bridge.install_package(content, install, managed, lambda _: None, platform_id="windows-x64")

    assert calls == [(contract.launcher_name, contract.launcher_name)]
    assert (install / contract.launcher_name).read_bytes() == b"old executable"


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux signal behavior")
def test_linux_graceful_and_force_close_use_term_then_kill(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, signal.Signals]] = []

    def fake_kill(pid: int, sig: signal.Signals) -> None:
        calls.append((pid, sig))

    monkeypatch.setattr(os, "kill", fake_kill)
    bridge.request_graceful_close([111, 222])
    bridge.force_terminate_processes([111])

    assert (111, signal.SIGTERM) in calls
    assert (222, signal.SIGTERM) in calls
    assert (111, signal.SIGKILL) in calls
