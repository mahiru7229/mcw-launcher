import os
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from src.gui.display_profile import select_display_profile
from src.gui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_main_window_lazy_dialog_signal_forwarding(app, monkeypatch):
    monkeypatch.setattr(MainWindow, "_initialize_data", lambda self: None)
    monkeypatch.setattr(MainWindow, "_detect_display_profile", lambda self: select_display_profile(1920, 1080))
    window = MainWindow()

    # Mock dialogs to verify they receive signals with multiple arguments
    mock_ftb_dialog = MagicMock()
    mock_atlauncher_dialog = MagicMock()
    mock_content_pack_dialog = MagicMock()
    mock_optifine_dialog = MagicMock()

    window._ftb_modpack_dialog = mock_ftb_dialog
    window._atlauncher_modpack_dialog = mock_atlauncher_dialog
    window._content_pack_manager_dialog = mock_content_pack_dialog
    window._optifine_dialog = mock_optifine_dialog

    # FTB Controller signals
    dummy_ftb_project = object()
    dummy_ftb_versions = (object(),)
    dummy_ftb_version = object()

    window.ftb_controller.project_details_changed.emit(42, dummy_ftb_project)
    mock_ftb_dialog.set_project_details.assert_called_once_with(42, dummy_ftb_project)

    window.ftb_controller.versions_changed.emit(42, dummy_ftb_versions)
    mock_ftb_dialog.set_versions.assert_called_once_with(42, dummy_ftb_versions)

    window.ftb_controller.version_details_changed.emit(42, 100, dummy_ftb_version)
    mock_ftb_dialog.set_version_details.assert_called_once_with(42, 100, dummy_ftb_version)

    # ATLauncher Controller signals
    dummy_atl_project = object()
    dummy_atl_versions = (object(),)
    dummy_atl_version = object()

    window.atlauncher_controller.project_details_changed.emit("safe_pack", dummy_atl_project)
    mock_atlauncher_dialog.set_project_details.assert_called_once_with("safe_pack", dummy_atl_project)

    window.atlauncher_controller.versions_changed.emit("safe_pack", dummy_atl_versions)
    mock_atlauncher_dialog.set_versions.assert_called_once_with("safe_pack", dummy_atl_versions)

    window.atlauncher_controller.version_details_changed.emit("safe_pack", "v1.0", dummy_atl_version)
    mock_atlauncher_dialog.set_version_details.assert_called_once_with("safe_pack", "v1.0", dummy_atl_version)

    # Content Pack Controller signals
    dummy_entries = [object()]
    window.content_pack_controller.entries_changed.emit("instA", "resourcepacks", dummy_entries)
    mock_content_pack_dialog.set_entries.assert_called_once_with("instA", "resourcepacks", dummy_entries)

    # OptiFine Controller signals
    dummy_optifine_state = object()
    window.optifine_controller.state_ready.emit("instB", dummy_optifine_state)
    mock_optifine_dialog.set_state.assert_called_once_with("instB", dummy_optifine_state)
