from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from src.core.theme.theme_authoring import ThemeAuthoringError, ThemeAuthoringService
from src.core.theme.theme_manager import ThemeManager


def write_theme(root: Path, theme_id: str = "test-theme", name: str = "Test Theme", *, broken_asset: bool = False) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    assets = {"background.window": "backgrounds/broken.png"} if broken_asset else {}
    if broken_asset:
        broken = root / "backgrounds" / "broken.png"
        broken.parent.mkdir(parents=True, exist_ok=True)
        broken.write_text("not png", encoding="utf-8")
    (root / "theme.json").write_text(json.dumps({"schema_version": 5, "id": theme_id, "name": name, "author": "Tester", "assets": assets}), encoding="utf-8")
    (root / "styles.qss").write_text("QWidget { background: #111; }", encoding="utf-8")
    return root


def test_validation_classifies_theme_issues(tmp_path: Path) -> None:
    themes = tmp_path / "themes"
    write_theme(themes / "broken", "broken", broken_asset=True)
    manager = ThemeManager(themes)
    service = ThemeAuthoringService(manager)

    report = service.validate("broken")

    assert report.is_valid is False
    assert report.error_count == 1
    assert report.issues[0].category == "asset"


def test_duplicate_updates_manifest_id_and_name(tmp_path: Path) -> None:
    themes = tmp_path / "themes"
    write_theme(themes / "source", "source", "Source Theme")
    manager = ThemeManager(themes)
    service = ThemeAuthoringService(manager)

    duplicate = service.duplicate("source", "source-copy", "Source Copy")
    payload = json.loads((themes / "source-copy" / "theme.json").read_text(encoding="utf-8"))

    assert duplicate.theme_id == "source-copy"
    assert payload["id"] == "source-copy"
    assert payload["name"] == "Source Copy"
    assert (themes / "source-copy" / "styles.qss").is_file()


def test_export_and_import_round_trip(tmp_path: Path) -> None:
    source_root = tmp_path / "source-themes"
    write_theme(source_root / "portable", "portable", "Portable Theme")
    source_manager = ThemeManager(source_root)
    archive = ThemeAuthoringService(source_manager).export("portable", tmp_path / "portable.zip")

    target_root = tmp_path / "target-themes"
    target_manager = ThemeManager(target_root)
    imported = ThemeAuthoringService(target_manager).import_archive(archive)

    assert imported.theme_id == "portable"
    assert (target_root / "portable" / "theme.json").is_file()
    assert (target_root / "portable" / "theme-checksums.json").is_file()


def test_import_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("../theme.json", "{}")
    service = ThemeAuthoringService(ThemeManager(tmp_path / "themes"))

    with pytest.raises(ThemeAuthoringError, match="Unsafe path"):
        service.import_archive(archive)


def test_import_rejects_scripts(tmp_path: Path) -> None:
    archive = tmp_path / "script.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("scripted/theme.json", json.dumps({"schema_version": 5, "id": "scripted"}))
        output.writestr("scripted/run.py", "print('no')")
    service = ThemeAuthoringService(ThemeManager(tmp_path / "themes"))

    with pytest.raises(ThemeAuthoringError, match="Unsupported file type"):
        service.import_archive(archive)


def test_export_refuses_invalid_theme(tmp_path: Path) -> None:
    themes = tmp_path / "themes"
    write_theme(themes / "broken", "broken", broken_asset=True)
    service = ThemeAuthoringService(ThemeManager(themes))

    with pytest.raises(ThemeAuthoringError, match="validation errors"):
        service.export("broken", tmp_path / "broken.zip")
