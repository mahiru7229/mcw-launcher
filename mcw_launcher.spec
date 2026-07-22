# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.win32.versioninfo import FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct, VSVersionInfo


PROJECT_ROOT = Path(SPECPATH).resolve()
ENTRY_POINT = PROJECT_ROOT / "launcher.py"
LANGUAGE_ROOT = PROJECT_ROOT / "lang"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEVELOPER_NAME, LAUNCHER_NAME, VERSION_ID


def _numeric_version(version_id: str) -> tuple[int, int, int, int]:
    parts = [int(value) for value in re.findall(r"\d+", version_id)]
    return tuple((parts + [0, 0, 0, 0])[:4])


if not ENTRY_POINT.is_file():
    raise FileNotFoundError(f"Launcher entry point not found: {ENTRY_POINT}")
if not LANGUAGE_ROOT.is_dir():
    raise FileNotFoundError(f"Language directory not found: {LANGUAGE_ROOT}")


NUMERIC_VERSION = _numeric_version(VERSION_ID)
IS_PRERELEASE = any(marker in VERSION_ID.casefold() for marker in ("alpha", "beta", "rc"))

# Keep the default language packs inside the one-file executable so the GUI can
# still start when the external release payload is incomplete. External packs
# beside the executable remain supported and override bundled packs.
DATAS = [(str(LANGUAGE_ROOT), "lang")]

# HTTPX/Requests use certifi for HTTPS certificate validation. PyInstaller has a
# certifi hook, but collecting the data explicitly makes the release contract
# clear and protects the launcher from hook changes between PyInstaller builds.
DATAS += collect_data_files("certifi")

# win32crypt is imported through a guarded import because source-mode tests also
# run outside Windows. Keep it explicit so Microsoft token DPAPI is always
# available in the Windows executable.
HIDDEN_IMPORTS = ["win32crypt", "pywintypes"]

# Only QtCore, QtGui and QtWidgets are used by the launcher. Excluding unrelated
# bindings and optional Qt modules prevents accidental size growth when the
# build environment contains extra packages.
EXCLUDES = [
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDBus",
    "PySide6.QtDesigner",
    "PySide6.QtGraphs",
    "PySide6.QtHelp",
    "PySide6.QtLocation",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth",
    "PySide6.QtNfc",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtPrintSupport",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtXml",
    "pytest",
    "unittest",
    "doctest",
    "pydoc",
    "IPython",
    "jupyter",
    "matplotlib",
    "numpy",
    "pandas",
    "tkinter",
]

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
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", DEVELOPER_NAME),
                        StringStruct("FileDescription", LAUNCHER_NAME),
                        StringStruct("FileVersion", VERSION_ID),
                        StringStruct("InternalName", "MCW Launcher"),
                        StringStruct("LegalCopyright", f"Copyright © 2026 {DEVELOPER_NAME}"),
                        StringStruct("OriginalFilename", "MCW Launcher.exe"),
                        StringStruct("ProductName", "MCW Launcher"),
                        StringStruct("ProductVersion", VERSION_ID),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

# PerMonitorV2 avoids Windows bitmap-scaling the Qt window, which keeps QScreen
# geometry reliable for the 1600x900 and 1280x720 display profiles. Long path
# awareness is useful for deeply nested Minecraft library and modpack paths.
WINDOWS_MANIFEST = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="{'.'.join(str(value) for value in NUMERIC_VERSION)}" processorArchitecture="*" name="MCW.Launcher" type="win32"/>
  <description>MCW Launcher</description>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
    </dependentAssembly>
  </dependency>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}}"/>
    </application>
  </compatibility>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/pm</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
    </windowsSettings>
  </application>
</assembly>
"""

analysis = Analysis(
    [str(ENTRY_POINT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
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
    name="MCW Launcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version=VERSION_RESOURCE,
    manifest=WINDOWS_MANIFEST,
    uac_admin=False,
    uac_uiaccess=False,
)
