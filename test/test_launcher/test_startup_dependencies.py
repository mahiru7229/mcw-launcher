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


def test_lazy_dialogs_finalization_and_translation(monkeypatch: pytest.MonkeyPatch) -> None:
    from PySide6.QtWidgets import QApplication
    from src.gui.display_profile import select_display_profile
    from src.gui.main_window import MainWindow

    _app = QApplication.instance() or QApplication(["test"])
    monkeypatch.setattr(MainWindow, "_initialize_data", lambda self: None)
    monkeypatch.setattr(MainWindow, "_detect_display_profile", lambda self: select_display_profile(1920, 1080))

    window = MainWindow()

    assert window._repair_center_dialog is None
    assert window._mod_manager_dialog is None

    calls: list[object] = []
    original_finalize = window._finalize_lazy_dialog

    def tracking_finalize(dialog):
        calls.append(dialog)
        return original_finalize(dialog)

    monkeypatch.setattr(window, "_finalize_lazy_dialog", tracking_finalize)

    dialog = window.repair_center_dialog
    assert dialog is not None
    assert window._repair_center_dialog is dialog
    assert dialog in calls


def test_mods_page_project_details_does_not_instantiate_dialogs(monkeypatch: pytest.MonkeyPatch) -> None:
    from PySide6.QtWidgets import QApplication
    from src.gui.display_profile import select_display_profile
    from src.gui.main_window import MainWindow

    _app = QApplication.instance() or QApplication(["test"])
    monkeypatch.setattr(MainWindow, "_initialize_data", lambda self: None)
    monkeypatch.setattr(MainWindow, "_detect_display_profile", lambda self: select_display_profile(1920, 1080))

    window = MainWindow()
    assert window._modrinth_mod_dialog is None
    assert window._curseforge_mod_dialog is None

    modrinth_details: list[tuple] = []
    curseforge_details: list[tuple] = []
    monkeypatch.setattr(window.mods_page, "set_modrinth_project_details", lambda *args: modrinth_details.append(args))
    monkeypatch.setattr(window.mods_page, "set_curseforge_project_details", lambda *args: curseforge_details.append(args))

    window._set_modrinth_project_details("mod", "proj-1", "fabric", {"id": "proj-1"})
    window._set_curseforge_project_details("mod", 123, "fabric", {"id": 123})

    assert len(modrinth_details) == 1
    assert len(curseforge_details) == 1
    assert window._modrinth_mod_dialog is None
    assert window._curseforge_mod_dialog is None


def test_modrinth_mod_installed_does_not_instantiate_mod_manager_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace
    from PySide6.QtWidgets import QApplication, QMessageBox
    from src.gui.display_profile import select_display_profile
    from src.gui.main_window import MainWindow

    _app = QApplication.instance() or QApplication(["test"])
    monkeypatch.setattr(MainWindow, "_initialize_data", lambda self: None)
    monkeypatch.setattr(MainWindow, "_detect_display_profile", lambda self: select_display_profile(1920, 1080))
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    window = MainWindow()
    monkeypatch.setattr(window.mod_controller, "refresh", lambda: None)
    assert window._mod_manager_dialog is None

    fake_result = SimpleNamespace(installed_files=[], warnings=[], manual_downloads=[])
    window._modrinth_mod_installed(fake_result)

    assert window._mod_manager_dialog is None


def test_allowed_modrinth_version_types_without_instantiating_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    from PySide6.QtWidgets import QApplication
    from src.gui.display_profile import select_display_profile
    from src.gui.main_window import MainWindow

    _app = QApplication.instance() or QApplication(["test"])
    monkeypatch.setattr(MainWindow, "_initialize_data", lambda self: None)
    monkeypatch.setattr(MainWindow, "_detect_display_profile", lambda self: select_display_profile(1920, 1080))

    window = MainWindow()
    assert window._modrinth_modpack_dialog is None

    window._cached_gui_settings = {"modrinth_include_beta": True, "modrinth_include_alpha": False}
    types = window._allowed_modrinth_version_types()
    assert types == ("release", "beta")
    assert window._modrinth_modpack_dialog is None

    window._cached_gui_settings = {"modrinth_include_beta": True, "modrinth_include_alpha": True}
    assert window._allowed_modrinth_version_types() == ("release", "beta", "alpha")
    assert window._modrinth_modpack_dialog is None


def test_apply_gui_settings_initial_and_subsequent_calls_use_current_locale(monkeypatch: pytest.MonkeyPatch) -> None:
    from PySide6.QtWidgets import QApplication
    from mcw_core.api.language.language_manager import language_manager
    from src.gui.display_profile import select_display_profile
    from src.gui.main_window import MainWindow

    _app = QApplication.instance() or QApplication(["test"])
    monkeypatch.setattr(MainWindow, "_initialize_data", lambda self: None)
    monkeypatch.setattr(MainWindow, "_detect_display_profile", lambda self: select_display_profile(1920, 1080))

    window = MainWindow()
    monkeypatch.setattr(window.launcher_settings_page, "reload_languages", lambda: None)
    language_manager.set_language(window._session_locale, notify=False)
    assert language_manager.current_locale == window._session_locale

    reload_calls: list[int] = []
    original_reload = language_manager.reload
    monkeypatch.setattr(language_manager, "reload", lambda: (reload_calls.append(1), original_reload())[1])

    assert window._initial_gui_applied is False
    window._apply_gui_settings(dict(window._startup_settings))
    assert window._initial_gui_applied is True
    assert len(reload_calls) == 0
    window._apply_gui_settings(dict(window._startup_settings))
    assert len(reload_calls) == 1
