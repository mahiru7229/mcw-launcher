from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from src.gui.widget.card_widget import CardWidget
from src.gui.widget.settings_section import SettingsSection


class _BusyPageOverlay(QWidget):
    def __init__(self, page: QScrollArea) -> None:
        super().__init__(page.viewport())
        self._page = page
        self.setObjectName("BusyPageOverlay")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.BusyCursor)
        self.setStyleSheet("background-color: rgba(12, 14, 12, 42);")
        self.hide()

    def wheelEvent(self, event) -> None:
        bar = self._page.verticalScrollBar()
        pixel_delta = event.pixelDelta().y()
        if pixel_delta:
            distance = int(pixel_delta)
        else:
            steps = event.angleDelta().y() / 120.0
            distance = int(round(steps * max(1, bar.singleStep()) * 3))
        if distance:
            bar.setValue(bar.value() - distance)
        event.accept()

    def mousePressEvent(self, event) -> None:
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        event.accept()

    def contextMenuEvent(self, event) -> None:
        event.accept()

    def keyPressEvent(self, event) -> None:
        event.accept()

    def keyReleaseEvent(self, event) -> None:
        event.accept()

    def focusNextPrevChild(self, _next: bool) -> bool:
        return True


class BasePage(QScrollArea):
    def __init__(self, title: str, subtitle: str, page_id: str = "generic") -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        page = QWidget()
        page.setObjectName("PageViewport")
        page.setProperty("themePage", str(page_id))
        self.setWidget(page)
        self.page_viewport = page
        self.root_layout = QVBoxLayout(page)
        self.root_layout.setContentsMargins(28, 24, 28, 24)
        self.root_layout.setSpacing(18)
        self._compact = False
        self._interaction_locked = False
        self._busy_overlay = _BusyPageOverlay(self)

        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setWordWrap(True)
        self.root_layout.addWidget(title_label)
        self.root_layout.addWidget(subtitle_label)

    @property
    def interaction_locked(self) -> bool:
        return self._interaction_locked

    def set_interaction_locked(self, locked: bool) -> None:
        self._interaction_locked = bool(locked)
        self._sync_busy_overlay_geometry()
        self._busy_overlay.setVisible(self._interaction_locked)
        if self._interaction_locked:
            self._busy_overlay.raise_()
            self._busy_overlay.setFocus(Qt.FocusReason.OtherFocusReason)
        else:
            self._busy_overlay.clearFocus()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_busy_overlay_geometry()

    def _sync_busy_overlay_geometry(self) -> None:
        if hasattr(self, "_busy_overlay"):
            self._busy_overlay.setGeometry(self.viewport().rect())

    def set_compact_mode(self, compact: bool) -> None:
        self._compact = bool(compact)
        self.page_viewport.setProperty("compactLayout", self._compact)
        if self._compact:
            self.root_layout.setContentsMargins(18, 14, 18, 14)
            self.root_layout.setSpacing(12)
        else:
            self.root_layout.setContentsMargins(28, 24, 28, 24)
            self.root_layout.setSpacing(18)

        for section in self.findChildren(SettingsSection):
            section.set_compact_mode(self._compact)
        for card in self.findChildren(CardWidget):
            card.set_compact_mode(self._compact)
