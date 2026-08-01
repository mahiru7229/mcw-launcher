from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import zlib

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.core.theme.theme_manager import ThemeManager
from src.gui.widget.themed_progress_bar import ThemedProgressBar


def write_png(path: Path, width: int, height: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    rows = b"".join(b"\x00" + (b"\x8e\xd3\x5b\xff" * width) for _ in range(height))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    path.write_bytes(signature + chunk(b"IHDR", ihdr_data) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_progress_bar_switches_between_determinate_and_indeterminate_animation(app, tmp_path: Path) -> None:
    root = tmp_path / "themes" / "animated"
    root.mkdir(parents=True)
    payload = {
        "schema_version": 2,
        "id": "animated",
        "assets": {},
        "animations": {
            "progress.chunk": {
                "type": "spritesheet",
                "path": "animations/chunk.png",
                "frame_size": [8, 8],
                "frame_count": 2,
                "columns": 2,
                "frame_duration_ms": 80,
            },
            "progress.indeterminate": {
                "type": "spritesheet",
                "path": "animations/indeterminate.png",
                "frame_size": [8, 8],
                "frame_count": 2,
                "columns": 2,
                "frame_duration_ms": 80,
                "render_mode": "stretch",
            },
        },
    }
    (root / "theme.json").write_text(json.dumps(payload), encoding="utf-8")
    write_png(root / "animations/chunk.png", 16, 8)
    write_png(root / "animations/indeterminate.png", 16, 8)

    manager = ThemeManager(tmp_path / "themes")
    manager.select("animated")
    progress = ThemedProgressBar(manager=manager)

    progress.setRange(0, 100)
    assert progress._active_animation_key == "progress.chunk"
    assert progress._animation_player.animation is not None

    progress.setRange(0, 0)
    assert progress._active_animation_key == "progress.indeterminate"
    assert progress._animation_player.animation is not None
