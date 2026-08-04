from __future__ import annotations

import sys
from pathlib import Path

from src.gui import app_restart


def test_source_restart_command_uses_current_python_and_launcher(monkeypatch) -> None:
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(sys, "argv", ["launcher.py", "--example"])

    executable, arguments, working_directory = app_restart.restart_command()

    assert Path(executable).resolve() == Path(sys.executable).resolve()
    assert Path(arguments[0]).name == "launcher.py"
    assert arguments[1:] == ["--example"]
    assert Path(working_directory).resolve() == Path(arguments[0]).resolve().parent


def test_frozen_restart_command_reuses_the_current_executable(monkeypatch, tmp_path: Path) -> None:
    executable_path = tmp_path / "MCW Launcher.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable_path))
    monkeypatch.setattr(sys, "argv", [str(executable_path), "--example"])

    executable, arguments, working_directory = app_restart.restart_command()

    assert Path(executable) == executable_path.resolve()
    assert arguments == ["--example"]
    assert Path(working_directory) == executable_path.resolve().parent
