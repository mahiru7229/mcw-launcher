from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_ROOT = PROJECT_ROOT / "tools" / "update_bridge"
if str(BRIDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(BRIDGE_ROOT))

import update_bridge as bridge


def _write_package(root: Path, version: str = bridge.TARGET_VERSION) -> tuple[Path, list[Path]]:
    content = root / f"MCW-Launcher-v{version}-windows-x64"
    content.mkdir(parents=True)
    files = {
        "MCW Launcher.exe": b"new executable",
        "README.md": b"new readme",
        "updater/MCW Updater.exe": b"new updater",
        "mcw-update.json": b"",
    }
    manifest = {
        "schema_version": 2,
        "version": version,
        "platform": "windows-x64",
        "executable": "MCW Launcher.exe",
        "updater": "updater/MCW Updater.exe",
        "files": sorted(files),
    }
    files["mcw-update.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    for name, data in files.items():
        path = content / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return content, sorted((Path(name) for name in files), key=lambda path: path.as_posix().casefold())


def test_parse_checksum_accepts_sha256sum_format() -> None:
    digest = "a" * 64
    assert bridge.parse_checksum(f"{digest}  package.zip\n", "package.zip") == digest


def test_select_release_package_requires_exact_checksum_sidecar() -> None:
    archive = f"MCW-Launcher-v{bridge.TARGET_VERSION}-windows-x64.zip"
    payload = {
        "assets": [
            {"name": archive, "browser_download_url": "https://example.invalid/package", "size": 1234},
            {"name": archive + ".sha256", "browser_download_url": "https://example.invalid/checksum", "size": 100},
        ]
    }
    selected = bridge.select_release_package(payload, bridge.TARGET_TAG)
    assert selected.archive.name == archive
    assert selected.checksum.name == archive + ".sha256"


def test_validate_manifest_rejects_unlisted_file(tmp_path: Path) -> None:
    content, _ = _write_package(tmp_path)
    (content / "surprise.dll").write_bytes(b"unexpected")
    with pytest.raises(bridge.BridgeError, match="unlisted files"):
        bridge.validate_package_manifest(content, bridge.TARGET_TAG)


def test_validate_manifest_returns_managed_paths(tmp_path: Path) -> None:
    content, expected = _write_package(tmp_path)
    managed = bridge.validate_package_manifest(content, bridge.TARGET_TAG)
    assert managed == expected


def test_safe_extract_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "no")
    with pytest.raises(bridge.BridgeError, match="Unsafe path"):
        bridge.safe_extract_archive(archive, tmp_path / "out")


def test_safe_extract_resolves_single_wrapper_directory(tmp_path: Path) -> None:
    archive = tmp_path / "good.zip"
    wrapper = f"MCW-Launcher-v{bridge.TARGET_VERSION}-windows-x64"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(f"{wrapper}/MCW Launcher.exe", "binary")
    content = bridge.safe_extract_archive(archive, tmp_path / "out")
    assert content.name == wrapper
    assert (content / "MCW Launcher.exe").is_file()


def test_install_package_replaces_executable_first_and_keeps_backup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install = tmp_path / "install"
    install.mkdir()
    (install / "MCW Launcher.exe").write_bytes(b"old executable")
    (install / "README.md").write_bytes(b"old readme")
    content, managed = _write_package(tmp_path / "payload")

    calls: list[str] = []
    original = bridge.replace_file_with_retry

    def recording_replace(source: Path, destination: Path, timeout_seconds: float = bridge.REPLACE_TIMEOUT_SECONDS) -> None:
        calls.append(destination.name)
        original(source, destination, timeout_seconds)

    monkeypatch.setattr(bridge, "replace_file_with_retry", recording_replace)
    backup = bridge.install_package(content, install, managed, lambda _: None)

    assert calls[0] == "MCW Launcher.exe"
    assert (install / "MCW Launcher.exe").read_bytes() == b"new executable"
    assert (install / "README.md").read_bytes() == b"new readme"
    assert (backup / "MCW Launcher.exe").read_bytes() == b"old executable"
    assert (backup / "README.md").read_bytes() == b"old readme"


def test_install_package_rolls_back_only_changed_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install = tmp_path / "install"
    install.mkdir()
    (install / "MCW Launcher.exe").write_bytes(b"old executable")
    (install / "README.md").write_bytes(b"old readme")
    content, managed = _write_package(tmp_path / "payload")

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
        bridge.install_package(content, install, managed, lambda _: None)

    assert (install / "MCW Launcher.exe").read_bytes() == b"old executable"
    assert (install / "README.md").read_bytes() == b"old readme"


def test_sha256_file(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"mcw bridge")
    assert bridge.sha256_file(path) == hashlib.sha256(b"mcw bridge").hexdigest()


def test_failed_executable_replace_does_not_rollback_unchanged_executable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install = tmp_path / "install"
    install.mkdir()
    (install / "MCW Launcher.exe").write_bytes(b"old executable")
    content, managed = _write_package(tmp_path / "payload")

    calls: list[tuple[str, str]] = []

    def always_locked(source: Path, destination: Path, timeout_seconds: float = bridge.REPLACE_TIMEOUT_SECONDS) -> None:
        calls.append((source.name, destination.name))
        raise bridge.BridgeError("simulated WinError 5")

    monkeypatch.setattr(bridge, "replace_file_with_retry", always_locked)
    with pytest.raises(bridge.BridgeError, match="simulated WinError 5"):
        bridge.install_package(content, install, managed, lambda _: None)

    assert calls == [("MCW Launcher.exe", "MCW Launcher.exe")]
    assert (install / "MCW Launcher.exe").read_bytes() == b"old executable"
