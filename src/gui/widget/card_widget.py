from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class CardWidget(QFrame):
    def __init__(self, title: str, subtitle: str = "", object_name: str = "Card") -> None:
        super().__init__()
        self.setObjectName(object_name)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(10)
        self._compact = False
        self.title_label: QLabel | None = None
        self.subtitle_label: QLabel | None = None

        if title:
            self.title_label = QLabel(title)
            self.title_label.setObjectName("CardTitle")
            self.title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.layout.addWidget(self.title_label)

        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("CardSubtitle")
            self.subtitle_label.setWordWrap(True)
            self.subtitle_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.layout.addWidget(self.subtitle_label)

    def set_compact_mode(self, compact: bool) -> None:
        self._compact = bool(compact)
        self.setProperty("compactLayout", self._compact)
        if self._compact:
            self.layout.setContentsMargins(12, 10, 12, 10)
            self.layout.setSpacing(7)
        else:
            self.layout.setContentsMargins(18, 16, 18, 16)
            self.layout.setSpacing(10)
