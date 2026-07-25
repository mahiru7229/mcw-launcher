import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from src.core.language.language_manager import language_manager, tr
from src.gui.dialogs.protected_value_reveal_dialog import confirm_reveal_protected_values


def test_reveal_dialog_uses_localized_five_second_gate(gui_app, monkeypatch):
    language_manager.set_language("vi-VN", notify=False)
    captured = {}

    def fake_exec(box):
        reveal = box.button(QMessageBox.StandardButton.Ok)
        cancel = box.button(QMessageBox.StandardButton.Cancel)
        captured["title"] = box.windowTitle()
        captured["message"] = box.text()
        captured["reveal_text"] = reveal.text()
        captured["reveal_enabled"] = reveal.isEnabled()
        captured["cancel_text"] = cancel.text()
        return int(QMessageBox.StandardButton.Cancel)

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)

    assert confirm_reveal_protected_values(countdown_seconds=5) is False
    assert captured["title"] == tr("curseforge.gateway.reveal.title")
    assert captured["message"] == tr("curseforge.gateway.reveal.message")
    assert captured["reveal_text"] == tr("curseforge.gateway.reveal.countdown", seconds=5)
    assert captured["reveal_enabled"] is False
    assert captured["cancel_text"] == tr("common.cancel")

    language_manager.set_language("en-US", notify=False)
