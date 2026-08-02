from src.models.minecraft.version import Version
from src.models.instance.instance import Instance
from src.models.progress.progress_callback import ProgressCallback
from src.models.instance.settings import InstanceSettings
from src.models.package.instance_package_preview import InstancePackagePreview
from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.core.fs.paths import Paths
from src.core.instance.settings_manager import SettingsManager
from src.core.package.package_manager import PackageManager
from src.config import VERSION_TAG

from pathlib import Path
from datetime import datetime, timezone
import json
import os
import re
import shutil
import uuid


class InstanceManager:
    METADATA_VERSION = 3
    DEFAULT_ICON = "grass_block"
    ICON_DIRECTORY = ".mcw"
    ICON_BASENAME = "instance-icon"
    ICON_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".ico"}
    MAX_ICON_BYTES = 8 * 1024 * 1024
    INSTANCE_NAME_PATTERN = re.compile(r'^[^<>:"/\\|?*\x00-\x1F]{1,80}$')
    WINDOWS_RESERVED_NAMES = {"con", "prn", "aux", "nul", *(f"com{index}" for index in range(1, 10)), *(f"lpt{index}" for index in range(1, 10))}

    @staticmethod
    def validate_name(value: str) -> str:
        name = str(value).strip()
        device_name = name.split(".", 1)[0].casefold()
        if not name or name in {".", ".."} or name.endswith((" ", ".")) or not InstanceManager.INSTANCE_NAME_PATTERN.fullmatch(name) or device_name in InstanceManager.WINDOWS_RESERVED_NAMES:
            raise RuntimeError("The instance name is not valid on Windows.")
        return name

    @staticmethod
    def _save_instance_metadata(instance: Instance) -> None:
        instance_dir = Path(instance.instance_dir)
        path = instance_dir / "instance.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, json.JSONDecodeError, ValueError):
            existing = {}
        if not isinstance(existing, dict):
            existing = {}

        now = datetime.now(timezone.utc).isoformat()
        created_at = str(existing.get("created_at") or now)
        last_played = str(instance.last_played or existing.get("last_played") or "")
        last_exit_code = instance.last_exit_code if instance.last_exit_code is not None else existing.get("last_exit_code")
        last_launch_crashed = bool(instance.last_launch_crashed)
        last_launch_state = str(existing.get("last_launch_state") or ("crashed" if last_launch_crashed else "finished" if last_played else "ready"))
        data = dict(existing)
        data.update({
            "id": instance.instance_id,
            "name": instance.name,
            "version_id": instance.version_id,
            "mod_loader": instance.mod_loader,
            "instance_dir": str(instance_dir),
            "created_at": created_at,
            "updated_at": now,
            "last_played": last_played,
            "last_exit_code": last_exit_code,
            "last_launch_crashed": last_launch_crashed,
            "last_launch_state": last_launch_state,
            "last_started_at": str(existing.get("last_started_at") or ""),
            "last_finished_at": str(existing.get("last_finished_at") or ""),
            "icon": str(instance.icon or existing.get("icon") or InstanceManager.DEFAULT_ICON),
            "notes": str(existing.get("notes") or ""),
            "launcher_version": VERSION_TAG,
            "metadata_version": InstanceManager.METADATA_VERSION,
        })

        temporary = path.with_name(f"{path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(data, indent=4, ensure_ascii=False) + "\n")
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)

    @staticmethod
    def _load_instance_metadata(path: Path) -> Instance:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise RuntimeError(f"Invalid instance metadata: {path}") from error
        return InstanceManager._parse_instance_metadata(data, path.parent, path)

    @staticmethod
    def _parse_instance_metadata(data: object, instance_dir: Path, source: object = "instance.json") -> Instance:
        try:
            if not isinstance(data, dict):
                raise ValueError("instance.json must contain an object.")
            instance_id = str(data["id"]).strip()
            name = str(data["name"]).strip()
            version_id = str(data["version_id"]).strip()
            raw_loader = data.get("mod_loader", ("vanilla", "-1"))
            if not instance_id or not name or not version_id or not isinstance(raw_loader, (list, tuple)) or len(raw_loader) != 2:
                raise ValueError("instance.json is missing required fields.")
            mod_loader = (str(raw_loader[0]).strip().lower() or "vanilla", str(raw_loader[1]).strip() or "-1")
            icon = str(data.get("icon") or InstanceManager.DEFAULT_ICON).strip() or InstanceManager.DEFAULT_ICON
            last_played = str(data.get("last_played") or "")
            raw_exit_code = data.get("last_exit_code")
            last_exit_code = int(raw_exit_code) if raw_exit_code is not None else None
            last_launch_crashed = bool(data.get("last_launch_crashed", False))
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError(f"Invalid instance metadata: {source}") from error
        return Instance(
            instance_id=instance_id,
            name=name,
            version_id=version_id,
            mod_loader=mod_loader,
            instance_dir=instance_dir,
            icon=icon,
            last_played=last_played,
            last_exit_code=last_exit_code,
            last_launch_crashed=last_launch_crashed,
        )

    @staticmethod
    def list_instances() -> list[Instance]:
        instances: list[Instance] = []

        root = Paths.instances_root()

        for instance_dir in root.iterdir():
            if not instance_dir.is_dir():
                continue

            metadata_path = instance_dir / "instance.json"

            if not metadata_path.exists():
                continue

            try:
                instance = InstanceManager.load(instance_dir.name)
            except RuntimeError:
                continue
            instances.append(instance)

        return instances

    @staticmethod
    def clone(
        source_name: str,
        new_name: str,
        include_saves: bool = False
    ) -> Instance:
        new_name = InstanceManager.validate_name(new_name)
        if not InstanceManager.is_instance_exist(source_name):
            raise RuntimeError(
                f"Instance '{source_name}' does not exist."
            )

        if InstanceManager.is_instance_exist(new_name):
            raise RuntimeError(
                f"Instance '{new_name}' already exists."
            )

        source_dir = Paths.load_instance_dir(source_name)
        target_dir = Paths.load_instance_dir(new_name)

        ignore = None

        if not include_saves:
            ignore = shutil.ignore_patterns(
                "saves",
                "logs",
                "crash-reports"
            )

        shutil.copytree(
            source_dir,
            target_dir,
            ignore=ignore
        )

        InstanceManager._reset_cloned_runtime_data(target_dir)
        instance = InstanceManager.load(new_name)

        instance.instance_id = str(uuid.uuid4())
        instance.name = new_name
        instance.instance_dir = target_dir

        InstanceManager._save_instance_metadata(instance)

        instances_data = InstanceManager._add_instances_data(
            InstanceManager._load_instances_data(),
            instance
        )
        InstanceManager._save_instances(instances_data)

        return instance


    @staticmethod
    def _reset_cloned_runtime_data(instance_dir: Path) -> None:
        metadata_path = instance_dir / "instance.json"
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            data = {}
        if isinstance(data, dict):
            data.update({
                "last_played": "",
                "total_play_time_seconds": 0,
                "last_exit_code": None,
                "last_launch_crashed": False,
                "last_launch_state": "ready",
                "last_started_at": "",
                "last_finished_at": "",
                "last_game_log": "",
                "last_crash_report": "",
            })
            temporary = metadata_path.with_name(f"{metadata_path.name}.tmp")
            temporary.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
            temporary.replace(metadata_path)
        mcw_dir = instance_dir / ".mcw"
        for filename in ("runtime-history.json", "last-repair.json"):
            try:
                (mcw_dir / filename).unlink(missing_ok=True)
            except OSError:
                pass

    @staticmethod
    def export(instance_name: str, output_path: Path, include_saves: bool = False, on_progress: ProgressCallback | None = None) -> Path:
        instance = InstanceManager.load(instance_name)

        return PackageManager.export_instance(instance, output_path, include_saves, on_progress)

    @staticmethod
    def set_icon(instance_name: str, source_path: Path) -> Instance:
        instance = InstanceManager.load(instance_name)
        source = Path(source_path).expanduser()
        if not source.is_file():
            raise RuntimeError("The selected instance icon does not exist.")
        extension = source.suffix.casefold()
        if extension not in InstanceManager.ICON_EXTENSIONS:
            raise RuntimeError("Unsupported instance icon format.")
        try:
            size = source.stat().st_size
        except OSError as error:
            raise RuntimeError("The selected instance icon cannot be read.") from error
        if size <= 0 or size > InstanceManager.MAX_ICON_BYTES:
            raise RuntimeError("Instance icons must be between 1 byte and 8 MiB.")

        icon_dir = Path(instance.instance_dir) / InstanceManager.ICON_DIRECTORY
        icon_dir.mkdir(parents=True, exist_ok=True)
        target = icon_dir / f"{InstanceManager.ICON_BASENAME}{extension}"
        temporary = target.with_name(f".{target.name}.tmp")
        source_resolved = source.resolve()
        target_resolved = target.resolve(strict=False)
        if source_resolved != target_resolved:
            try:
                with source.open("rb") as input_file, temporary.open("wb") as output_file:
                    shutil.copyfileobj(input_file, output_file, length=1024 * 1024)
                    output_file.flush()
                    os.fsync(output_file.fileno())
                temporary.replace(target)
            except Exception:
                temporary.unlink(missing_ok=True)
                raise

        for old_icon in icon_dir.glob(f"{InstanceManager.ICON_BASENAME}.*"):
            if old_icon != target:
                old_icon.unlink(missing_ok=True)

        instance.icon = target.relative_to(instance.instance_dir).as_posix()
        InstanceManager._save_instance_metadata(instance)
        return InstanceManager.load(instance.name)

    @staticmethod
    def reset_icon(instance_name: str) -> Instance:
        instance = InstanceManager.load(instance_name)
        icon_dir = Path(instance.instance_dir) / InstanceManager.ICON_DIRECTORY
        for old_icon in icon_dir.glob(f"{InstanceManager.ICON_BASENAME}.*"):
            old_icon.unlink(missing_ok=True)
        instance.icon = InstanceManager.DEFAULT_ICON
        InstanceManager._save_instance_metadata(instance)
        return InstanceManager.load(instance.name)

    @staticmethod
    def resolve_icon_path(instance: Instance) -> Path | None:
        value = str(instance.icon or "").strip()
        if not value or value == InstanceManager.DEFAULT_ICON:
            return None
        path = Path(value)
        if not path.is_absolute():
            path = Path(instance.instance_dir) / path
        return path if path.is_file() else None

    @staticmethod
    def inspect_import(package_path: Path) -> InstancePackagePreview:
        metadata, instance_data, settings_data = PackageManager.inspect_instance(Path(package_path))
        instance = InstanceManager._parse_instance_metadata(instance_data, Path(), package_path)
        instance.name = InstanceManager.validate_name(instance.name)
        if InstanceManager.is_instance_exist(instance.name):
            raise RuntimeError(f"Instance '{instance.name}' already exists.")
        return InstancePackagePreview(
            package_path=Path(package_path),
            name=instance.name,
            version_id=instance.version_id,
            mod_loader=instance.mod_loader,
            icon=instance.icon,
            settings=SettingsManager.normalize_dict(settings_data),
            has_package_settings=settings_data is not None,
            package_metadata=metadata,
        )

    @staticmethod
    def import_instance(
        package_path: Path,
        on_progress: ProgressCallback | None = None,
        settings_override: dict | InstanceSettings | None = None,
    ) -> Instance:
        temp_dir = Paths.instances_root() / "_import_temp"

        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        temp_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        try:
            PackageManager.extract(package_path, temp_dir, on_progress)

            metadata_files = list(
                temp_dir.rglob("instance.json")
            )

            if len(metadata_files) != 1:
                raise RuntimeError(
                    "Invalid package: missing or duplicated instance.json."
                )

            metadata_path = metadata_files[0]
            imported_dir = metadata_path.parent

            instance = InstanceManager._load_instance_metadata(
                metadata_path
            )
            instance.name = InstanceManager.validate_name(instance.name)

            if InstanceManager.is_instance_exist(instance.name):
                raise RuntimeError(
                    f"Instance '{instance.name}' already exists."
                )

            target_dir = Paths.load_instance_dir(instance.name)

            if settings_override is not None:
                SettingsManager.save_dict(instance, settings_override)
            elif (imported_dir / "settings.json").is_file():
                SettingsManager.save(instance, SettingsManager.load(instance))
            else:
                SettingsManager.save_dict(instance, InstanceManager.default_instance_settings())

            shutil.move(
                str(imported_dir),
                str(target_dir)
            )

            instance.instance_dir = target_dir
            InstanceManager._save_instance_metadata(instance)

            instances_data = InstanceManager._add_instances_data(
                InstanceManager._load_instances_data(),
                instance
            )
            InstanceManager._save_instances(instances_data)

            return instance

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    @staticmethod
    def rename(instance_name: str, new_name: str) -> Path:
        new_name = InstanceManager.validate_name(new_name)
        if not InstanceManager.is_instance_exist(instance_name):
            raise RuntimeError(
                f"Instance '{instance_name}' does not exist!"
            )

        if InstanceManager.is_instance_exist(new_name):
            raise RuntimeError(
                f"Instance '{new_name}' already exists!"
            )

        if instance_name == new_name:
            return Paths.load_instance_dir(instance_name)

        old_dir = Paths.load_instance_dir(instance_name)
        new_dir = Paths.load_instance_dir(new_name)

        old_dir.rename(new_dir)

        instance = InstanceManager.load(new_name)
        instance.name = new_name
        instance.instance_dir = new_dir

        InstanceManager._save_instance_metadata(instance)

        instances_data = InstanceManager._load_instances_data()

        for item in instances_data.get("instances", []):
            if item.get("name") == instance_name:
                item["name"] = new_name
                item["instance_dir"] = str(new_dir)
                break

        InstanceManager._save_instances(instances_data)

        return new_dir

    @staticmethod
    def load(name: str) -> Instance:
        instance_dir = Paths.load_instance_dir(name)
        metadata_path = instance_dir / "instance.json"

        if metadata_path.exists():
            instance = InstanceManager._load_instance_metadata(metadata_path)
            repaired = False

            if instance.name != name:
                instance.name = name
                repaired = True

            if Path(instance.instance_dir) != instance_dir:
                instance.instance_dir = instance_dir
                repaired = True

            if repaired:
                InstanceManager._save_instance_metadata(instance)

            return instance

        instance_data = InstanceManager._find_instance_data(name)

        if instance_data is None:
            raise RuntimeError(
                f"Instance '{name}' not found."
            )

        instance = InstanceManager._parse_instance(instance_data)
        instance.name = name
        instance.instance_dir = instance_dir

        InstanceManager._migrate_instance(instance)

        return instance

    @staticmethod
    def _migrate_instance(instance: Instance) -> None:
        InstanceManager._save_instance_metadata(instance)

    @staticmethod
    def create(
        name: str,
        version: Version,
        mod_loader=("vanilla", "-1"),
        settings: dict | InstanceSettings | None = None,
    ) -> Instance:
        name = InstanceManager.validate_name(name)
        if InstanceManager.is_instance_exist(name):
            raise RuntimeError(
                f"Instance '{name}' already exists."
            )

        Paths.instances_root()
        Paths.instance_data_path_create()
        Paths.create_instance_dir(name)

        instance = InstanceManager._add_instance(
            name,
            version,
            mod_loader
        )

        instances_data = InstanceManager._add_instances_data(
            InstanceManager._load_instances_data(),
            instance
        )
        InstanceManager._save_instances(instances_data)

        InstanceManager._save_instance_metadata(instance)
        SettingsManager.save_dict(instance, settings if settings is not None else InstanceManager.default_instance_settings())

        return instance

    @staticmethod
    def default_instance_settings() -> dict:
        try:
            settings = LauncherSettingsManager().load().get("instance_defaults")
        except (OSError, RuntimeError, TypeError, ValueError):
            settings = None
        return SettingsManager.normalize_dict(settings)

    @staticmethod
    def set_runtime_profile(name: str, version: Version, mod_loader: tuple[str, str]) -> Instance:
        instance = InstanceManager.load(name)
        normalized_loader = (str(mod_loader[0]).strip().lower(), str(mod_loader[1]).strip())
        if normalized_loader[0] == "vanilla":
            normalized_loader = ("vanilla", "-1")
        instance.version_id = version.id
        instance.mod_loader = normalized_loader
        InstanceManager._save_instance_metadata(instance)
        instances_data = InstanceManager._load_instances_data()
        for item in instances_data.get("instances", []):
            if item.get("name") == name:
                item["version_id"] = version.id
                item["mod_loader"] = normalized_loader
                item["instance_dir"] = str(instance.instance_dir)
                break
        InstanceManager._save_instances(instances_data)
        return instance

    @staticmethod
    def set_mod_loader(name: str, mod_loader: tuple[str, str]) -> Instance:
        instance = InstanceManager.load(name)
        normalized_loader = (str(mod_loader[0]).strip().lower(), str(mod_loader[1]).strip())

        if normalized_loader[0] == "vanilla":
            normalized_loader = ("vanilla", "-1")

        instance.mod_loader = normalized_loader
        InstanceManager._save_instance_metadata(instance)

        instances_data = InstanceManager._load_instances_data()
        for item in instances_data.get("instances", []):
            if item.get("name") == name:
                item["mod_loader"] = normalized_loader
                break
        InstanceManager._save_instances(instances_data)
        return instance

    @staticmethod
    def delete_instance(name: str) -> bool:
        if not InstanceManager.is_instance_exist(name):
            return False

        instance_dir = Paths.load_instance_dir(name)

        if instance_dir.exists():
            shutil.rmtree(instance_dir)

        Paths.instances_root()
        Paths.instance_data_path_create()

        instances_data = InstanceManager._load_instances_data()

        instances_data["instances"] = [
            inst for inst in instances_data.get("instances", [])
            if inst.get("name") != name
        ]

        InstanceManager._save_instances(instances_data)

        return True

    @staticmethod
    def next_available_name(preferred_name: str) -> str:
        base_name = InstanceManager.validate_name(str(preferred_name).strip() or "New Instance")
        try:
            existing_names = {instance.name.casefold() for instance in InstanceManager.list_instances()}
        except Exception:
            existing_names = set()

        def is_taken(candidate: str) -> bool:
            return candidate.casefold() in existing_names or Paths.load_instance_dir(candidate).exists() or InstanceManager.is_instance_exist(candidate)

        if not is_taken(base_name):
            return base_name
        suffix = 2
        while True:
            candidate = f"{base_name} ({suffix})"
            if not is_taken(candidate):
                return candidate
            suffix += 1

    @staticmethod
    def is_instance_exist(name: str) -> bool:
        metadata_path = Paths.instance_metadata(name)

        if metadata_path.exists():
            return True

        return InstanceManager._find_instance_data(name) is not None

    @staticmethod
    def _find_instance_data(name: str) -> dict | None:
        instances_data = InstanceManager._load_instances_data()

        for instance in instances_data.get("instances", []):
            if instance.get("name") == name:
                return instance

        return None

    @staticmethod
    def _add_instance(
        name: str,
        version: Version,
        mod_loader: tuple
    ) -> Instance:
        return Instance(
            instance_id=str(uuid.uuid4()),
            name=name,
            version_id=version.id,
            mod_loader=mod_loader,
            instance_dir=Paths.load_instance_dir(name)
        )

    @staticmethod
    def _parse_instance(instance_data: dict) -> Instance:
        return Instance(
            instance_id=instance_data.get("id")
            or instance_data.get("instance_id")
            or str(uuid.uuid4()),
            name=instance_data.get("name"),
            version_id=instance_data.get("version_id"),
            mod_loader=instance_data.get("mod_loader"),
            instance_dir=Paths.load_instance_dir(instance_data.get("name")),
            icon=str(instance_data.get("icon") or InstanceManager.DEFAULT_ICON),
            last_played=str(instance_data.get("last_played") or ""),
            last_exit_code=instance_data.get("last_exit_code"),
            last_launch_crashed=bool(instance_data.get("last_launch_crashed", False)),
        )

    @staticmethod
    def _load_instances_data() -> dict:
        try:
            data = json.loads(Paths.instance_data_path().read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            return {"instances": []}
        if not isinstance(data, dict) or not isinstance(data.get("instances", []), list):
            return {"instances": []}
        return data

    @staticmethod
    def _add_instances_data(
        pre_data: dict,
        instance_data: Instance
    ) -> dict:
        if "instances" not in pre_data:
            pre_data["instances"] = []

        pre_data["instances"].append(
            {
                "id": instance_data.instance_id,
                "name": instance_data.name,
                "version_id": instance_data.version_id,
                "mod_loader": instance_data.mod_loader,
                "instance_dir": str(instance_data.instance_dir)
            }
        )

        return pre_data

    @staticmethod
    def _save_instances(data: dict) -> Path:
        instance_data_path = Paths.instance_data_path()
        instance_data_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = instance_data_path.with_name(f"{instance_data_path.name}.tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as file:
                file.write(json.dumps(data, indent=4, ensure_ascii=False) + "\n")
                file.flush()
                os.fsync(file.fileno())
            temporary.replace(instance_data_path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return instance_data_path
