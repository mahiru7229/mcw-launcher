from __future__ import annotations

from PySide6.QtCore import Property, QSize, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QStyle, QVBoxLayout

from src.core.language.language_manager import tr
from src.gui.config import DEVELOPER_NAME, LAUNCHER_NAME, NAVIGATION_ITEMS
from src.gui.theme.runtime import set_theme_icon, set_theme_pixmap
from src.gui.widget.separator import Separator


class SidebarWidget(QFrame):
    page_requested = Signal(str)
    collapse_requested = Signal(bool)

    def __init__(self, compact: bool = False) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self._compact = bool(compact)
        self._collapsed = False
        self.setProperty("compactLayout", self._compact)
        self._buttons: dict[str, QPushButton] = {}
        self._button_labels: dict[str, str] = {}
        self._dirty_pages: set[str] = set()
        self._decorative_widgets: list[QFrame] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        if self._compact:
            layout.setContentsMargins(10, 12, 10, 10)
            layout.setSpacing(4)
        else:
            layout.setContentsMargins(14, 14, 14, 18)
            layout.setSpacing(8)

        self._toggle_button = QPushButton()
        self._toggle_button.setObjectName("SidebarToggleButton")
        self._toggle_button.setFixedHeight(36)
        self._toggle_button.setIconSize(QSize(22, 22))
        self._toggle_button.setVisible(not self._compact)
        self._toggle_button.clicked.connect(lambda: self.collapse_requested.emit(not self._collapsed))
        layout.addWidget(self._toggle_button)

        logo_width, logo_height = ((156, 58) if self._compact else (192, 72))
        self._logo = set_theme_pixmap(QLabel(), "logo.sidebar", logo_width, logo_height)
        layout.addWidget(self._logo)

        self._brand = QLabel("MCW LAUNCHER")
        self._brand.setObjectName("BrandLabel")
        self._brand.setProperty("compactLayout", self._compact)
        self._version = QLabel(LAUNCHER_NAME.replace("MCW LAUNCHER ", ""))
        self._version.setObjectName("VersionLabel")
        layout.addWidget(self._brand)
        layout.addWidget(self._version)
        layout.addSpacing(6 if self._compact else 14)
        main_separator = Separator()
        self._decorative_widgets.append(main_separator)
        layout.addWidget(main_separator)
        layout.addSpacing(4 if self._compact else 8)

        for page_id, label in NAVIGATION_ITEMS:
            if page_id in {"instances", "launcher_settings", "about"}:
                layout.addSpacing(2)
                separator = Separator("#2f352a", 2)
                self._decorative_widgets.append(separator)
                layout.addWidget(separator)
                layout.addSpacing(2)
            button = set_theme_icon(QPushButton(label), f"icon.nav.{page_id}", 22 if self._compact else 28)
            button.setObjectName("NavButton")
            button.setProperty("compactLayout", self._compact)
            button.setCheckable(True)
            button.setFixedHeight(38 if self._compact else 46)
            button.clicked.connect(lambda _checked=False, current_page=page_id: self.page_requested.emit(current_page))
            self._buttons[page_id] = button
            self._button_labels[page_id] = label
            layout.addWidget(button)

        layout.addStretch()
        self._footer = QLabel(f"Dev by {DEVELOPER_NAME}\nPNG theme assets fall back safely when missing.")
        self._footer.setObjectName("TinyLabel")
        self._footer.setWordWrap(True)
        self._footer.setVisible(not self._compact)
        self._footer_separator = Separator()
        self._footer_separator.setVisible(not self._compact)
        layout.addWidget(self._footer_separator)
        if not self._compact:
            layout.addSpacing(8)
        layout.addWidget(self._footer)
        self.set_collapsed_visual(False)

    def set_current_page(self, page_id: str) -> None:
        for current_id, button in self._buttons.items():
            button.setChecked(current_id == page_id)

    def set_page_dirty(self, page_id: str, dirty: bool) -> None:
        button = self._buttons.get(page_id)
        if button is None:
            return
        if dirty:
            self._dirty_pages.add(page_id)
        else:
            self._dirty_pages.discard(page_id)
        button.setProperty("unsavedChanges", bool(dirty))
        button.setText(self._button_text(page_id))
        button.style().unpolish(button)
        button.style().polish(button)

    def set_collapsed_visual(self, collapsed: bool) -> None:
        self._collapsed = bool(collapsed) and not self._compact
        if self._compact:
            for widget in (self._logo, self._brand, self._version, *self._decorative_widgets):
                widget.setVisible(True)
            self._footer.setVisible(False)
            self._footer_separator.setVisible(False)
        else:
            show_details = not self._collapsed
            for widget in (self._logo, self._brand, self._version, self._footer, self._footer_separator, *self._decorative_widgets):
                widget.setVisible(show_details)
        for page_id, button in self._buttons.items():
            button.setText(self._button_text(page_id))
            button.setToolTip(self._button_labels.get(page_id, "") if self._collapsed else "")
        arrow = QStyle.StandardPixmap.SP_ArrowRight if self._collapsed else QStyle.StandardPixmap.SP_ArrowLeft
        self._toggle_button.setText("")
        self._toggle_button.setIcon(self.style().standardIcon(arrow))
        self._toggle_button.setToolTip(tr("motion.sidebar.expand" if self._collapsed else "motion.sidebar.collapse"))
        self._toggle_button.setAccessibleName(self._toggle_button.toolTip())

    def retranslate_dynamic(self) -> None:
        self.set_collapsed_visual(self._collapsed)

    def _button_text(self, page_id: str) -> str:
        if self._collapsed:
            return ""
        label = self._button_labels.get(page_id, "")
        return f"● {label}" if page_id in self._dirty_pages else label

    def _get_animated_width(self) -> int:
        return self.width()

    def _set_animated_width(self, width: int) -> None:
        normalized = max(1, int(width))
        self.setMinimumWidth(normalized)
        self.setMaximumWidth(normalized)

    animatedWidth = Property(int, _get_animated_width, _set_animated_width)
