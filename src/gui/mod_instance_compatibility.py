from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.models.instance.instance import Instance


class CompatibleModVersion(Protocol):
    version_number: str
    game_versions: tuple[str, ...]


def compatible_instances(instances: Iterable[Instance], version: CompatibleModVersion, loader: str) -> list[Instance]:
    """Return loader-compatible instances; provider game versions are advisory."""
    normalized_loader = normalize_supported_loader(loader)
    compatible: list[Instance] = []
    for instance in instances:
        instance_loader, _ = ModLoaderManager.normalize(instance.mod_loader)
        if instance_loader != normalized_loader:
            continue
        compatible.append(instance)
    return sorted(compatible, key=lambda item: item.name.casefold())


def normalize_supported_loader(loader: str) -> str:
    normalized = str(loader or "").strip().lower()
    if normalized not in {ModLoaderManager.FABRIC, ModLoaderManager.FORGE}:
        raise RuntimeError(f"Unsupported mod loader: {normalized or 'unknown'}")
    return normalized
