from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QAbstractButton, QComboBox, QGroupBox, QLabel, QLineEdit, QPlainTextEdit, QTabWidget, QTableWidget, QTextEdit, QWidget

from src.core.language.language_manager import tr

_SOURCE_TEXT_PROPERTY = "mcw_i18n_source_text"
_LAST_TEXT_PROPERTY = "mcw_i18n_last_text"
_SOURCE_TITLE_PROPERTY = "mcw_i18n_source_title"
_LAST_TITLE_PROPERTY = "mcw_i18n_last_title"
_SOURCE_PLACEHOLDER_PROPERTY = "mcw_i18n_source_placeholder"
_LAST_PLACEHOLDER_PROPERTY = "mcw_i18n_last_placeholder"
_SOURCE_TOOLTIP_PROPERTY = "mcw_i18n_source_tooltip"
_LAST_TOOLTIP_PROPERTY = "mcw_i18n_last_tooltip"
_ITEM_SOURCE_ROLE = int(Qt.ItemDataRole.UserRole) + 117
_ITEM_LAST_ROLE = int(Qt.ItemDataRole.UserRole) + 118


def retranslate_widget_tree(root: QWidget) -> None:
    widgets = [root, *root.findChildren(QWidget)]
    for widget in widgets:
        _translate_widget(widget)
        for action in widget.findChildren(QAction, options=Qt.FindChildOption.FindDirectChildrenOnly):
            _translate_action(action)


def _can_replace(current: str, source: str, last: object) -> bool:
    return last is None or current == source or current == str(last)


def _translate_widget(widget: QWidget) -> None:
    title = widget.windowTitle()
    if title:
        source = widget.property(_SOURCE_TITLE_PROPERTY)
        if source is None:
            source = title
            widget.setProperty(_SOURCE_TITLE_PROPERTY, source)
        last = widget.property(_LAST_TITLE_PROPERTY)
        if _can_replace(title, str(source), last):
            translated = tr(str(source))
            widget.setWindowTitle(translated)
            widget.setProperty(_LAST_TITLE_PROPERTY, translated)

    if isinstance(widget, (QLabel, QAbstractButton)):
        _translate_text_property(widget)
    elif isinstance(widget, QGroupBox):
        source = widget.property(_SOURCE_TITLE_PROPERTY)
        if source is None:
            source = widget.title()
            widget.setProperty(_SOURCE_TITLE_PROPERTY, source)
        last = widget.property(_LAST_TITLE_PROPERTY)
        if _can_replace(widget.title(), str(source), last):
            translated = tr(str(source))
            widget.setTitle(translated)
            widget.setProperty(_LAST_TITLE_PROPERTY, translated)

    if isinstance(widget, (QLineEdit, QPlainTextEdit, QTextEdit)):
        source = widget.property(_SOURCE_PLACEHOLDER_PROPERTY)
        if source is None:
            source = widget.placeholderText()
            widget.setProperty(_SOURCE_PLACEHOLDER_PROPERTY, source)
        last = widget.property(_LAST_PLACEHOLDER_PROPERTY)
        current = widget.placeholderText()
        if source and _can_replace(current, str(source), last):
            translated = tr(str(source))
            widget.setPlaceholderText(translated)
            widget.setProperty(_LAST_PLACEHOLDER_PROPERTY, translated)

    if isinstance(widget, QComboBox):
        for index in range(widget.count()):
            source = widget.itemData(index, _ITEM_SOURCE_ROLE)
            if source is None:
                source = widget.itemText(index)
                widget.setItemData(index, source, _ITEM_SOURCE_ROLE)
            last = widget.itemData(index, _ITEM_LAST_ROLE)
            current = widget.itemText(index)
            if _can_replace(current, str(source), last):
                translated = tr(str(source))
                widget.setItemText(index, translated)
                widget.setItemData(index, translated, _ITEM_LAST_ROLE)

    if isinstance(widget, QTabWidget):
        for index in range(widget.count()):
            source = widget.tabBar().tabData(index)
            if not isinstance(source, str):
                source = widget.tabText(index)
                widget.tabBar().setTabData(index, source)
            widget.setTabText(index, tr(source))

    if isinstance(widget, QTableWidget):
        for column in range(widget.columnCount()):
            item = widget.horizontalHeaderItem(column)
            if item is None:
                continue
            source = item.data(_ITEM_SOURCE_ROLE)
            if source is None:
                source = item.text()
                item.setData(_ITEM_SOURCE_ROLE, source)
            last = item.data(_ITEM_LAST_ROLE)
            if _can_replace(item.text(), str(source), last):
                translated = tr(str(source))
                item.setText(translated)
                item.setData(_ITEM_LAST_ROLE, translated)

    tooltip = widget.toolTip()
    if tooltip:
        source = widget.property(_SOURCE_TOOLTIP_PROPERTY)
        if source is None:
            source = tooltip
            widget.setProperty(_SOURCE_TOOLTIP_PROPERTY, source)
        last = widget.property(_LAST_TOOLTIP_PROPERTY)
        if _can_replace(tooltip, str(source), last):
            translated = tr(str(source))
            widget.setToolTip(translated)
            widget.setProperty(_LAST_TOOLTIP_PROPERTY, translated)


def _translate_text_property(widget: QLabel | QAbstractButton) -> None:
    source = widget.property(_SOURCE_TEXT_PROPERTY)
    if source is None:
        source = widget.text()
        widget.setProperty(_SOURCE_TEXT_PROPERTY, source)
    last = widget.property(_LAST_TEXT_PROPERTY)
    current = widget.text()
    if source and _can_replace(current, str(source), last):
        translated = tr(str(source))
        widget.setText(translated)
        widget.setProperty(_LAST_TEXT_PROPERTY, translated)


def _translate_action(action: QAction) -> None:
    source = action.property(_SOURCE_TEXT_PROPERTY)
    if source is None:
        source = action.text()
        action.setProperty(_SOURCE_TEXT_PROPERTY, source)
    last = action.property(_LAST_TEXT_PROPERTY)
    if source and _can_replace(action.text(), str(source), last):
        translated = tr(str(source))
        action.setText(translated)
        action.setProperty(_LAST_TEXT_PROPERTY, translated)
