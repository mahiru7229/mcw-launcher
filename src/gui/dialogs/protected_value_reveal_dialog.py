from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

from src.core.language.language_manager import tr
from src.gui.dialogs.message_box_compat import apply_message_box_compatibility


def confirm_reveal_protected_values(parent: QWidget | None = None, countdown_seconds: int = 5) -> bool:
    """Ask for deliberate confirmation before revealing protected local values."""

    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(tr("curseforge.gateway.reveal.title"))
    box.setText(tr("curseforge.gateway.reveal.message"))
    box.setInformativeText(tr("curseforge.gateway.reveal.details"))
    box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    box.setDefaultButton(QMessageBox.StandardButton.Cancel)
    box.setEscapeButton(QMessageBox.StandardButton.Cancel)
    apply_message_box_compatibility(box)

    reveal_button = box.button(QMessageBox.StandardButton.Ok)
    cancel_button = box.button(QMessageBox.StandardButton.Cancel)
    cancel_button.setText(tr("common.cancel"))

    state = {"remaining": max(0, int(countdown_seconds))}
    timer = QTimer(box)
    timer.setInterval(1000)

    def refresh_button() -> None:
        remaining = state["remaining"]
        if remaining > 0:
            reveal_button.setEnabled(False)
            reveal_button.setText(tr("curseforge.gateway.reveal.countdown", seconds=remaining))
            return
        reveal_button.setText(tr("curseforge.gateway.reveal.confirm"))
        reveal_button.setEnabled(True)
        timer.stop()

    def tick() -> None:
        state["remaining"] = max(0, state["remaining"] - 1)
        refresh_button()

    timer.timeout.connect(tick)
    refresh_button()
    if state["remaining"] > 0:
        timer.start()

    result = box.exec()
    return result == int(QMessageBox.StandardButton.Ok.value)
