from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from src.gui.startup_splash import StartupSplash


def test_startup_splash_updates_progress_and_message(gui_app):
    splash = StartupSplash()

    splash.update_progress(62, "startup.preparing_accounts")

    assert splash.progress_bar.value() == 62
    assert "account" in splash.status_label.text().casefold()
    splash.close()


def test_startup_splash_clamps_progress_and_can_show_failure(gui_app):
    splash = StartupSplash()

    splash.update_progress(999, "startup.ready")
    assert splash.progress_bar.value() == 100

    splash.show_error()
    assert "could not start" in splash.status_label.text().casefold()
    splash.close()


def test_startup_splash_does_not_stay_on_top_or_bottom(gui_app):
    splash = StartupSplash()
    flags = splash.windowFlags()
    assert not bool(flags & Qt.WindowType.WindowStaysOnTopHint)
    assert not bool(flags & Qt.WindowType.WindowStaysOnBottomHint)
    assert (flags & Qt.WindowType.WindowType_Mask) == Qt.WindowType.Window
    assert (flags & Qt.WindowType.WindowType_Mask) != Qt.WindowType.Tool
    splash.close()
