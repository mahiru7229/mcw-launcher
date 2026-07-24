from __future__ import annotations

from pathlib import Path
from typing import Iterable
import json
import re
import shutil
import tomllib
import zipfile

from src.core.fs.paths import Paths
from src.core.instance.errors import InstanceModChangeBlockedError
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.models.instance.instance import Instance
from src.models.mod.mod_info import ModInfo


class ModManager:
    DISABLED_SUFFIX = ".disabled"
    _INVALID_STATUSES = {"Broken JAR", "Not a mod", "Broken metadata"}

    @staticmethod
    def mods_dir(instance: Instance) -> Path:
        return Paths.instance_mods_dir(instance)

    @staticmethod
    def list_mods(instance: Instance) -> list[ModInfo]:
        directory = ModManager.mods_dir(instance)
        paths = [path for path in directory.iterdir() if path.is_file() and ModManager._is_mod_file(path)]
        return sorted((ModManager.read_mod(path) for path in paths), key=lambda mod: (not mod.enabled, mod.name.casefold(), mod.file_name.casefold()))

    @staticmethod
    def add_mods(instance: Instance, source_paths: Iterable[Path], replace: bool = False) -> list[ModInfo]:
        ModManager._ensure_modifiable(instance)
        destination_dir = ModManager.mods_dir(instance)
        installed = ModManager.list_mods(instance)
        added: list[ModInfo] = []

        for source_value in source_paths:
            source = Path(source_value)
            if not source.is_file() or source.suffix.lower() != ".jar":
                raise RuntimeError(f"Mod file must be a .jar file: {source.name}")

            metadata = ModManager.read_mod(source)
            ModManager._validate_mod_for_instance(instance, metadata)

            destination = destination_dir / source.name
            disabled_destination = destination.with_name(destination.name + ModManager.DISABLED_SUFFIX)
            source_resolved = source.resolve()
            destination_resolved = destination.resolve()

            if source_resolved == destination_resolved:
                if not replace:
                    raise FileExistsError(f"Mod already exists: {source.name}")
                added.append(ModManager.read_mod(destination))
                continue

            same_id = [
                mod for mod in installed
                if mod.mod_id != "unknown" and mod.mod_id.casefold() == metadata.mod_id.casefold() and mod.path.resolve() != source_resolved
            ]
            file_conflicts = [path for path in (destination, disabled_destination) if path.exists()]
            if (same_id or file_conflicts) and not replace:
                if same_id:
                    files = ", ".join(mod.file_name for mod in same_id)
                    raise FileExistsError(f"Mod ID '{metadata.mod_id}' is already installed as: {files}")
                raise FileExistsError(f"Mod already exists: {source.name}")

            temporary_path = destination.with_name(destination.name + ".part")
            try:
                shutil.copy2(source, temporary_path)
                copied = ModManager.read_mod(temporary_path)
                ModManager._validate_mod_for_instance(instance, copied)

                for conflict in same_id:
                    conflict.path.unlink(missing_ok=True)
                disabled_destination.unlink(missing_ok=True)
                temporary_path.replace(destination)
            finally:
                temporary_path.unlink(missing_ok=True)

            installed = [mod for mod in installed if mod.mod_id.casefold() != metadata.mod_id.casefold()]
            installed_mod = ModManager.read_mod(destination)
            installed.append(installed_mod)
            added.append(installed_mod)

        return added

    @staticmethod
    def remove_mods(instance: Instance, paths: Iterable[Path]) -> None:
        ModManager._ensure_modifiable(instance)
        directory = ModManager.mods_dir(instance).resolve()

        for path in paths:
            candidate = Path(path).resolve()
            if candidate.parent != directory:
                raise RuntimeError("Refusing to remove a file outside the instance mods folder.")
            candidate.unlink(missing_ok=True)

    @staticmethod
    def set_enabled(instance: Instance, paths: Iterable[Path], enabled: bool) -> list[ModInfo]:
        ModManager._ensure_modifiable(instance)
        directory = ModManager.mods_dir(instance).resolve()
        changed: list[ModInfo] = []

        for path in paths:
            source = Path(path).resolve()
            if source.parent != directory or not source.exists():
                raise RuntimeError("Mod file no longer exists in this instance.")

            currently_enabled = not source.name.endswith(ModManager.DISABLED_SUFFIX)
            if currently_enabled == enabled:
                changed.append(ModManager.read_mod(source))
                continue

            target = source.with_name(source.name[:-len(ModManager.DISABLED_SUFFIX)]) if enabled else source.with_name(source.name + ModManager.DISABLED_SUFFIX)
            if target.exists():
                raise FileExistsError(f"Cannot change mod state because '{target.name}' already exists.")

            source.replace(target)
            changed.append(ModManager.read_mod(target))

        return changed

    @staticmethod
    def read_mod(path: Path) -> ModInfo:
        path = Path(path)
        enabled = not path.name.endswith(ModManager.DISABLED_SUFFIX)
        file_name = path.name[:-len(ModManager.DISABLED_SUFFIX)] if not enabled else path.name

        try:
            with zipfile.ZipFile(path, "r") as archive:
                names = set(archive.namelist())
                if "fabric.mod.json" in names:
                    return ModManager._read_fabric_mod(path, file_name, enabled, archive.read("fabric.mod.json"))
                if "META-INF/neoforge.mods.toml" in names:
                    return ModManager._read_forge_mod(path, file_name, enabled, archive.read("META-INF/neoforge.mods.toml"), loader="neoforge", metadata_format="neoforge.mods.toml")
                if "META-INF/mods.toml" in names:
                    return ModManager._read_forge_mod(path, file_name, enabled, archive.read("META-INF/mods.toml"), loader="forge", metadata_format="mods.toml")
                if "mcmod.info" in names:
                    return ModManager._read_legacy_forge_mod(path, file_name, enabled, archive.read("mcmod.info"))
                return ModManager._invalid_mod(
                    path,
                    file_name,
                    enabled,
                    "Not a mod",
                    "No fabric.mod.json, Forge META-INF/mods.toml, NeoForge metadata, or mcmod.info metadata was found.",
                )
        except (OSError, zipfile.BadZipFile) as error:
            return ModManager._invalid_mod(path, file_name, enabled, "Broken JAR", str(error))

    @staticmethod
    def _read_fabric_mod(path: Path, file_name: str, enabled: bool, raw_metadata: bytes) -> ModInfo:
        try:
            data = json.loads(raw_metadata.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as error:
            return ModManager._invalid_mod(path, file_name, enabled, "Broken JAR", f"Invalid fabric.mod.json: {error}")
        if not isinstance(data, dict):
            return ModManager._invalid_mod(path, file_name, enabled, "Broken JAR", "fabric.mod.json must contain an object.")

        mod_id = str(data.get("id") or "").strip()
        version = str(data.get("version") or "Unknown").strip()
        name = str(data.get("name") or mod_id or Path(file_name).stem).strip()
        environment = str(data.get("environment") or "*").strip()
        status = "Server only" if environment == "server" else "Ready"
        error = "This mod declares a server-only environment." if environment == "server" else ""
        if not mod_id:
            status = "Broken metadata"
            error = "Fabric mod id is missing."
        return ModInfo(
            path=path,
            file_name=file_name,
            enabled=enabled,
            mod_id=mod_id or "unknown",
            name=name,
            version=version,
            loader="fabric",
            metadata_format="fabric.mod.json",
            description=str(data.get("description") or "").strip(),
            environment=environment,
            authors=ModManager._parse_authors(data.get("authors")),
            licenses=ModManager._parse_licenses(data.get("license")),
            dependencies=dict(data.get("depends") or {}) if isinstance(data.get("depends"), dict) else {},
            recommends=dict(data.get("recommends") or {}) if isinstance(data.get("recommends"), dict) else {},
            suggests=dict(data.get("suggests") or {}) if isinstance(data.get("suggests"), dict) else {},
            conflicts=dict(data.get("conflicts") or {}) if isinstance(data.get("conflicts"), dict) else {},
            breaks=dict(data.get("breaks") or {}) if isinstance(data.get("breaks"), dict) else {},
            status=status,
            error=error,
        )

    @staticmethod
    def _read_forge_mod(path: Path, file_name: str, enabled: bool, raw_metadata: bytes, loader: str, metadata_format: str) -> ModInfo:
        try:
            data = tomllib.loads(raw_metadata.decode("utf-8-sig"))
        except (UnicodeError, tomllib.TOMLDecodeError) as error:
            return ModManager._invalid_mod(path, file_name, enabled, "Broken JAR", f"Invalid Forge mods.toml: {error}", loader=loader, metadata_format=metadata_format)

        mods = data.get("mods") if isinstance(data.get("mods"), list) else []
        metadata = next((item for item in mods if isinstance(item, dict)), {})
        mod_id = str(metadata.get("modId") or "").strip()
        name = str(metadata.get("displayName") or mod_id or Path(file_name).stem).strip()
        version = str(metadata.get("version") or "Unknown").strip()
        authors = ModManager._parse_authors(metadata.get("authors"))
        license_value = data.get("license") or metadata.get("license")
        if not mod_id:
            return ModManager._invalid_mod(path, file_name, enabled, "Broken metadata", "Forge mod id is missing.", loader=loader, metadata_format=metadata_format)

        dependencies, recommends = ModManager._forge_dependencies(data, mod_id)
        loader_requirement = str(data.get("loaderVersion") or "").strip()
        loader_dependency = "neoforge" if loader == "neoforge" else "forge"
        if loader_requirement:
            dependencies.setdefault(loader_dependency, loader_requirement)

        return ModInfo(
            path=path,
            file_name=file_name,
            enabled=enabled,
            mod_id=mod_id,
            name=name,
            version=version,
            loader=loader,
            metadata_format=metadata_format,
            description=str(metadata.get("description") or "").strip(),
            environment="*",
            authors=authors,
            licenses=ModManager._parse_licenses(license_value),
            dependencies=dependencies,
            recommends=recommends,
            suggests={},
            conflicts={},
            breaks={},
            status="Ready",
            error="",
        )

    @staticmethod
    def _read_legacy_forge_mod(path: Path, file_name: str, enabled: bool, raw_metadata: bytes) -> ModInfo:
        try:
            data = json.loads(raw_metadata.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as error:
            return ModManager._invalid_mod(path, file_name, enabled, "Broken JAR", f"Invalid mcmod.info: {error}", loader="forge", metadata_format="mcmod.info")

        if isinstance(data, dict):
            entries = data.get("modList") if isinstance(data.get("modList"), list) else [data]
        elif isinstance(data, list):
            entries = data
        else:
            entries = []
        metadata = next((item for item in entries if isinstance(item, dict)), {})
        mod_id = str(metadata.get("modid") or metadata.get("modId") or "").strip()
        if not mod_id:
            return ModManager._invalid_mod(path, file_name, enabled, "Broken metadata", "Legacy Forge mod id is missing.", loader="forge", metadata_format="mcmod.info")

        dependencies, recommends = ModManager._legacy_forge_dependencies(metadata)
        minecraft_version = str(metadata.get("mcversion") or "").strip()
        if minecraft_version and minecraft_version.casefold() not in {"unknown", "*"}:
            dependencies.setdefault("minecraft", minecraft_version)

        return ModInfo(
            path=path,
            file_name=file_name,
            enabled=enabled,
            mod_id=mod_id,
            name=str(metadata.get("name") or mod_id).strip(),
            version=str(metadata.get("version") or "Unknown").strip(),
            loader="forge",
            metadata_format="mcmod.info",
            description=str(metadata.get("description") or "").strip(),
            environment="*",
            authors=ModManager._parse_authors(metadata.get("authorList") or metadata.get("authors")),
            licenses=ModManager._parse_licenses(metadata.get("license")),
            dependencies=dependencies,
            recommends=recommends,
            suggests={},
            conflicts={},
            breaks={},
            status="Ready",
            error="",
        )

    @staticmethod
    def _forge_dependencies(data: dict, mod_id: str) -> tuple[dict[str, object], dict[str, object]]:
        required: dict[str, object] = {}
        optional: dict[str, object] = {}
        groups = data.get("dependencies") if isinstance(data.get("dependencies"), dict) else {}
        entries = groups.get(mod_id) if isinstance(groups.get(mod_id), list) else []
        if not entries:
            entries = next((value for value in groups.values() if isinstance(value, list)), [])
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            dependency_id = str(entry.get("modId") or "").strip()
            if not dependency_id or dependency_id.casefold() == mod_id.casefold():
                continue
            requirement = str(entry.get("versionRange") or "*").strip() or "*"
            target = required if bool(entry.get("mandatory", True)) else optional
            target[dependency_id] = requirement
        return required, optional

    @staticmethod
    def _legacy_forge_dependencies(metadata: dict) -> tuple[dict[str, object], dict[str, object]]:
        required: dict[str, object] = {}
        optional: dict[str, object] = {}
        raw_values: list[object] = []
        for key in ("requiredMods", "dependencies", "dependants"):
            value = metadata.get(key)
            if isinstance(value, list):
                raw_values.extend(value)
            elif isinstance(value, str):
                raw_values.extend(part.strip() for part in value.split(";") if part.strip())

        for value in raw_values:
            token = str(value).strip()
            if not token:
                continue
            mandatory = token.casefold().startswith(("required-after:", "required-before:"))
            token = re.sub(r"^(?:required-)?(?:after|before):", "", token, flags=re.IGNORECASE)
            match = re.match(r"(?P<id>[A-Za-z0-9_.-]+)(?:@(?P<range>.+))?", token)
            if match is None:
                continue
            dependency_id = match.group("id")
            requirement = (match.group("range") or "*").strip()
            (required if mandatory else optional)[dependency_id] = requirement
        return required, optional

    @staticmethod
    def _validate_mod_for_instance(instance: Instance, mod: ModInfo) -> None:
        if mod.status in ModManager._INVALID_STATUSES:
            raise RuntimeError(mod.error or f"'{mod.file_name}' is not a supported Minecraft mod.")
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        if mod.loader not in {loader_name, "unknown", "universal"}:
            expected = loader_name.title()
            actual = mod.loader.title()
            raise RuntimeError(f"'{mod.file_name}' is a {actual} mod and cannot be added to this {expected} instance.")

    @staticmethod
    def _ensure_modifiable(instance: Instance) -> None:
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        if loader_name not in {ModLoaderManager.FABRIC, ModLoaderManager.FORGE}:
            raise RuntimeError("This instance does not use Fabric or Forge.")
        if InstanceRunLock.is_active(instance):
            raise InstanceModChangeBlockedError(instance.name)

    @staticmethod
    def _is_mod_file(path: Path) -> bool:
        lower_name = path.name.lower()
        return lower_name.endswith(".jar") or lower_name.endswith(".jar" + ModManager.DISABLED_SUFFIX)

    @staticmethod
    def _parse_authors(value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(part.strip() for part in re.split(r"[,;]", value) if part.strip())
        if not isinstance(value, list):
            return ()
        authors: list[str] = []
        for author in value:
            if isinstance(author, str) and author.strip():
                authors.append(author.strip())
            elif isinstance(author, dict):
                name = str(author.get("name") or "").strip()
                if name:
                    authors.append(name)
        return tuple(authors)

    @staticmethod
    def _parse_licenses(value: object) -> tuple[str, ...]:
        if isinstance(value, str) and value.strip():
            return (value.strip(),)
        if isinstance(value, list):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return ()

    @staticmethod
    def _invalid_mod(path: Path, file_name: str, enabled: bool, status: str, error: str, loader: str = "unknown", metadata_format: str = "unknown") -> ModInfo:
        return ModInfo(path=path, file_name=file_name, enabled=enabled, mod_id="unknown", name=Path(file_name).stem, version="Unknown", loader=loader, metadata_format=metadata_format, status=status, error=error)
