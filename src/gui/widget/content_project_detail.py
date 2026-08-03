from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from html import escape

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget

from mcw_core.api.language.language_manager import tr
from src.gui.media.remote_image_cache import RemoteImageCache
from src.gui.media.safe_rich_text import safe_external_url, sanitize_html


class SafeTextBrowser(QTextBrowser):
    """Display provider descriptions without silently loading remote resources."""

    def loadResource(self, resource_type: int, url: QUrl) -> object:
        if url.scheme().casefold() in {"http", "https"}:
            return None
        return super().loadResource(resource_type, url)


class ContentProjectDetailPanel(QFrame):
    """Provider-neutral project details used by content browser dialogs."""

    ICON_SIZE = QSize(88, 88)
    PREVIEW_SIZE = QSize(420, 160)
    MINIMUM_PANEL_WIDTH = 500
    MAX_TITLE_CHARACTERS = 160
    MAX_AUTHOR_ITEMS = 5
    MAX_AUTHOR_CHARACTERS = 120
    MAX_SUMMARY_CHARACTERS = 360
    MAX_METADATA_ENTRIES = 8
    MAX_METADATA_SEQUENCE_ITEMS = 8
    MAX_METADATA_VALUE_CHARACTERS = 240

    def __init__(self, image_cache: RemoteImageCache, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ContentProjectDetailPanel")
        self.setMinimumWidth(self.MINIMUM_PANEL_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._image_cache = image_cache
        self._project_token = ""
        self._web_url = ""
        self._show_description = False
        self._legacy_action_row: QHBoxLayout | None = None
        self._build_ui()
        self.clear(tr("content.details.select_project"))

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(9)

        header = QHBoxLayout()
        header.setSpacing(12)
        self.icon_label = QLabel()
        self.icon_label.setObjectName("ContentProjectIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(self.ICON_SIZE)
        self.icon_label.setText(tr("content.icon.placeholder"))

        titles = QVBoxLayout()
        titles.setSpacing(4)
        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.title_label.setMaximumHeight(72)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.provider_label = QLabel()
        self.provider_label.setObjectName("MutedLabel")
        self.provider_label.setWordWrap(True)
        self.provider_label.setMaximumHeight(48)
        self.provider_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        titles.addWidget(self.title_label)
        titles.addWidget(self.provider_label)
        titles.addStretch()

        header.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)
        header.addLayout(titles, 1)
        root.addLayout(header)

        self.body_scroll = QScrollArea()
        self.body_scroll.setObjectName("ContentProjectBodyScroll")
        self.body_scroll.setWidgetResizable(True)
        self.body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(9)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(10)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.summary_label.setMaximumHeight(76)
        self.summary_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.open_web_button = QPushButton()
        self.open_web_button.setEnabled(False)
        self.open_web_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.open_web_button.clicked.connect(self._open_web)
        summary_row.addWidget(self.summary_label, 1)
        summary_row.addWidget(self.open_web_button, 0, Qt.AlignmentFlag.AlignTop)
        body_layout.addLayout(summary_row)

        self.metadata_label = QLabel()
        self.metadata_label.setObjectName("MutedLabel")
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setTextFormat(Qt.TextFormat.RichText)
        self.metadata_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.metadata_label.setMaximumHeight(132)
        self.metadata_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        body_layout.addWidget(self.metadata_label)

        self.preview_label = QLabel()
        self.preview_label.setObjectName("ContentProjectPreview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(100)
        self.preview_label.setMaximumHeight(self.PREVIEW_SIZE.height())
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.preview_label.hide()
        body_layout.addWidget(self.preview_label)

        self.description_browser = SafeTextBrowser()
        self.description_browser.setObjectName("ContentProjectDescription")
        self.description_browser.setOpenExternalLinks(True)
        self.description_browser.setMinimumHeight(130)
        self.description_browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.description_browser.setVisible(self._show_description)
        body_layout.addWidget(self.description_browser, 1)
        body_layout.addStretch()
        self.body_scroll.setWidget(body)
        root.addWidget(self.body_scroll, 1)

        self.status_label = QLabel()
        self.status_label.setObjectName("MutedLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status_label.setMaximumHeight(56)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        root.addWidget(self.status_label)

        self.actions_layout = QVBoxLayout()
        self.actions_layout.setSpacing(8)
        root.addLayout(self.actions_layout)

    def add_action_row(self, *widgets: tuple[QWidget, int]) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        for widget, stretch in widgets:
            row.addWidget(widget, max(0, int(stretch)))
        self.actions_layout.addLayout(row)
        return row

    def add_action_widget(self, widget: QWidget, stretch: int = 0) -> None:
        if self._legacy_action_row is None:
            self._legacy_action_row = QHBoxLayout()
            self._legacy_action_row.setSpacing(8)
            self.actions_layout.addLayout(self._legacy_action_row)
        self._legacy_action_row.addWidget(widget, max(0, int(stretch)))

    def add_action_stretch(self) -> None:
        if self._legacy_action_row is None:
            self._legacy_action_row = QHBoxLayout()
            self._legacy_action_row.setSpacing(8)
            self.actions_layout.addLayout(self._legacy_action_row)
        self._legacy_action_row.addStretch()

    @property
    def description_visible(self) -> bool:
        return self._show_description

    def set_description_visible(self, visible: bool) -> None:
        self._show_description = bool(visible)
        self.description_browser.setVisible(self._show_description)
        self.updateGeometry()

    def set_open_web_text(self, text: str) -> None:
        self.open_web_button.setText(text)

    def clear(self, message: str) -> None:
        self._project_token = ""
        self._web_url = ""
        self.icon_label.setPixmap(QPixmap())
        self.icon_label.setText(tr("content.icon.placeholder"))
        self.title_label.setText(tr("content.details.no_project"))
        self.title_label.setToolTip("")
        self.provider_label.clear()
        self.provider_label.setToolTip("")
        self.summary_label.clear()
        self.summary_label.setToolTip("")
        self.metadata_label.clear()
        self.metadata_label.setToolTip("")
        self.preview_label.clear()
        self.preview_label.hide()
        self.description_browser.clear()
        self.set_status(message)
        self.open_web_button.setEnabled(False)

    def set_loading(self, token: str, provider: str, title: str, author: str, summary: str, icon_url: str, web_url: str, message: str) -> None:
        self.set_project(
            token=token,
            provider=provider,
            title=title,
            author=author,
            summary=summary,
            description=summary,
            icon_url=icon_url,
            web_url=web_url,
            metadata={},
            gallery_urls=(),
            description_format="plain",
            status=message,
        )

    def set_project(
        self,
        *,
        token: str,
        provider: str,
        title: str,
        author: str,
        summary: str,
        description: str,
        icon_url: str,
        web_url: str,
        metadata: Mapping[str, object],
        gallery_urls: Sequence[str] = (),
        description_format: str = "plain",
        status: str = "",
    ) -> None:
        self._project_token = str(token)
        self._web_url = safe_external_url(web_url)
        title_text = str(title or tr("common.unknown")).strip()
        compact_title = self._compact_text(title_text, self.MAX_TITLE_CHARACTERS)
        self.title_label.setText(compact_title)
        self.title_label.setToolTip(self._compact_text(title_text, 600) if title_text != compact_title else "")
        provider_text = str(provider).strip()
        author_text = str(author).strip()
        full_provider_text = " · ".join(item for item in (provider_text, author_text) if item)
        compact_provider_text = " · ".join(item for item in (provider_text, self._compact_people(author_text)) if item)
        summary_text = str(summary or "").strip()
        self.provider_label.setText(compact_provider_text)
        self.provider_label.setToolTip(self._compact_text(full_provider_text, 500) if full_provider_text != compact_provider_text else "")
        self.summary_label.setText(self._compact_text(summary_text, self.MAX_SUMMARY_CHARACTERS))
        self.summary_label.setToolTip(self._compact_text(summary_text, 1200) if len(summary_text) > self.MAX_SUMMARY_CHARACTERS else "")
        self.metadata_label.setText(self._metadata_html(metadata))
        self.metadata_label.setToolTip(self._compact_text(self._metadata_plain_text(metadata), 1500))
        self.set_status(status)
        self.open_web_button.setEnabled(bool(self._web_url))
        self._set_description(description or summary, description_format)
        self._load_icon(icon_url, self._project_token)
        self._load_preview(next((str(url) for url in gallery_urls if str(url).strip()), ""), self._project_token)

    def set_status(self, message: str) -> None:
        text = str(message or "").strip()
        compact = self._compact_text(text, 300)
        self.status_label.setText(compact)
        self.status_label.setToolTip(self._compact_text(text, 1000) if text != compact else "")

    def _set_description(self, description: str, description_format: str) -> None:
        value = str(description or "").strip()
        if not value:
            self.description_browser.setPlainText(tr("content.details.no_description"))
            return
        normalized = str(description_format).strip().casefold()
        if normalized == "markdown":
            self.description_browser.setMarkdown(value)
        elif normalized == "html":
            self.description_browser.setHtml(sanitize_html(value))
        else:
            self.description_browser.setPlainText(value)

    def _load_icon(self, url: str, token: str) -> None:
        self.icon_label.setPixmap(QPixmap())
        self.icon_label.setText(tr("content.icon.placeholder"))
        self._image_cache.request(url, lambda pixmap: self._apply_icon(token, pixmap))

    def _apply_icon(self, token: str, pixmap: QPixmap) -> None:
        if token != self._project_token or pixmap.isNull():
            return
        self.icon_label.setText("")
        self.icon_label.setPixmap(self._image_cache.scaled(pixmap, self.ICON_SIZE))

    def _load_preview(self, url: str, token: str) -> None:
        self.preview_label.clear()
        self.preview_label.hide()
        if url:
            self._image_cache.request(url, lambda pixmap: self._apply_preview(token, pixmap))

    def _apply_preview(self, token: str, pixmap: QPixmap) -> None:
        if token != self._project_token or pixmap.isNull():
            return
        self.preview_label.setPixmap(self._image_cache.scaled(pixmap, self.PREVIEW_SIZE))
        self.preview_label.show()

    def _open_web(self) -> None:
        if self._web_url:
            QDesktopServices.openUrl(QUrl(self._web_url))

    @classmethod
    def _metadata_html(cls, metadata: Mapping[str, object]) -> str:
        parts: list[str] = []
        visible_items = list(metadata.items())[: cls.MAX_METADATA_ENTRIES]
        for label, raw_value in visible_items:
            if raw_value is None or raw_value == "" or raw_value == () or raw_value == [] or raw_value == {}:
                continue
            value = cls._metadata_display_value(raw_value)
            if value:
                parts.append(f"<b>{escape(str(label))}:</b> {escape(value)}")
        remaining = max(0, len(metadata) - len(visible_items))
        if remaining:
            parts.append(escape(f"… (+{remaining})"))
        rows = [" &nbsp;•&nbsp; ".join(parts[index : index + 2]) for index in range(0, len(parts), 2)]
        return "<br>".join(rows)

    @classmethod
    def _metadata_plain_text(cls, metadata: Mapping[str, object]) -> str:
        lines: list[str] = []
        for label, raw_value in metadata.items():
            if raw_value is None or raw_value == "" or raw_value == () or raw_value == [] or raw_value == {}:
                continue
            if isinstance(raw_value, (tuple, list, set)):
                value = ", ".join(str(item).strip() for item in raw_value if str(item).strip())
            else:
                value = str(raw_value).strip()
            if value:
                lines.append(f"{label}: {value}")
        return "\n".join(lines)

    @classmethod
    def _metadata_display_value(cls, raw_value: object) -> str:
        if isinstance(raw_value, (tuple, list, set)):
            values = [str(item).strip() for item in raw_value if str(item).strip()]
            visible = values[: cls.MAX_METADATA_SEQUENCE_ITEMS]
            value = ", ".join(visible)
            remaining = len(values) - len(visible)
            if remaining:
                value = f"{value} … (+{remaining})" if value else f"… (+{remaining})"
        else:
            value = str(raw_value).strip()
        return cls._compact_text(value, cls.MAX_METADATA_VALUE_CHARACTERS)

    @classmethod
    def _compact_people(cls, value: str) -> str:
        text = " ".join(str(value or "").split())
        if not text:
            return ""
        people = [item.strip() for item in re.split(r"\s*(?:,|;|\||·|\n)\s*", text) if item.strip()]
        if len(people) <= 1:
            return cls._compact_text(text, cls.MAX_AUTHOR_CHARACTERS)
        visible = people[: cls.MAX_AUTHOR_ITEMS]
        compact = ", ".join(visible)
        remaining = len(people) - len(visible)
        if remaining:
            compact = f"{compact} … (+{remaining})"
        return cls._compact_text(compact, cls.MAX_AUTHOR_CHARACTERS)

    @staticmethod
    def _compact_text(value: str, maximum: int) -> str:
        text = " ".join(str(value or "").split())
        limit = max(1, int(maximum))
        if len(text) <= limit:
            return text
        return f"{text[: max(1, limit - 1)].rstrip()}…"
