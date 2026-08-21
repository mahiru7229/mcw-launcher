from __future__ import annotations

from dataclasses import dataclass
import os
import platform
import sys


@dataclass(frozen=True, slots=True)
class PlatformProfile:
    os_name: str
    architecture: str
    adoptium_architecture: str
    java_executable: str
    java_console_executable: str
    archive_suffix: str


class PlatformInfo:
    """Single source of truth for launcher platform-specific names."""

    _OS_NAMES = {
        "windows": "windows",
        "linux": "linux",
        "darwin": "mac",
    }
    _ARCHITECTURES = {
        "amd64": ("x64", "x64"),
        "x86_64": ("x64", "x64"),
        "x86": ("x86", "x86"),
        "i386": ("x86", "x86"),
        "i686": ("x86", "x86"),
        "arm64": ("arm64", "aarch64"),
        "aarch64": ("arm64", "aarch64"),
    }

    @classmethod
    def current(cls) -> PlatformProfile:
        system = platform.system().strip().casefold()
        machine = platform.machine().strip().casefold()
        os_name = cls._OS_NAMES.get(system, system or sys.platform.casefold())
        architecture, adoptium_architecture = cls._ARCHITECTURES.get(
            machine,
            (machine or "unknown", machine or "unknown"),
        )
        is_windows = os_name == "windows" or os.name == "nt"
        return PlatformProfile(
            os_name=os_name,
            architecture=architecture,
            adoptium_architecture=adoptium_architecture,
            java_executable="javaw.exe" if is_windows else "java",
            java_console_executable="java.exe" if is_windows else "java",
            archive_suffix=".zip" if is_windows else ".tar.gz",
        )

    @classmethod
    def supports_managed_java(cls) -> bool:
        profile = cls.current()
        return profile.os_name in {"windows", "linux"} and profile.adoptium_architecture in {
            "x64",
            "x86",
            "aarch64",
        }

    @classmethod
    def java_home_executables(cls) -> tuple[str, ...]:
        profile = cls.current()
        if profile.os_name == "windows":
            return (profile.java_executable, profile.java_console_executable)
        return (profile.java_executable,)
