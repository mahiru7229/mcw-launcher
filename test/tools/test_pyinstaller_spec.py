from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_windows_version_resource_import_is_platform_guarded() -> None:
    tree = ast.parse((PROJECT_ROOT / "mcw_launcher.spec").read_text(encoding="utf-8"))

    guarded_imports = [
        child
        for node in tree.body
        if isinstance(node, ast.If)
        for child in ast.walk(node)
        if isinstance(child, ast.ImportFrom)
        and child.module == "PyInstaller.utils.win32.versioninfo"
    ]
    top_level_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "PyInstaller.utils.win32.versioninfo"
    ]

    assert guarded_imports
    assert not top_level_imports


def test_updater_windows_version_resource_import_is_platform_guarded() -> None:
    tree = ast.parse((PROJECT_ROOT / "mcw_updater.spec").read_text(encoding="utf-8"))
    guarded_imports = [
        child
        for node in tree.body
        if isinstance(node, ast.If)
        for child in ast.walk(node)
        if isinstance(child, ast.ImportFrom)
        and child.module == "PyInstaller.utils.win32.versioninfo"
    ]
    top_level_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "PyInstaller.utils.win32.versioninfo"
    ]
    assert guarded_imports
    assert not top_level_imports


def test_updater_spec_uses_dedicated_entry_point() -> None:
    text = (PROJECT_ROOT / "mcw_updater.spec").read_text(encoding="utf-8")
    assert 'ENTRY_POINT = PROJECT_ROOT / "updater.py"' in text
    assert 'EXECUTABLE_NAME = "MCW Updater" if IS_WINDOWS else "mcw-updater"' in text
