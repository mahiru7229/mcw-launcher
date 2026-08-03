from __future__ import annotations

from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse


class _Sanitizer(HTMLParser):
    ALLOWED_TAGS = {
        "a", "b", "blockquote", "br", "code", "em", "h1", "h2", "h3", "h4",
        "hr", "i", "li", "ol", "p", "pre", "strong", "table", "tbody", "td",
        "th", "thead", "tr", "u", "ul",
    }
    VOID_TAGS = {"br", "hr"}
    BLOCKED_TAGS = {"script", "style", "iframe", "object", "embed", "svg", "math"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._blocked_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.casefold()
        if normalized in self.BLOCKED_TAGS:
            self._blocked_depth += 1
            return
        if self._blocked_depth or normalized not in self.ALLOWED_TAGS:
            return
        if normalized == "a":
            href = next((str(value or "").strip() for key, value in attrs if key.casefold() == "href"), "")
            parsed = urlparse(href)
            if parsed.scheme.casefold() in {"https", "http"} and parsed.hostname and not parsed.username and not parsed.password:
                self.parts.append(f'<a href="{escape(href, quote=True)}">')
                return
            self.parts.append("<a>")
            return
        self.parts.append(f"<{normalized}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.casefold() not in self.VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if normalized in self.BLOCKED_TAGS:
            self._blocked_depth = max(0, self._blocked_depth - 1)
            return
        if self._blocked_depth:
            return
        if normalized in self.ALLOWED_TAGS and normalized not in self.VOID_TAGS:
            self.parts.append(f"</{normalized}>")

    def handle_data(self, data: str) -> None:
        if not self._blocked_depth:
            self.parts.append(escape(data))


def sanitize_html(value: str) -> str:
    parser = _Sanitizer()
    parser.feed(str(value or ""))
    parser.close()
    return "".join(parser.parts)


def safe_external_url(value: str) -> str:
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    if parsed.scheme.casefold() != "https" or not parsed.hostname or parsed.username or parsed.password:
        return ""
    return raw
