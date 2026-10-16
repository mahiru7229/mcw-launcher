from pathlib import Path

import pytest

from launcher import _validate_startup_dependencies


def test_current_source_contains_required_startup_dependencies() -> None:
    project_root = Path(__file__).resolve().parents[2]

    _validate_startup_dependencies(project_root)


def test_incomplete_source_reports_all_missing_dependencies(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError) as captured:
        _validate_startup_dependencies(tmp_path)

    message = str(captured.value)
    assert "installation is incomplete" in message
    assert "mcw_core/api/lan/lan_agent_manager.py" in message
    assert "mcw_core/api/curseforge/curseforge_errors.py" in message
    assert "mcw_core/rpc/dispatcher.py" in message
    assert "runtime/mcw-lan-agent.jar" in message


def test_launcher_startup_failure_formats_stage_and_error_log_without_name_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import launcher
    import mcw_core.api.startup_runner as startup_runner
    from PySide6.QtWidgets import QMessageBox

    captured_messages: list[str] = []

    class DummySplash:
        def show(self) -> None:
            pass

        def update_progress(self, *_args, **_kwargs) -> None:
            pass

        def show_error(self) -> None:
            pass

        def raise_(self) -> None:
            pass

        def activateWindow(self) -> None:
            pass

        def close(self) -> None:
            pass

    class DummyApp:
        class _Sig:
            def connect(self, *_args, **_kwargs) -> None:
                pass

        aboutToQuit = _Sig()

        def processEvents(self) -> None:
            pass

        def exec(self) -> int:
            return 0

    class DummyMessageBox:
        class Icon:
            Critical = 3

        class ButtonRole:
            ActionRole = 0

        class StandardButton:
            Close = 1

        def __init__(self, _parent=None) -> None:
            pass

        def setIcon(self, _icon) -> None:
            pass

        def setWindowTitle(self, _title: str) -> None:
            pass

        def setText(self, text: str) -> None:
            captured_messages.append(str(text))

        def addButton(self, *_args, **_kwargs):
            return object()

        def exec(self) -> int:
            return 0

        def clickedButton(self):
            return None

    monkeypatch.setattr("src.gui.application.create_application", lambda _argv: DummyApp())
    monkeypatch.setattr("src.gui.startup_splash.StartupSplash", DummySplash)
    monkeypatch.setattr(
        startup_runner,
        "run_startup_task",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("Simulated startup failure")),
    )
    monkeypatch.setattr(launcher, "_write_startup_error", lambda *_args, **_kwargs: tmp_path / "startup-error.log")
    monkeypatch.setattr(launcher, "_find_recovery_executable", lambda: None)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox", DummyMessageBox)

    with pytest.raises(SystemExit) as exc_info:
        launcher.main()

    assert exc_info.value.code == 1
    assert len(captured_messages) == 1
    assert "Simulated startup failure" in captured_messages[0]
    assert "startup-error.log" in captured_messages[0]

