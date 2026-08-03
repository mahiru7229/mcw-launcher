from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QObject, QSize, Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from mcw_core.api.fs.paths import Paths
from src.config import MODRINTH_USER_AGENT


class RemoteImageCache(QObject):
    """Small HTTPS-only image cache for content cards and project details."""

    MAX_IMAGE_BYTES = 4 * 1024 * 1024
    REQUEST_TIMEOUT_MS = 15_000

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._memory: dict[str, QPixmap] = {}
        self._callbacks: dict[str, list[Callable[[QPixmap], None]]] = {}

    def request(self, url: str, callback: Callable[[QPixmap], None]) -> None:
        normalized = self._safe_url(url)
        if not normalized:
            callback(QPixmap())
            return

        cached = self._memory.get(normalized)
        if cached is not None:
            callback(QPixmap(cached))
            return

        disk = self._cache_path(normalized)
        pixmap = QPixmap(str(disk)) if disk.is_file() else QPixmap()
        if not pixmap.isNull():
            self._memory[normalized] = pixmap
            callback(QPixmap(pixmap))
            return

        pending = self._callbacks.setdefault(normalized, [])
        pending.append(callback)
        if len(pending) > 1:
            return

        request = QNetworkRequest(QUrl(normalized))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, MODRINTH_USER_AGENT)
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        request.setMaximumRedirectsAllowed(4)
        request.setTransferTimeout(self.REQUEST_TIMEOUT_MS)
        reply = self._manager.get(request)
        reply.finished.connect(lambda reply=reply, url=normalized: self._finished(url, reply))

    def scaled(self, pixmap: QPixmap, size: QSize) -> QPixmap:
        if pixmap.isNull():
            return QPixmap()
        return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def _finished(self, url: str, reply: QNetworkReply) -> None:
        callbacks = self._callbacks.pop(url, [])
        pixmap = QPixmap()
        try:
            length = reply.header(QNetworkRequest.KnownHeaders.ContentLengthHeader)
            try:
                content_length = int(length or 0)
            except (TypeError, ValueError):
                content_length = 0
            if reply.error() == QNetworkReply.NetworkError.NoError and content_length <= self.MAX_IMAGE_BYTES:
                payload = bytes(reply.readAll())
                if len(payload) <= self.MAX_IMAGE_BYTES and pixmap.loadFromData(payload):
                    self._memory[url] = pixmap
                    self._write_cache(url, payload)
        finally:
            reply.deleteLater()

        for callback in callbacks:
            try:
                callback(QPixmap(pixmap))
            except RuntimeError:
                continue

    @classmethod
    def _safe_url(cls, value: str) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        parsed = urlparse(raw)
        if parsed.scheme.casefold() != "https" or not parsed.hostname or parsed.username or parsed.password:
            return ""
        return raw

    @staticmethod
    def _cache_root() -> Path:
        root = Path(Paths.CACHE_ROOT) / "content-images"
        root.mkdir(parents=True, exist_ok=True)
        return root

    @classmethod
    def _cache_path(cls, url: str) -> Path:
        return cls._cache_root() / sha256(url.encode("utf-8")).hexdigest()

    @classmethod
    def _write_cache(cls, url: str, payload: bytes) -> None:
        path = cls._cache_path(url)
        part = path.with_suffix(".part")
        try:
            part.write_bytes(payload)
            part.replace(path)
        except OSError:
            try:
                part.unlink(missing_ok=True)
            except OSError:
                pass
