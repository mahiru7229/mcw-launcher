from __future__ import annotations

from weakref import WeakKeyDictionary

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QApplication, QComboBox


class AdaptiveComboBoxManager(QObject):
    """Keep every combo box readable without allowing it to break layouts."""

    DEFAULT_MINIMUM_WIDTH = 92
    DEFAULT_MAXIMUM_WIDTH = 480
    TEXT_CHROME_WIDTH = 48
    POPUP_CHROME_WIDTH = 40

    def __init__(self, application: QApplication) -> None:
        super().__init__(application)
        self._configured: WeakKeyDictionary[QComboBox, bool] = WeakKeyDictionary()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QComboBox) and event.type() in {
            QEvent.Type.Polish,
            QEvent.Type.Show,
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.LanguageChange,
            QEvent.Type.LayoutRequest,
        }:
            self.configure(watched)
            QTimer.singleShot(0, lambda combo=watched: self.refresh(combo))
        return False

    def configure(self, combo: QComboBox) -> None:
        if combo in self._configured:
            return
        self._configured[combo] = True
        combo.currentTextChanged.connect(lambda _text, target=combo: self.refresh(target))
        model = combo.model()
        model.rowsInserted.connect(lambda *_args, target=combo: self.refresh(target))
        model.rowsRemoved.connect(lambda *_args, target=combo: self.refresh(target))
        model.modelReset.connect(lambda target=combo: self.refresh(target))
        model.dataChanged.connect(lambda *_args, target=combo: self.refresh(target))

    def refresh(self, combo: QComboBox) -> None:
        if combo is None:
            return
        self.configure(combo)
        minimum = self._property_int(combo, "mcwAdaptiveMinWidth", self.DEFAULT_MINIMUM_WIDTH)
        maximum = self._property_int(combo, "mcwAdaptiveMaxWidth", self.DEFAULT_MAXIMUM_WIDTH)
        maximum = max(minimum, self._available_maximum(combo, maximum))

        text = combo.currentText() or combo.placeholderText() or " "
        text_width = combo.fontMetrics().horizontalAdvance(text)
        current_index = combo.currentIndex()
        current_icon = combo.itemIcon(current_index) if current_index >= 0 else None
        icon_width = (
            combo.iconSize().width() + 8
            if current_icon is not None and not current_icon.isNull()
            else 0
        )
        unbounded = text_width + icon_width + self.TEXT_CHROME_WIDTH
        desired = max(minimum, min(maximum, unbounded))

        if combo.minimumWidth() != desired or combo.maximumWidth() != desired:
            combo.setMinimumWidth(desired)
            combo.setMaximumWidth(desired)
            combo.resize(desired, combo.height())
            combo.updateGeometry()
        self._update_tooltip(combo, text, unbounded > maximum)
        self._resize_popup(combo, minimum, maximum)

    @classmethod
    def _resize_popup(cls, combo: QComboBox, minimum: int, maximum: int) -> None:
        metrics = combo.fontMetrics()
        longest = max(
            (metrics.horizontalAdvance(combo.itemText(index)) for index in range(combo.count())),
            default=0,
        )
        popup_width = max(combo.width(), minimum, min(maximum, longest + cls.POPUP_CHROME_WIDTH))
        view = combo.view()
        if view.minimumWidth() != popup_width:
            view.setMinimumWidth(popup_width)
        if view.maximumWidth() != maximum:
            view.setMaximumWidth(maximum)

    @staticmethod
    def _property_int(combo: QComboBox, name: str, fallback: int) -> int:
        value = combo.property(name)
        try:
            return max(1, int(value)) if value is not None else fallback
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _available_maximum(combo: QComboBox, requested: int) -> int:
        limits = [requested]
        parent = combo.parentWidget()
        if parent is not None and parent.width() > 120:
            limits.append(max(92, parent.width() - 24))
        screen = combo.screen() or QApplication.primaryScreen()
        if screen is not None:
            limits.append(max(92, int(screen.availableGeometry().width() * 0.8)))
        return min(limits)

    @staticmethod
    def _update_tooltip(combo: QComboBox, text: str, truncated: bool) -> None:
        owns_tooltip = bool(combo.property("_mcwAdaptiveTooltip"))
        if truncated and (not combo.toolTip() or owns_tooltip):
            combo.setToolTip(text)
            combo.setProperty("_mcwAdaptiveTooltip", True)
        elif not truncated and owns_tooltip:
            combo.setToolTip("")
            combo.setProperty("_mcwAdaptiveTooltip", False)


def install_adaptive_combo_boxes(application: QApplication) -> AdaptiveComboBoxManager:
    existing = getattr(application, "_adaptive_combo_box_manager", None)
    if isinstance(existing, AdaptiveComboBoxManager):
        return existing
    manager = AdaptiveComboBoxManager(application)
    application.installEventFilter(manager)
    application._adaptive_combo_box_manager = manager
    return manager
