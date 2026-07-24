from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

from src.core.fs.paths import Paths
from src.core.mod.mod_manager import ModManager
from src.core.modloader.forge.forge_change_manager import ForgeChangeManager
from src.core.modloader.forge.forge_preflight_manager import ForgePreflightManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.minecraft.version_manager import VersionManager
from src.core.security.sensitive_data_redactor import SensitiveDataRedactor
from src.models.instance.instance import Instance


class ForgeDiagnosticsManager:
    SCHEMA_VERSION = 1
    MAX_TEXT_BYTES = 2 * 1024 * 1024

    @classmethod
    def export(cls, instance: Instance, destination: Path, launcher_version: str) -> Path:
        loader_name, loader_version = ModLoaderManager.normalize(instance.mod_loader)
        if loader_name != ModLoaderManager.FORGE:
            raise RuntimeError("Forge diagnostics are available only for Forge instances.")

        target = Path(destination)
        if target.suffix.lower() != ".zip":
            target = target.with_suffix(".zip")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".part")
        temporary.unlink(missing_ok=True)

        profile_path = Paths.forge_version_json(instance.version_id, loader_version)
        try:
            profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
            forge_version = VersionManager._parse_version(profile_data, profile_path)
            if forge_version is None:
                raise RuntimeError("The cached Forge launch profile could not be parsed.")
            report = ForgePreflightManager.scan(instance, forge_version, verify_files=False)
        except Exception as error:
            forge_version = None
            report = None
            preflight_error = SensitiveDataRedactor.redact_text(error)
        else:
            preflight_error = ""

        summary = cls._summary(
            instance=instance,
            launcher_version=launcher_version,
            loader_version=loader_version,
            java_major=int((getattr(forge_version, "java_version", None) or {}).get("majorVersion") or 8),
            report=report,
            preflight_error=preflight_error,
        )

        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                cls._write_text(archive, "summary.txt", summary)
                cls._add_json_file(archive, Path(instance.instance_dir) / "instance.json", "instance/instance.json")
                cls._add_json_file(archive, Path(instance.instance_dir) / "settings.json", "instance/settings.json")
                if forge_version is not None:
                    cls._write_text(
                        archive,
                        "forge/profile.json",
                        json.dumps(forge_version.raw_json, ensure_ascii=False, indent=2) + "\n",
                    )
                snapshot = ForgeChangeManager.load_snapshot(instance)
                if snapshot is not None:
                    cls._write_text(
                        archive,
                        "forge/previous-installation.json",
                        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
                    )
                cls._add_forge_logs(archive, instance, loader_version)
                cls._write_mod_inventory(archive, instance)
                cls._add_runtime_logs(archive, instance)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return target

    @classmethod
    def _summary(
        cls,
        instance: Instance,
        launcher_version: str,
        loader_version: str,
        java_major: int,
        report: object | None,
        preflight_error: str,
    ) -> str:
        lines = [
            "MCW Launcher Forge Diagnostic Package",
            "=" * 37,
            f"schema_version: {cls.SCHEMA_VERSION}",
            f"generated_at: {datetime.now(timezone.utc).isoformat()}",
            f"launcher_version: {launcher_version}",
            f"instance_name: {instance.name}",
            f"instance_id: {instance.instance_id}",
            f"minecraft_version: {instance.version_id}",
            f"forge_version: {loader_version}",
            f"required_java_major: {java_major}",
            "",
            "Pre-launch check",
            "----------------",
        ]
        if report is not None:
            lines.append(report.format_summary())
            for issue in report.issues:
                lines.append(f"[{issue.severity.upper()}] {issue.code}: {issue.message}")
        elif preflight_error:
            lines.append(f"Could not complete pre-launch scan: {preflight_error}")
        else:
            lines.append("No pre-launch data available.")
        lines.extend([
            "",
            "Privacy",
            "-------",
            "This package excludes account databases, access tokens, refresh tokens, passwords, worlds, saves, and mod JAR contents.",
        ])
        return "\n".join(lines).rstrip() + "\n"

    @classmethod
    def _write_mod_inventory(cls, archive: zipfile.ZipFile, instance: Instance) -> None:
        mods = []
        for mod in ModManager.list_mods(instance):
            mods.append({
                "file_name": mod.file_name,
                "enabled": mod.enabled,
                "mod_id": mod.mod_id,
                "name": mod.name,
                "version": mod.version,
                "loader": mod.loader,
                "metadata_format": mod.metadata_format,
                "dependencies": mod.dependencies,
                "recommends": mod.recommends,
                "status": mod.status,
                "error": mod.error,
            })
        cls._write_text(archive, "mods/inventory.json", json.dumps(mods, ensure_ascii=False, indent=2) + "\n")

    @classmethod
    def _add_forge_logs(cls, archive: zipfile.ZipFile, instance: Instance, loader_version: str) -> None:
        roots = [Paths.forge_root() / "logs", Path(instance.instance_dir) / ".mcw" / "logs"]
        patterns = [
            f"*{instance.version_id}*{loader_version}*.log",
            "forge*.log",
        ]
        added: set[Path] = set()
        for root in roots:
            if not root.is_dir():
                continue
            candidates: list[Path] = []
            for pattern in patterns:
                candidates.extend(root.glob(pattern))
            for path in sorted(set(candidates), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:5]:
                if path in added or not path.is_file():
                    continue
                added.add(path)
                cls._add_text_file(archive, path, f"forge/logs/{path.name}")

    @classmethod
    def _add_runtime_logs(cls, archive: zipfile.ZipFile, instance: Instance) -> None:
        for relative, archive_name in (
            (Path("logs") / "latest.log", "minecraft/latest.log"),
            (Path(".mcw") / "minecraft.log", "minecraft/launcher-captured.log"),
        ):
            path = Path(instance.instance_dir) / relative
            if path.is_file():
                cls._add_text_file(archive, path, archive_name)

    @classmethod
    def _add_json_file(cls, archive: zipfile.ZipFile, path: Path, archive_name: str) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError):
            return
        safe = SensitiveDataRedactor.redact_value(data)
        cls._write_text(archive, archive_name, json.dumps(safe, ensure_ascii=False, indent=2) + "\n")

    @classmethod
    def _add_text_file(cls, archive: zipfile.ZipFile, path: Path, archive_name: str) -> None:
        try:
            raw = path.read_bytes()[-cls.MAX_TEXT_BYTES :]
            text = raw.decode("utf-8", errors="replace")
        except OSError:
            return
        cls._write_text(archive, archive_name, text)

    @staticmethod
    def _write_text(archive: zipfile.ZipFile, archive_name: str, content: str) -> None:
        safe = SensitiveDataRedactor.redact_text(content)
        archive.writestr(archive_name, safe.encode("utf-8"))
