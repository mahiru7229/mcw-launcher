from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.pages.account_page import AccountPage
from src.models.account.account import Account
from src.models.account.account_source import AccountSource


def test_account_combo_switches_immediately_without_confirmation(gui_app) -> None:
    page = AccountPage()
    first = Account("first", AccountSource.OFFLINE, "First", "1" * 32)
    second = Account("second", AccountSource.OFFLINE, "Second", "2" * 32)
    emitted: list[str] = []
    page.select_requested.connect(emitted.append)

    page.set_accounts([first, second], first.account_id)
    assert emitted == []

    page.account_combo.setCurrentIndex(1)

    assert emitted == [second.account_id]
    assert "Second" in page.selection_status.text()
