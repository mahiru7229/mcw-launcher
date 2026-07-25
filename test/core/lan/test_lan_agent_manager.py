from pathlib import Path
from types import SimpleNamespace
import hashlib
import zipfile

import pytest

from src.core.fs.paths import Paths
from src.core.lan.lan_agent_manager import LanAgentInstallResult, LanAgentManager


def make_version() -> SimpleNamespace:
    return SimpleNamespace(id="26.2", raw_json={})


def write_supported_client(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b"class-data:setUsesAuthentication:(Z)V"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(LanAgentManager.TARGET_CLASS + ".class", payload)


def test_bundled_agent_matches_pinned_sha256() -> None:
    path = Path(__file__).resolve().parents[3] / "runtime" / LanAgentManager.AGENT_FILENAME

    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == LanAgentManager.AGENT_SHA256


def test_install_copies_verified_agent_atomically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = Path(__file__).resolve().parents[3] / "runtime" / LanAgentManager.AGENT_FILENAME
    destination = tmp_path / "cache" / LanAgentManager.AGENT_FILENAME
    monkeypatch.setattr(LanAgentManager, "_bundled_agent_path", classmethod(lambda cls: source))
    monkeypatch.setattr(LanAgentManager, "runtime_agent_path", classmethod(lambda cls: destination))

    first = LanAgentManager.install()
    second = LanAgentManager.install()

    assert first == LanAgentInstallResult(destination, True)
    assert second == LanAgentInstallResult(destination, False)
    assert destination.read_bytes() == source.read_bytes()
    assert not destination.with_suffix(destination.suffix + ".part").exists()


def test_runtime_arguments_are_emitted_only_for_private_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = tmp_path / "client.jar"
    write_supported_client(client)
    installed = tmp_path / "mcw-lan-agent.jar"
    monkeypatch.setattr(Paths, "client", staticmethod(lambda _version: client))
    monkeypatch.setattr(LanAgentManager, "install", classmethod(lambda cls: LanAgentInstallResult(installed, False)))

    assert LanAgentManager.runtime_arguments(make_version(), "microsoft_only") == []
    arguments = LanAgentManager.runtime_arguments(make_version(), "private_offline")

    assert arguments == [
        "-Dmcw.lan.offline=true",
        f"-Dmcw.lan.target.class={LanAgentManager.TARGET_CLASS}",
        f"-Dmcw.lan.target.method={LanAgentManager.TARGET_METHOD}",
        f"-javaagent:{installed}",
    ]


def test_runtime_arguments_fail_safe_for_unsupported_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = tmp_path / "client.jar"
    with zipfile.ZipFile(client, "w") as archive:
        archive.writestr("a/b.class", b"unknown")
    monkeypatch.setattr(Paths, "client", staticmethod(lambda _version: client))

    with pytest.raises(RuntimeError, match="experimental"):
        LanAgentManager.runtime_arguments(make_version(), "private_offline")


def test_sanitize_user_arguments_removes_only_mcw_agent_overrides() -> None:
    arguments = LanAgentManager.sanitize_user_jvm_arguments(
        [
            "-Dmcw.lan.offline=false",
            "-Dmcw.lan.target.class=example/Evil",
            "-javaagent:C:/cache/mcw-lan-agent.jar",
            "-javaagent:C:/tools/other-agent.jar",
            "-Dexample=true",
        ]
    )

    assert arguments == ["-javaagent:C:/tools/other-agent.jar", "-Dexample=true"]
