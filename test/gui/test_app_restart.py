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


def test_frozen_restart_environment_resets_pyinstaller_parent_state(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    source = {"EXAMPLE": "value", "_PYI_APPLICATION_HOME_DIR": "stale-extraction"}

    environment = app_restart.restart_environment(source)

    assert environment["EXAMPLE"] == "value"
    assert environment["_PYI_APPLICATION_HOME_DIR"] == "stale-extraction"
    assert environment["PYINSTALLER_RESET_ENVIRONMENT"] == "1"
    assert "PYINSTALLER_RESET_ENVIRONMENT" not in source


def test_source_restart_environment_does_not_leak_pyinstaller_reset_marker(monkeypatch) -> None:
    monkeypatch.delattr(sys, "frozen", raising=False)

    environment = app_restart.restart_environment({"PYINSTALLER_RESET_ENVIRONMENT": "1", "EXAMPLE": "value"})

    assert environment == {"EXAMPLE": "value"}


def test_start_restarted_process_spawns_exact_command_and_environment(monkeypatch, tmp_path: Path) -> None:
    executable_path = tmp_path / "MCW Launcher.exe"
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable_path))
    monkeypatch.setattr(sys, "argv", [str(executable_path), "--example"])
    monkeypatch.setenv("EXAMPLE", "value")

    def fake_popen(command: list[str], **kwargs: object) -> object:
        calls.append((command, kwargs))
        return object()

    monkeypatch.setattr(app_restart.subprocess, "Popen", fake_popen)

    assert app_restart.start_restarted_process()
    assert len(calls) == 1

    command, kwargs = calls[0]
    assert command == [str(executable_path.resolve()), "--example"]
    assert Path(str(kwargs["cwd"])) == executable_path.resolve().parent
    assert kwargs["close_fds"] is True
    assert kwargs["env"]["EXAMPLE"] == "value"  # type: ignore[index]
    assert kwargs["env"]["PYINSTALLER_RESET_ENVIRONMENT"] == "1"  # type: ignore[index]


def test_start_restarted_process_reports_spawn_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        app_restart,
        "restart_command",
        lambda: ("missing-launcher.exe", [], "."),
    )
    monkeypatch.setattr(app_restart, "restart_environment", lambda: {})

    def fail_popen(command: list[str], **kwargs: object) -> object:
        raise OSError("spawn failed")

    monkeypatch.setattr(app_restart.subprocess, "Popen", fail_popen)

    assert not app_restart.start_restarted_process()
