from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import hashlib
import os
import shutil
import sys
import zipfile

from src.core.fs.paths import Paths
from src.models.instance.instance import Instance
from src.models.minecraft.version import Version


@dataclass(frozen=True, slots=True)
class LanAgentInstallResult:
    path: Path
    installed: bool


class LanAgentManager:
    """Install and attach the bundled host-side LAN agent.

    The agent is intentionally narrow: it only changes
    ``MinecraftServer#setUsesAuthentication(boolean)`` inside the Minecraft
    client process. It never replaces Authlib and is attached only when the
    selected instance uses the explicit ``private_offline`` LAN policy.
    """

    AUTH_PRIVATE_OFFLINE = "private_offline"
    AGENT_FILENAME = "mcw-lan-agent.jar"
    AGENT_LOG_FILENAME = "mcw-lan-agent.log"
    AGENT_SHA256 = "c6c39033c85d8b111411ac1a0afb67f4b717a91af532befd8c3379f8c03667cc"
    TARGET_CLASS = "net/minecraft/server/MinecraftServer"
    TARGET_METHOD = "setUsesAuthentication"
    TARGET_DESCRIPTOR = "(Z)V"
    RESERVED_ARGUMENT_PREFIXES = (
        "-Dmcw.lan.",
        "-javaagent:",
    )

    @classmethod
    def is_enabled(cls, auth_mode: object) -> bool:
        return str(auth_mode or "").strip().lower() in {cls.AUTH_PRIVATE_OFFLINE, "friends"}

    @classmethod
    def install(cls) -> LanAgentInstallResult:
        source = cls._bundled_agent_path()
        cls._verify_file(source, "Bundled MCW LAN Agent")

        destination = cls.runtime_agent_path()
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_file() and cls._sha256(destination) == cls.AGENT_SHA256:
            return LanAgentInstallResult(path=destination, installed=False)

        temporary = destination.with_suffix(destination.suffix + ".part")
        try:
            shutil.copyfile(source, temporary)
            cls._verify_file(temporary, "Copied MCW LAN Agent")
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

        return LanAgentInstallResult(path=destination, installed=True)

    @classmethod
    def runtime_arguments(cls, version: Version, auth_mode: object, instance: Instance) -> list[str]:
        path = cls.log_path(instance)
        if not path.is_file():
            path = cls.prepare_log(instance, auth_mode)
        if not cls.is_enabled(auth_mode):
            cls.append_log_path(path, f"Agent not attached because LAN authentication mode is {auth_mode!r}.")
            return []

        cls.append_log_path(path, "Private LAN mode is enabled; validating the MCW LAN Agent.")
        try:
            cls._verify_supported_client(version)
            cls.append_log_path(path, f"Minecraft client compatibility check passed for {version.id}.")
            installation = cls.install()
            cls.append_log_path(
                path,
                f"Agent {'installed' if installation.installed else 'reused'}: {installation.path.resolve()}",
            )
            arguments = [
                "-Dmcw.lan.offline=true",
                f"-Dmcw.lan.target.class={cls.TARGET_CLASS}",
                f"-Dmcw.lan.target.method={cls.TARGET_METHOD}",
                f"-Dmcw.lan.log={path.resolve().as_posix()}",
                f"-javaagent:{installation.path}",
            ]
            cls.append_log_path(path, "Agent JVM arguments were prepared successfully.")
            return arguments
        except Exception as error:
            cls.append_log_path(path, f"ERROR while preparing the agent: {type(error).__name__}: {error}")
            raise

    @classmethod
    def log_path(cls, instance: Instance) -> Path:
        instance_dir = Path(getattr(instance, "instance_dir", Paths.load_instance_dir(instance.name)))
        directory = instance_dir / "logs"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / cls.AGENT_LOG_FILENAME

    @classmethod
    def prepare_log(cls, instance: Instance, auth_mode: object = "unknown") -> Path:
        path = cls.log_path(instance)
        path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        bundled_path = cls._bundled_agent_path()
        runtime_path = cls.runtime_agent_path()
        path.write_text(
            "[MCW Launcher] MCW LAN Agent launch diagnostics\n"
            f"[MCW Launcher] Started: {timestamp}\n"
            f"[MCW Launcher] Instance: {instance.name}\n"
            f"[MCW Launcher] Instance directory: {Path(getattr(instance, 'instance_dir', Paths.load_instance_dir(instance.name))).resolve()}\n"
            f"[MCW Launcher] LAN authentication mode: {auth_mode}\n"
            f"[MCW Launcher] Agent requested: {cls.is_enabled(auth_mode)}\n"
            f"[MCW Launcher] Launcher mode: {'frozen executable' if getattr(sys, 'frozen', False) else 'source'}\n"
            f"[MCW Launcher] Bundled agent: {bundled_path.resolve()}\n"
            f"[MCW Launcher] Runtime agent: {runtime_path.resolve()}\n"
            f"[MCW Launcher] Target: {cls.TARGET_CLASS.replace('/', '.')}#{cls.TARGET_METHOD}{cls.TARGET_DESCRIPTOR}\n",
            encoding="utf-8",
        )
        return path

    @classmethod
    def append_log(cls, instance: Instance, message: str) -> None:
        cls.append_log_path(cls.log_path(instance), message)

    @staticmethod
    def append_log_path(path: Path, message: str) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            with path.open("a", encoding="utf-8") as stream:
                stream.write(f"[MCW Launcher] {timestamp} {message}\n")
        except OSError:
            return

    @classmethod
    def read_log(cls, instance: Instance) -> str:
        path = cls.log_path(instance)
        if not path.is_file():
            return ""
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    @classmethod
    def sanitize_user_jvm_arguments(cls, arguments: list[str]) -> list[str]:
        sanitized: list[str] = []
        for argument in arguments:
            value = str(argument)
            if value.startswith("-Dmcw.lan."):
                continue
            if value.startswith("-javaagent:") and cls.AGENT_FILENAME.casefold() in value.casefold():
                continue
            sanitized.append(value)
        return sanitized

    @classmethod
    def runtime_agent_path(cls) -> Path:
        return Paths.CACHE_ROOT / "runtime" / "agents" / "mcw-lan-agent" / cls.AGENT_FILENAME

    @classmethod
    def _bundled_agent_path(cls) -> Path:
        if getattr(sys, "frozen", False):
            bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        else:
            bundle_root = Paths.root()
        return bundle_root / "runtime" / cls.AGENT_FILENAME

    @classmethod
    def _verify_supported_client(cls, version: Version) -> None:
        client_path = Paths.client(version)
        if not client_path.is_file():
            raise RuntimeError("Minecraft client is missing; repair the instance before enabling Private LAN.")

        class_entry = cls.TARGET_CLASS + ".class"
        try:
            with zipfile.ZipFile(client_path) as archive:
                class_bytes = archive.read(class_entry)
        except KeyError as error:
            raise RuntimeError(
                "Force LAN Offline Mode is experimental and this Minecraft runtime does not expose "
                "the supported named MinecraftServer class. Use Microsoft-only LAN for this version "
                "or test with Minecraft 26.2 while broader mapping support is developed."
            ) from error
        except (OSError, zipfile.BadZipFile) as error:
            raise RuntimeError("Minecraft client JAR could not be inspected for LAN Agent compatibility.") from error

        method_name = cls.TARGET_METHOD.encode("utf-8")
        descriptor = cls.TARGET_DESCRIPTOR.encode("ascii")
        if method_name not in class_bytes or descriptor not in class_bytes:
            raise RuntimeError(
                "The current MinecraftServer bytecode is not compatible with this MCW LAN Agent build. "
                "Minecraft will not be patched; use Microsoft-only LAN for this version."
            )

    @classmethod
    def _verify_file(cls, path: Path, label: str) -> None:
        if not path.is_file():
            raise RuntimeError(f"{label} is missing: {path}")
        digest = cls._sha256(path)
        if digest != cls.AGENT_SHA256:
            raise RuntimeError(f"{label} failed SHA-256 verification and will not be loaded.")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
