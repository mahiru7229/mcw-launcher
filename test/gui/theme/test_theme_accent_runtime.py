from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QColor, QPalette

from src.core.theme.theme_manager import ThemeManager
from src.gui.theme.accent_runtime import ThemeAccentRuntime


def test_custom_accent_derives_runtime_palette_and_qss(gui_app, tmp_path: Path) -> None:
    root = tmp_path / "themes" / "accent"
    root.mkdir(parents=True)
    (root / "theme.json").write_text(json.dumps({
        "schema_version": 6,
        "id": "accent",
        "assets": {},
        "palette": {"primary": "#3366cc", "selection": "#224488"},
    }), encoding="utf-8")
    manager = ThemeManager(tmp_path / "themes")
    theme = manager.select("accent")
    runtime = ThemeAccentRuntime(manager)

    palette = runtime.configure(theme, "custom", "#b26cff")
    runtime.apply_application_palette(gui_app)

    assert palette.primary == "#b26cff"
    assert "#b26cff" in runtime.stylesheet_rule()
    assert gui_app.palette().color(QPalette.ColorRole.Highlight) == QColor(palette.selection)


def test_legacy_theme_does_not_override_custom_stylesheet_in_theme_mode(tmp_path: Path) -> None:
    root = tmp_path / "themes" / "legacy"
    root.mkdir(parents=True)
    (root / "theme.json").write_text(json.dumps({"schema_version": 5, "id": "legacy", "assets": {}}), encoding="utf-8")
    manager = ThemeManager(tmp_path / "themes")
    runtime = ThemeAccentRuntime(manager)

    runtime.configure(manager.select("legacy"), "theme", "#b26cff")

    assert runtime.enabled is False
    assert runtime.stylesheet_rule() == ""
