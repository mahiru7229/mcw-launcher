from __future__ import annotations


def loader_version_entries(loader: str, versions: list[object], stable_suffix: str = "") -> list[tuple[str, str, bool]]:
    normalized_loader = str(loader or "").strip().casefold()
    entries: list[tuple[str, str, bool]] = []
    preferred_selected = False
    for version in versions:
        if normalized_loader in {"fabric", "quilt"}:
            value = str(getattr(version, "version", "") or "").strip()
            stable = bool(getattr(version, "stable", False))
            label = value + (stable_suffix if stable else "")
            preferred = stable and not preferred_selected
        elif normalized_loader == "forge":
            value = str(getattr(version, "forge_version", "") or "").strip()
            label = value
            preferred = not entries
        elif normalized_loader == "neoforge":
            value = str(getattr(version, "neoforge_version", "") or "").strip()
            label = value
            preferred = not entries
        else:
            continue
        if not value:
            continue
        entries.append((value, label, preferred))
        preferred_selected = preferred_selected or preferred
    return entries


def loader_title(loader: str) -> str:
    normalized = str(loader or "").strip().casefold()
    return {
        "fabric": "Fabric Loader",
        "quilt": "Quilt Loader",
        "forge": "Minecraft Forge",
        "neoforge": "NeoForge",
    }.get(normalized, normalized.title())
