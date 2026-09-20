from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget


class ElidedLabel(QLabel):
    """A QLabel that automatically elides overflowing text with ellipsis

    and preserves the full text in text() and tooltip.
    """

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = str(text or "")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(60)
        self._update_elided()

    def setText(self, text: str) -> None:
        self._full_text = str(text or "")
        self.setToolTip(self._full_text)
        self._update_elided()

    def text(self) -> str:
        return self._full_text

    def full_text(self) -> str:
        return self._full_text

    def resizeEvent(self, event: object) -> None:
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self) -> None:
        if not self._full_text:
            if super().text():
                super().setText("")
            return
        metrics = self.fontMetrics()
        w = max(0, self.width() - 4)
        if w <= 0:
            w = max(self.minimumWidth(), 200)
        elided = metrics.elidedText(self._full_text, Qt.TextElideMode.ElideRight, w)
        if super().text() != elided:
            super().setText(elided)
