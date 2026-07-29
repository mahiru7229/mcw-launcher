from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from src.core.theme.theme_manager import ThemeManager
from src.gui.theme.font_runtime import ThemeFontRuntime


def write_font(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00\x01\x00\x00" + (b"\x00" * 60))


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_font_runtime_applies_theme_font_and_builds_global_qss_rule(tmp_path: Path, app: QApplication, monkeypatch) -> None:
    root = tmp_path / "themes" / "font-theme"
    root.mkdir(parents=True)
    (root / "theme.json").write_text(json.dumps({
        "schema_version": 3,
        "id": "font-theme",
        "assets": {},
        "font": {
            "path": "fonts/ui.ttf",
            "family": "MCW Pixel",
            "point_size": 12,
            "weight": 600,
            "letter_spacing": 1,
            "fallback_families": ["Segoe UI"],
        },
    }), encoding="utf-8")
    write_font(root / "fonts/ui.ttf")

    monkeypatch.setattr(QFontDatabase, "addApplicationFont", lambda path: 17)
    monkeypatch.setattr(QFontDatabase, "applicationFontFamilies", lambda font_id: ["MCW Pixel"])
    monkeypatch.setattr(QFontDatabase, "removeApplicationFont", lambda font_id: True)

    app.setFont(QFont("Sans Serif", 10))
    manager = ThemeManager(tmp_path / "themes")
    selected = manager.select("font-theme")
    runtime = ThemeFontRuntime(manager)

    family = runtime.apply(app, selected)

    assert family == "MCW Pixel"
    assert runtime.active_theme_id == "font-theme"
    assert runtime.active_family == "MCW Pixel"
    assert app.font().pointSizeF() == 12
    rule = runtime.stylesheet_rule()
    assert 'font-family: "MCW Pixel", "Segoe UI"' in rule
    assert "font-size: 12pt" in rule
    assert "font-weight: 600" in rule
    assert "font-style: normal" in rule

    runtime.reset(app)
    assert runtime.active_family == ""


def test_font_runtime_falls_back_when_qt_rejects_font(tmp_path: Path, app: QApplication, monkeypatch) -> None:
    root = tmp_path / "themes" / "font-theme"
    root.mkdir(parents=True)
    (root / "theme.json").write_text(json.dumps({
        "schema_version": 3,
        "id": "font-theme",
        "assets": {},
        "font": {"path": "fonts/ui.ttf"},
    }), encoding="utf-8")
    write_font(root / "fonts/ui.ttf")

    monkeypatch.setattr(QFontDatabase, "addApplicationFont", lambda path: -1)
    monkeypatch.setattr(QFontDatabase, "removeApplicationFont", lambda font_id: True)

    app.setFont(QFont("Sans Serif", 10))
    manager = ThemeManager(tmp_path / "themes")
    selected = manager.select("font-theme")
    runtime = ThemeFontRuntime(manager)

    assert runtime.apply(app, selected) is None
    assert runtime.active_family == ""
    assert runtime.stylesheet_rule() == ""
