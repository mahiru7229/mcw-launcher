from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.java.adoptium_client import AdoptiumClient
from src.core.java.java_manager import JavaManager
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.core.system.platform_info import PlatformInfo


def run(java_major: int = 21) -> tuple[dict, bool]:
    profile = PlatformInfo.current()
    checks: dict[str, object] = {
        "platform": {
            "os": profile.os_name,
            "architecture": profile.architecture,
            "adoptium_architecture": profile.adoptium_architecture,
        },
        "display_session": {
            "display": bool(os.environ.get("DISPLAY")),
            "wayland": bool(os.environ.get("WAYLAND_DISPLAY")),
            "session_type": str(os.environ.get("XDG_SESSION_TYPE") or "unknown"),
        },
    }
    required_ok = profile.os_name == "linux" and PlatformInfo.supports_managed_java()

    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401

        checks["qt"] = {"ok": True}
    except Exception as error:
        checks["qt"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        required_ok = False

    try:
        versions = VersionManifestManager.get()
        checks["minecraft_manifest"] = {
            "ok": bool(versions),
            "entries": len(versions),
            "latest_entry": versions[0].id if versions else "",
        }
        required_ok = required_ok and bool(versions)
    except Exception as error:
        checks["minecraft_manifest"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        required_ok = False

    try:
        release = AdoptiumClient.get_latest_jdk(java_major)
        checks["managed_java_metadata"] = {
            "ok": release.filename.casefold().endswith(profile.archive_suffix),
            "major": release.major,
            "filename": release.filename,
            "size": release.size,
        }
        required_ok = required_ok and bool(checks["managed_java_metadata"]["ok"])
    except Exception as error:
        checks["managed_java_metadata"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        required_ok = False

    try:
        installations = JavaManager.find_installation()
        checks["installed_java"] = {
            "ok": True,
            "count": len(installations),
            "items": [
                {"major": item.version, "path": str(item.executable), "source": item.source.value}
                for item in installations
            ],
        }
    except Exception as error:
        checks["installed_java"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}

    return checks, required_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate MCW Launcher source prerequisites on Linux.")
    parser.add_argument("--java-major", type=int, default=21)
    args = parser.parse_args()
    checks, ok = run(args.java_major)
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
