# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys

if sys.platform == "win32":
    from PyInstaller.utils.win32.versioninfo import FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct, VSVersionInfo

PROJECT_ROOT = Path(SPECPATH).resolve()
ENTRY_POINT = PROJECT_ROOT / "updater.py"
APP_ICON_PATH = PROJECT_ROOT / "assets" / "icons" / "mcw_launcher.ico"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEVELOPER_NAME, VERSION_ID


def _numeric_version(value: str) -> tuple[int, int, int, int]:
    numbers = [int(part) for part in re.findall(r"\d+", value)[:4]]
    numbers.extend([0] * (4 - len(numbers)))
    return tuple(numbers[:4])


if not ENTRY_POINT.is_file():
    raise FileNotFoundError(f"Updater entry point not found: {ENTRY_POINT}")
if not APP_ICON_PATH.is_file():
    raise FileNotFoundError(f"Updater icon not found: {APP_ICON_PATH}")

NUMERIC_VERSION = _numeric_version(VERSION_ID)
IS_PRERELEASE = any(marker in VERSION_ID.casefold() for marker in ("alpha", "beta", "rc"))
IS_WINDOWS = sys.platform == "win32"
EXECUTABLE_NAME = "MCW Updater" if IS_WINDOWS else "mcw-updater"

VERSION_RESOURCE = None
if IS_WINDOWS:
    VERSION_RESOURCE = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=NUMERIC_VERSION,
            prodvers=NUMERIC_VERSION,
            mask=0x3F,
            flags=0x2 if IS_PRERELEASE else 0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo([
                StringTable("040904B0", [
                    StringStruct("CompanyName", DEVELOPER_NAME),
                    StringStruct("FileDescription", "MCW Updater"),
                    StringStruct("FileVersion", VERSION_ID),
                    StringStruct("InternalName", "MCW Updater"),
                    StringStruct("LegalCopyright", f"Copyright © 2026 {DEVELOPER_NAME}"),
                    StringStruct("OriginalFilename", "MCW Updater.exe"),
                    StringStruct("ProductName", "MCW Launcher Updater"),
                    StringStruct("ProductVersion", VERSION_ID),
                ])
            ]),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ],
    )

UPDATER_EXCLUDES = [
    "PyQt5", "PyQt6", "PySide2", "PySide6", "pytest",
    "unittest", "numpy", "pandas", "matplotlib",
]
if not IS_WINDOWS:
    # Linux keeps the recovery/update helper dependency-light and headless.
    UPDATER_EXCLUDES.append("tkinter")

analysis = Analysis(
    [str(ENTRY_POINT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=UPDATER_EXCLUDES,
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name=EXECUTABLE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=not IS_WINDOWS,
    disable_windowed_traceback=False,
    version=VERSION_RESOURCE,
    icon=str(APP_ICON_PATH) if IS_WINDOWS else None,
    uac_admin=False,
    uac_uiaccess=False,
)
