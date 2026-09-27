"""Qt-compatible JSON-RPC 2.0 Bridge for MCW Launcher v1.8.0 GUI."""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Any

from PySide6.QtCore import QObject, Signal

from mcw_core.rpc import CoreRpcClient, CoreRpcDispatcher, HttpRpcServer, RpcEvent


class GuiCoreRpcBridge(QObject):
    """Bridges MCW Core JSON-RPC 2.0 commands and events to PySide6 signals.

    Allows the v1.8.0 GUI to communicate with ``mcw-launcher-core`` over
    ``direct``, ``http`` (with SSE), or ``stdio`` (Sidecar subprocess) transports
    without importing any ``src.core`` or ``src.models`` internals.
    """

    event_received = Signal(str, dict)

    def __init__(
        self,
        mode: str = "direct",
        *,
        data_root: Path | str | None = None,
        http_url: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._lock = threading.RLock()
        self.client = CoreRpcClient(mode=mode, data_root=data_root, http_url=http_url)
        self._unsubscribe = self.client.subscribe(self._on_rpc_event)

    def _on_rpc_event(self, event: RpcEvent) -> None:
        self.event_received.emit(event.event, dict(event.data))

    def call(self, method: str, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        with self._lock:
            return self.client.call(method, params=params, **kwargs)

    def ping(self) -> dict[str, Any]:
        return dict(self.call("system.ping"))

    def list_instances(self) -> list[dict[str, Any]]:
        return list(self.call("instances.list"))

    def close(self) -> None:
        with self._lock:
            try:
                self._unsubscribe()
            except Exception:
                pass
            self.client.close()


_default_bridge: GuiCoreRpcBridge | None = None
_bridge_lock = threading.RLock()


def get_gui_rpc_bridge(mode: str = "direct", data_root: Path | str | None = None) -> GuiCoreRpcBridge:
    global _default_bridge
    with _bridge_lock:
        if _default_bridge is None:
            _default_bridge = GuiCoreRpcBridge(mode=mode, data_root=data_root)
        return _default_bridge
