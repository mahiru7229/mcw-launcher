from __future__ import annotations

import subprocess
from pathlib import Path

from src.gui import platform_open


class _Process:
    def __init__(self, returncode: int = 0, *, timeout: bool = False) -> None:
        self.returncode = returncode
        self.timeout = timeout

    def wait(self, timeout: float | None = None) -> int:
        if self.timeout:
            raise subprocess.TimeoutExpired(["desktop-handler"], timeout)
        return self.returncode


def test_linux_path_opener_prefers_xdg_open(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(platform_open.subprocess, "Popen", lambda command, **_kwargs: calls.append(command) or _Process())

    assert platform_open.open_local_path(tmp_path) is True
    assert calls == [["/usr/bin/xdg-open", str(tmp_path.resolve())]]


def test_linux_path_opener_falls_back_to_gio(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda name: None if name == "xdg-open" else f"/usr/bin/{name}")
    monkeypatch.setattr(platform_open.subprocess, "Popen", lambda command, **_kwargs: calls.append(command) or _Process())

    assert platform_open.open_local_path(tmp_path) is True
    assert calls == [["/usr/bin/gio", "open", str(tmp_path.resolve())]]


def test_linux_path_opener_tries_gio_after_xdg_open_exits_with_error(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda name: f"/usr/bin/{name}")

    def start(command, **_kwargs):
        calls.append(command)
        return _Process(returncode=3 if command[0].endswith("xdg-open") else 0)

    monkeypatch.setattr(platform_open.subprocess, "Popen", start)

    assert platform_open.open_local_path(tmp_path) is True
    assert calls == [
        ["/usr/bin/xdg-open", str(tmp_path.resolve())],
        ["/usr/bin/gio", "open", str(tmp_path.resolve())],
    ]


def test_linux_path_opener_uses_pcmanfm_qt_after_standard_handlers_fail(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda name: f"/usr/bin/{name}")

    def start(command, **_kwargs):
        calls.append(command)
        return _Process(returncode=0 if command[0].endswith("pcmanfm-qt") else 1)

    monkeypatch.setattr(platform_open.subprocess, "Popen", start)

    assert platform_open.open_local_path(tmp_path) is True
    assert calls[-1] == ["/usr/bin/pcmanfm-qt", str(tmp_path.resolve())]


def test_linux_path_opener_treats_running_handler_as_accepted(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        platform_open.subprocess,
        "Popen",
        lambda command, **_kwargs: calls.append(command) or _Process(timeout=True),
    )

    assert platform_open.open_local_path(tmp_path) is True
    assert len(calls) == 1


def test_linux_path_opener_sanitizes_frozen_pyinstaller_environment(monkeypatch, tmp_path: Path) -> None:
    environments: list[dict[str, str]] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.sys, "frozen", True, raising=False)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/_MEI123")
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/usr/local/lib")
    monkeypatch.setenv("QT_PLUGIN_PATH", "/tmp/_MEI123/PySide6/Qt/plugins")
    monkeypatch.setenv("QT_QPA_PLATFORM_PLUGIN_PATH", "/tmp/_MEI123/PySide6/Qt/plugins/platforms")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(platform_open.shutil, "which", lambda name: f"/usr/bin/{name}")

    def start(_command, **kwargs):
        environments.append(kwargs["env"])
        return _Process()

    monkeypatch.setattr(platform_open.subprocess, "Popen", start)

    assert platform_open.open_local_path(tmp_path) is True
    assert environments[0]["LD_LIBRARY_PATH"] == "/usr/local/lib"
    assert "LD_LIBRARY_PATH_ORIG" not in environments[0]
    assert "QT_PLUGIN_PATH" not in environments[0]
    assert "QT_QPA_PLATFORM_PLUGIN_PATH" not in environments[0]
    assert environments[0]["DISPLAY"] == ":0"


def test_path_opener_uses_qt_when_no_linux_handler_exists(monkeypatch, tmp_path: Path) -> None:
    opened: list[str] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda _name: None)
    monkeypatch.setattr(platform_open.QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()) or True)

    assert platform_open.open_local_path(tmp_path) is True
    assert len(opened) == 1
    assert Path(opened[0]) == tmp_path.resolve()


def test_path_opener_rejects_a_missing_path(monkeypatch, tmp_path: Path) -> None:
    opened: list[str] = []
    missing = tmp_path / "missing"
    monkeypatch.setattr(platform_open.QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()) or True)

    assert platform_open.open_local_path(missing) is False
    assert opened == []
