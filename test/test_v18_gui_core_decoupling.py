"""AST boundary and JSON-RPC 2.0 integration tests for MCW Launcher v1.8.0."""

from __future__ import annotations

import ast
from pathlib import Path

from mcw_core.rpc import CoreRpcClient, CoreRpcDispatcher, HttpRpcServer
from src.gui.core.rpc_bridge import GuiCoreRpcBridge


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_gui_and_launcher_have_zero_internal_src_core_or_models_imports() -> None:
    """Ensure src/gui/** and launcher.py never import src.core.* or src.models.*."""
    forbidden_prefixes = ("src.core", "src.models")
    violations: list[str] = []

    files_to_check = [PROJECT_ROOT / "launcher.py", *list((PROJECT_ROOT / "src" / "gui").rglob("*.py"))]
    for py_file in files_to_check:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden_prefixes):
                        violations.append(f"{py_file.relative_to(PROJECT_ROOT)}:{node.lineno} import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(forbidden_prefixes):
                    violations.append(f"{py_file.relative_to(PROJECT_ROOT)}:{node.lineno} from {node.module}")

    assert violations == [], f"GUI or launcher.py imported internal Core modules: {violations}"
    launcher_source = (PROJECT_ROOT / "launcher.py").read_text(encoding="utf-8")
    assert "src/core/" not in launcher_source


def test_gui_core_rpc_bridge_direct_and_http_modes(tmp_path: Path) -> None:
    """Verify GuiCoreRpcBridge communicates over JSON-RPC 2.0 in direct and HTTP modes."""
    bridge = GuiCoreRpcBridge(mode="direct", data_root=tmp_path / "gui_rpc_direct")
    try:
        ping = bridge.ping()
        assert ping["pong"] is True
        assert ping["version_id"] == "1.8.0"

        created = bridge.call(
            "instances.create",
            name="V18 Decoupled Instance",
            version_id="1.21.1",
            loader_name="fabric",
        )
        assert created["name"] == "V18 Decoupled Instance"
        instances = bridge.list_instances()
        assert any(i["name"] == "V18 Decoupled Instance" for i in instances)
    finally:
        bridge.close()

    server = HttpRpcServer(data_root=tmp_path / "gui_rpc_http", port=0)
    base_url = server.start()
    http_bridge = GuiCoreRpcBridge(mode="http", http_url=base_url)
    try:
        ping_http = http_bridge.ping()
        assert ping_http["ok"] is True
        assert ping_http["version"] == "v1.8.0"
    finally:
        http_bridge.close()
        server.stop()


def test_stdio_sidecar_subprocess_rpc_v18(tmp_path: Path) -> None:
    """Verify mcw_core.rpc.cli runs as an isolated Stdio Sidecar subprocess."""
    client = CoreRpcClient(mode="stdio", data_root=tmp_path / "gui_rpc_stdio")
    try:
        pong = client.call("system.ping")
        assert pong["pong"] is True
        assert pong["version_id"] == "1.8.0"
    finally:
        client.close()
