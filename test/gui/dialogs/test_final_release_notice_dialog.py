from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from src.config import MCW_DOWNLOAD_PAGE_URL
from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.gui.dialogs.final_release_notice_dialog import FinalReleaseNoticeDialog


def test_final_release_notice_should_show_flag() -> None:
    assert FinalReleaseNoticeDialog.should_show({}) is True
    assert FinalReleaseNoticeDialog.should_show({"updates": {"dismiss_final_release_notice": False}}) is True
    assert FinalReleaseNoticeDialog.should_show({"updates": {"dismiss_final_release_notice": True}}) is False


def test_final_release_notice_open_download_url(gui_app, monkeypatch: pytest.MonkeyPatch) -> None:
    opened_urls: list[str] = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened_urls.append(QUrl(url).toString()) or True)

    dialog = FinalReleaseNoticeDialog()
    dialog.dont_show_checkbox.setChecked(True)
    dialog.open_download_button.click()

    assert opened_urls == [MCW_DOWNLOAD_PAGE_URL]
    assert dialog.decision == FinalReleaseNoticeDialog.OPEN_DOWNLOAD
    assert dialog.should_dismiss_forever is True


def test_final_release_notice_dont_show_button(gui_app) -> None:
    dialog = FinalReleaseNoticeDialog()
    dialog.dont_show_button.click()

    assert dialog.decision == FinalReleaseNoticeDialog.DONT_SHOW_AGAIN
    assert dialog.should_dismiss_forever is True


def test_final_release_notice_show_if_needed_persists_dismissal(
    gui_app,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = LauncherSettingsManager(tmp_path / "launcher_settings.json")
    initial = manager.load()
    assert FinalReleaseNoticeDialog.should_show(initial) is True

    def _fake_exec(self) -> int:
        self._on_dont_show_clicked()
        return 0

    monkeypatch.setattr(FinalReleaseNoticeDialog, "exec", _fake_exec)

    updated = FinalReleaseNoticeDialog.show_if_needed(initial, settings_manager=manager)
    assert updated is True

    reloaded = manager.load()
    assert reloaded["updates"]["dismiss_final_release_notice"] is True
    assert FinalReleaseNoticeDialog.should_show(reloaded) is False

    # Subsequent calls should not show the dialog again.
    monkeypatch.setattr(FinalReleaseNoticeDialog, "exec", lambda _self: (_ for _ in ()).throw(AssertionError("Should not exec")))
    assert FinalReleaseNoticeDialog.show_if_needed(reloaded, settings_manager=manager) is False
