from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit
import json
import os

from src.core.fs.paths import Paths
from src.core.network.download_models import DownloadRequest, DownloadState


class DownloadJournal:
    SCHEMA_VERSION = 1

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else Paths.download_journal_path()
        self._lock = RLock()

    def start(self, request: DownloadRequest, downloaded_bytes: int = 0) -> None:
        self.update(request, DownloadState.DOWNLOADING, downloaded_bytes=downloaded_bytes, error="")

    def update(self, request: DownloadRequest, state: DownloadState, downloaded_bytes: int = 0, error: str = "") -> None:
        with self._lock:
            payload = self._read()
            entries = payload.setdefault("entries", {})
            first_url = request.urls[0] if request.urls else ""
            parsed = urlsplit(first_url)
            entries[request.request_id] = {
                "request_id": request.request_id,
                "operation_id": request.operation_id,
                "source": request.source,
                "display_name": request.display_name,
                "destination": str(request.destination),
                "temporary_path": str(request.temporary_path),
                "host": parsed.hostname or "",
                "state": state.value,
                "downloaded_bytes": max(0, int(downloaded_bytes or 0)),
                "expected_size": request.expected_size,
                "error": self._compact_error(error),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._write(payload)

    def complete(self, request: DownloadRequest, size: int) -> None:
        self.update(request, DownloadState.COMPLETED, downloaded_bytes=size, error="")

    def remove(self, request_id: str) -> None:
        with self._lock:
            payload = self._read()
            payload.setdefault("entries", {}).pop(str(request_id), None)
            self._write(payload)

    def recoverable_entries(self) -> list[dict]:
        with self._lock:
            entries = self._read().get("entries", {})
            recoverable = []
            for entry in entries.values():
                if entry.get("state") in {DownloadState.DOWNLOADING.value, DownloadState.PAUSED.value, DownloadState.CANCELLED.value, DownloadState.FAILED.value}:
                    recoverable.append(dict(entry))
            return sorted(recoverable, key=lambda item: str(item.get("updated_at", "")), reverse=True)

    def clear_completed(self) -> None:
        with self._lock:
            payload = self._read()
            entries = payload.setdefault("entries", {})
            payload["entries"] = {key: value for key, value in entries.items() if value.get("state") != DownloadState.COMPLETED.value}
            self._write(payload)

    def _read(self) -> dict:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
            payload = {"schema_version": self.SCHEMA_VERSION, "entries": {}}
        payload["schema_version"] = self.SCHEMA_VERSION
        if not isinstance(payload.get("entries"), dict):
            payload["entries"] = {}
        return payload

    def _write(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f"{self.path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(self.path)

    @staticmethod
    def _compact_error(error: str) -> str:
        compact = " ".join(str(error or "").split())
        return compact[:500]


download_journal = DownloadJournal()
