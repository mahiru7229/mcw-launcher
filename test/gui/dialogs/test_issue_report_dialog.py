from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from src.gui.dialogs.issue_report_dialog import IssueReportDialog


def test_issue_report_collects_information_before_guidance(gui_app) -> None:
    dialog = IssueReportDialog("MCW 1.4.0-beta.3; instance=RLCraft")
    submitted = []
    dialog.information_submitted.connect(submitted.append)

    assert dialog.stack.currentIndex() == 0
    dialog.prefill(title="Forge failed", what_happened="Runtime missing")
    dialog.steps_edit.setPlainText("1. Launch")
    dialog._submit_information()

    assert submitted[0]["title"] == "Forge failed"
    assert dialog.stack.currentIndex() == 0

    dialog.show_guidance(
        __import__("pathlib").Path("MCW-Diagnostics.zip"),
        "issue body",
        "https://github.com/mahiru7229/mcw-launcher/issues/new",
    )
    assert dialog.stack.currentIndex() == 1
    assert dialog.preview.toPlainText() == "issue body"
