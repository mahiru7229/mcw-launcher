from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLayout, QScrollArea, QWidget


def scrollable_page(content: QWidget, *, object_name: str = "") -> QScrollArea:
    """Keep a page at its natural minimum size and scroll when space is tight."""
    layout = content.layout()
    if isinstance(layout, QLayout):
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

    scroll = QScrollArea()
    if object_name:
        scroll.setObjectName(object_name)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(content)
    return scroll
