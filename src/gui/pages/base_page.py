from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from src.gui.widget.card_widget import CardWidget
from src.gui.widget.settings_section import SettingsSection
from src.gui.widget.wheel_guard import prevent_wheel_value_changes


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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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
        self._floating_action_bar: QWidget | None = None

        self.title_label = QLabel(title)
        self.title_label.setObjectName("PageTitle")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("PageSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.root_layout.addWidget(self.title_label)
        self.root_layout.addWidget(self.subtitle_label)

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

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not getattr(self, "_wheel_guard_installed", False):
            self._wheel_guard_installed = True
            prevent_wheel_value_changes(self)
        self._sync_busy_overlay_geometry()
        QTimer.singleShot(0, self._sync_busy_overlay_geometry)

    def install_floating_action_bar(self, bar: QWidget) -> None:
        self._floating_action_bar = bar
        bar.setParent(self.viewport())
        bar.installEventFilter(self)
        bar.show()
        bar.raise_()
        self._apply_root_margins()
        self._sync_busy_overlay_geometry()

    def eventFilter(self, watched, event) -> bool:
        if watched is getattr(self, "_floating_action_bar", None) and event.type() in (
            QEvent.Type.LayoutRequest,
            QEvent.Type.PolishRequest,
            QEvent.Type.StyleChange,
        ):
            if not getattr(self, "_syncing_floating_bar", False):
                self._sync_busy_overlay_geometry()
        return super().eventFilter(watched, event)

    def _apply_root_margins(self) -> None:
        if getattr(self, "_floating_action_bar", None) is not None:
            bottom_margin = 84 if self._compact else 96
        else:
            bottom_margin = 14 if self._compact else 24
        if self._compact:
            self.root_layout.setContentsMargins(18, 14, 18, bottom_margin)
            self.root_layout.setSpacing(12)
        else:
            self.root_layout.setContentsMargins(28, 24, 28, bottom_margin)
            self.root_layout.setSpacing(18)

    def _sync_busy_overlay_geometry(self) -> None:
        vp_rect = self.viewport().rect()
        if getattr(self, "_floating_action_bar", None) is not None:
            self._syncing_floating_bar = True
            try:
                margin = 12 if self._compact else 16
                bar_width = max(260, vp_rect.width() - margin * 2)
                layout = self._floating_action_bar.layout()
                if layout is not None:
                    layout.invalidate()
                    layout.activate()
                hint_height = self._floating_action_bar.sizeHint().height()
                hfw = self._floating_action_bar.heightForWidth(bar_width)
                if hfw <= 0 and layout is not None and layout.hasHeightForWidth():
                    hfw = layout.totalHeightForWidth(bar_width)
                bar_height = max(60, hint_height, hfw)
                self._floating_action_bar.setGeometry(
                    margin,
                    max(margin, vp_rect.height() - bar_height - margin),
                    bar_width,
                    bar_height,
                )
                self._floating_action_bar.raise_()
            finally:
                self._syncing_floating_bar = False
        if hasattr(self, "_busy_overlay"):
            self._busy_overlay.setGeometry(vp_rect)
            if self._interaction_locked:
                self._busy_overlay.raise_()

    def set_compact_mode(self, compact: bool) -> None:
        self._compact = bool(compact)
        self.page_viewport.setProperty("compactLayout", self._compact)
        self._apply_root_margins()

        for section in self.findChildren(SettingsSection):
            section.set_compact_mode(self._compact)
        for card in self.findChildren(CardWidget):
            card.set_compact_mode(self._compact)

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        self._refresh_scrolled_widgets()

    def wheelEvent(self, event) -> None:
        super().wheelEvent(event)
        self._refresh_scrolled_widgets()

    def _refresh_scrolled_widgets(self) -> None:
        """Invalidate stale child regions after scrolling on Windows.

        Qt's backing store can occasionally leave stylesheet-rendered buttons in
        an old scroll region until hover triggers a repaint.  Updating the
        viewport immediately and the buttons once more on the next event-loop
        tick keeps their normal state visible without rebuilding the page.
        """
        self.viewport().update()
        self.page_viewport.update()
        if getattr(self, "_floating_action_bar", None) is not None:
            self._floating_action_bar.raise_()
            self._floating_action_bar.update()
        buttons = tuple(self.page_viewport.findChildren(QPushButton))
        for button in buttons:
            button.update()
        QTimer.singleShot(0, lambda controls=buttons: self._update_controls(controls))

    @staticmethod
    def _update_controls(controls: tuple[QPushButton, ...]) -> None:
        for control in controls:
            if control is not None:
                control.update()

