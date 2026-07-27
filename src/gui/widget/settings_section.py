from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget


class SettingsSection(QFrame):
    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__()
        self.setObjectName("SettingsSection")
        self._compact = False
        self._next_index = 0

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 4, 0, 4)
        self.layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("SectionTitle")
        self.layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("SectionSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setVisible(bool(subtitle))
        self.layout.addWidget(self.subtitle_label)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.layout.addLayout(self.grid)

    def add_card(self, card: QWidget, span: int = 1) -> None:
        requested_span = 2 if int(span) >= 2 else 1
        card.setProperty("settingsSectionSpan", requested_span)
        self._place_card(card, requested_span)

    def set_compact_mode(self, compact: bool) -> None:
        compact = bool(compact)
        if compact == self._compact:
            return
        self._compact = compact
        self.setProperty("compactLayout", compact)
        self.layout.setSpacing(7 if compact else 10)
        self.grid.setHorizontalSpacing(0 if compact else 14)
        self.grid.setVerticalSpacing(10 if compact else 14)
        self._reflow()

    def _place_card(self, card: QWidget, requested_span: int) -> None:
        if self._compact:
            row = self._next_index
            self.grid.addWidget(card, row, 0, 1, 2)
            self._next_index += 1
            return

        if requested_span == 2:
            row = (self._next_index + 1) // 2
            if self._next_index % 2:
                self._next_index += 1
                row = self._next_index // 2
            self.grid.addWidget(card, row, 0, 1, 2)
            self._next_index += 2
            return

        row, column = divmod(self._next_index, 2)
        self.grid.addWidget(card, row, column)
        self._next_index += 1

    def _reflow(self) -> None:
        cards: list[tuple[QWidget, int]] = []
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                cards.append((widget, int(widget.property("settingsSectionSpan") or 1)))
        self._next_index = 0
        for card, span in cards:
            self._place_card(card, span)
