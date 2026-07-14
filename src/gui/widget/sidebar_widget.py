from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QFrame

from src.gui.config import DEVELOPER_NAME, LAUNCHER_NAME, NAVIGATION_ITEMS
from src.gui.widget.separator import Separator
from src.gui.theme.runtime import set_theme_icon, set_theme_pixmap


class SidebarWidget(QFrame):
    page_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self._buttons: dict[str, QPushButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 22, 14, 18)
        layout.setSpacing(8)

        logo = set_theme_pixmap(QLabel(), "logo.sidebar", 192, 72)
        layout.addWidget(logo)

        brand = QLabel("MCW LAUNCHER")
        brand.setObjectName("BrandLabel")
        version = QLabel(LAUNCHER_NAME.replace("MCW LAUNCHER ", ""))
        version.setObjectName("VersionLabel")
        layout.addWidget(brand)
        layout.addWidget(version)
        layout.addSpacing(14)
        layout.addWidget(Separator())
        layout.addSpacing(8)

        for index, (page_id, label) in enumerate(NAVIGATION_ITEMS):
            if index in {2, 4, 6}:
                layout.addSpacing(2)
                layout.addWidget(Separator("#2f352a", 2))
                layout.addSpacing(2)
            button = set_theme_icon(QPushButton(label), f"icon.nav.{page_id}", 28)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setFixedHeight(46)
            button.clicked.connect(lambda _checked=False, current_page=page_id: self.page_requested.emit(current_page))
            self._buttons[page_id] = button
            layout.addWidget(button)

        layout.addStretch()
        footer = QLabel(f"Dev by {DEVELOPER_NAME}\nPNG theme assets fall back safely when missing.")
        footer.setObjectName("TinyLabel")
        footer.setWordWrap(True)
        layout.addWidget(Separator())
        layout.addSpacing(8)
        layout.addWidget(footer)

    def set_current_page(self, page_id: str) -> None:
        for current_id, button in self._buttons.items():
            button.setChecked(current_id == page_id)
