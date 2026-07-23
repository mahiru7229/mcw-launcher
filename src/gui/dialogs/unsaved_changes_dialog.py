from __future__ import annotations

from enum import Enum

from PySide6.QtWidgets import QMessageBox, QWidget

from src.core.language.language_manager import tr


class UnsavedChangesDecision(Enum):
    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"


def prompt_unsaved_changes(parent: QWidget | None, scope: str) -> UnsavedChangesDecision:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(tr("settings.unsaved.title"))
    box.setText(tr("settings.unsaved.message", scope=scope))
    box.setInformativeText(tr("settings.unsaved.detail"))
    box.setStandardButtons(
        QMessageBox.StandardButton.Save
        | QMessageBox.StandardButton.Discard
        | QMessageBox.StandardButton.Cancel
    )
    box.setDefaultButton(QMessageBox.StandardButton.Save)
    box.setEscapeButton(QMessageBox.StandardButton.Cancel)

    result = box.exec()
    if result == QMessageBox.StandardButton.Save:
        return UnsavedChangesDecision.SAVE
    if result == QMessageBox.StandardButton.Discard:
        return UnsavedChangesDecision.DISCARD
    return UnsavedChangesDecision.CANCEL
