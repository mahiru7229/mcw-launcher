from types import SimpleNamespace

from src.gui.loader_version_options import loader_title, loader_version_entries


def test_fabric_entries_prefer_first_stable_version() -> None:
    versions = [
        SimpleNamespace(version="0.16.0", stable=False),
        SimpleNamespace(version="0.15.11", stable=True),
        SimpleNamespace(version="0.15.10", stable=True),
    ]

    entries = loader_version_entries("fabric", versions, " (stable)")

    assert entries == [
        ("0.16.0", "0.16.0", False),
        ("0.15.11", "0.15.11 (stable)", True),
        ("0.15.10", "0.15.10 (stable)", False),
    ]


def test_forge_and_neoforge_entries_use_provider_version_fields() -> None:
    forge = loader_version_entries("forge", [SimpleNamespace(forge_version="47.3.0"), SimpleNamespace(forge_version="47.2.0")])
    neoforge = loader_version_entries("neoforge", [SimpleNamespace(neoforge_version="21.1.80")])

    assert forge == [("47.3.0", "47.3.0", True), ("47.2.0", "47.2.0", False)]
    assert neoforge == [("21.1.80", "21.1.80", True)]


def test_unknown_or_empty_loader_versions_are_ignored() -> None:
    assert loader_version_entries("vanilla", [SimpleNamespace(version="ignored")]) == []
    assert loader_version_entries("quilt", [SimpleNamespace(version="", stable=True)]) == []


def test_loader_titles_are_consistent() -> None:
    assert loader_title("forge") == "Minecraft Forge"
    assert loader_title("neoforge") == "NeoForge"
