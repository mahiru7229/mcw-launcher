from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal


class ThemeLiveReload(QObject):
    reload_requested = Signal(str)

    WATCHED_SUFFIXES = frozenset({".json", ".qss", ".png", ".ttf", ".otf"})

    def __init__(self, parent: QObject | None = None, debounce_ms: int = 350) -> None:
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(max(100, int(debounce_ms)))
        self._timer.timeout.connect(self._emit_reload)
        self._watcher.fileChanged.connect(self._queue_reload)
        self._watcher.directoryChanged.connect(self._queue_reload)
        self._theme_id = ""
        self._root: Path | None = None
        self._enabled = False

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        if not self._enabled:
            self._timer.stop()
        self._refresh_watches()

    def watch(self, theme_id: str, root: Path | None) -> None:
        self._theme_id = str(theme_id or "").strip()
        self._root = Path(root).resolve() if root is not None else None
        self._refresh_watches()

    def _queue_reload(self, _path: str = "") -> None:
        if not self._enabled or not self._theme_id:
            return
        self._refresh_watches()
        self._timer.start()

    def _emit_reload(self) -> None:
        if self._enabled and self._theme_id:
            self.reload_requested.emit(self._theme_id)

    def _refresh_watches(self) -> None:
        existing = [*self._watcher.files(), *self._watcher.directories()]
        if existing:
            self._watcher.removePaths(existing)
        if not self._enabled or self._root is None or not self._root.is_dir():
            return
        paths = [str(self._root)]
        for path in self._root.rglob("*"):
            if path.is_dir():
                paths.append(str(path))
            elif path.is_file() and path.suffix.lower() in self.WATCHED_SUFFIXES:
                paths.append(str(path))
        if paths:
            self._watcher.addPaths(paths)
