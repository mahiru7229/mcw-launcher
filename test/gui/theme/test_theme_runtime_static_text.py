from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import zlib

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from src.core.theme.theme_manager import ThemeManager
from src.gui.theme.runtime import ThemeRuntime, set_theme_static_text


def write_png(path: Path, width: int = 4, height: int = 4) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    rows = b"".join(b"\x00" + (b"\x00\x00\x00\x00" * width) for _ in range(height))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    path.write_bytes(signature + chunk(b"IHDR", ihdr_data) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def build_root() -> tuple[QWidget, QPushButton]:
    root = QWidget()
    layout = QVBoxLayout(root)
    button = QPushButton("Launch")
    set_theme_static_text(button, "control.launch", "Launch")
    layout.addWidget(button)
    return root, button


def test_static_text_is_hidden_only_for_a_valid_declared_asset(tmp_path: Path, app: QApplication) -> None:
    theme_root = tmp_path / "themes" / "pixel"
    theme_root.mkdir(parents=True)
    (theme_root / "theme.json").write_text(json.dumps({
        "schema_version": 1,
        "id": "pixel",
        "name": "Pixel",
        "author": "Test",
        "assets": {"button.launch": "launch.png"},
        "text_assets": {"control.launch": "button.launch"},
    }), encoding="utf-8")
    write_png(theme_root / "launch.png", 461, 133)

    root, button = build_root()
    runtime = ThemeRuntime(ThemeManager(tmp_path / "themes"))
    runtime.apply(root, "", "pixel", show_static_text=False)

    assert button.text() == ""
    assert button.property("themeStaticTextHidden") is True

    runtime.apply(root, "", "pixel", show_static_text=True)

    assert button.text() == "Launch"
    assert button.property("themeStaticTextHidden") is False


def test_missing_text_asset_keeps_fallback_text_visible(tmp_path: Path, app: QApplication) -> None:
    theme_root = tmp_path / "themes" / "incomplete"
    theme_root.mkdir(parents=True)
    (theme_root / "theme.json").write_text(json.dumps({
        "schema_version": 1,
        "id": "incomplete",
        "name": "Incomplete",
        "author": "Test",
        "assets": {"button.launch": "missing.png"},
        "text_assets": {"control.launch": "button.launch"},
    }), encoding="utf-8")

    root, button = build_root()
    runtime = ThemeRuntime(ThemeManager(tmp_path / "themes"))
    runtime.apply(root, "", "incomplete", show_static_text=False)

    assert button.text() == "Launch"
    assert button.property("themeStaticTextHidden") is False
