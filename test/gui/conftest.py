from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def gui_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QApplication

    existing = QCoreApplication.instance()
    if existing is not None and not isinstance(existing, QApplication):
        pytest.fail("A QCoreApplication was created before the GUI test QApplication.")

    application = existing or QApplication([])
    yield application
    application.processEvents()
