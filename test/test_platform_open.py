from __future__ import annotations

from pathlib import Path

from src.gui import platform_open


def test_linux_path_opener_prefers_xdg_open(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(platform_open.subprocess, "Popen", lambda command, **_kwargs: calls.append(command))

    assert platform_open.open_local_path(tmp_path) is True
    assert calls == [["xdg-open", str(tmp_path.resolve())]]


def test_linux_path_opener_falls_back_to_gio(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda name: None if name == "xdg-open" else f"/usr/bin/{name}")
    monkeypatch.setattr(platform_open.subprocess, "Popen", lambda command, **_kwargs: calls.append(command))

    assert platform_open.open_local_path(tmp_path) is True
    assert calls == [["gio", "open", str(tmp_path.resolve())]]


def test_path_opener_uses_qt_when_no_linux_handler_exists(monkeypatch, tmp_path: Path) -> None:
    opened: list[str] = []
    monkeypatch.setattr(platform_open.sys, "platform", "linux")
    monkeypatch.setattr(platform_open.shutil, "which", lambda _name: None)
    monkeypatch.setattr(platform_open.QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()) or True)

    assert platform_open.open_local_path(tmp_path) is True
    assert opened == [str(tmp_path.resolve())]
