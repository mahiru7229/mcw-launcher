from __future__ import annotations

from pathlib import Path
import json

from src.core.fs.paths import Paths
from src.models.instance.instance import Instance


class ModrinthRegistry:
    SCHEMA_VERSION = 1

    @staticmethod
    def load(instance: Instance) -> dict:
        path = Paths.modrinth_instance_registry(instance)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {"schemaVersion": ModrinthRegistry.SCHEMA_VERSION, "mods": {}}
        if not isinstance(data, dict) or data.get("schemaVersion") != ModrinthRegistry.SCHEMA_VERSION:
            return {"schemaVersion": ModrinthRegistry.SCHEMA_VERSION, "mods": {}}
        if not isinstance(data.get("mods"), dict):
            data["mods"] = {}
        return data

    @staticmethod
    def save(instance: Instance, data: dict) -> None:
        path = Paths.modrinth_instance_registry(instance)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {**data, "schemaVersion": ModrinthRegistry.SCHEMA_VERSION}
        temp = path.with_suffix(path.suffix + ".part")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    @staticmethod
    def safe_tracked_path(instance: Instance, filename: str) -> Path | None:
        directory = Paths.instance_mods_dir(instance).resolve()
        candidate = (directory / Path(filename).name).resolve()
        if candidate.parent != directory:
            return None
        return candidate
