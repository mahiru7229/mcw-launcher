from types import SimpleNamespace

from src.core.curseforge.curseforge_links import (
    best_manual_download_url,
    file_download_url,
    file_page_url,
    is_numeric_project_placeholder,
    normalize_project_page,
    project_search_url,
)


def test_normalize_project_page_strips_file_suffix_and_legacy_host() -> None:
    assert normalize_project_page("https://legacy.curseforge.com/minecraft/mc-mods/jei/files/123?x=1") == "https://www.curseforge.com/minecraft/mc-mods/jei"


def test_numeric_project_placeholder_is_detected() -> None:
    url = "https://www.curseforge.com/minecraft/mc-mods/238222"
    assert is_numeric_project_placeholder(url, 238222)
    assert not is_numeric_project_placeholder("https://www.curseforge.com/minecraft/mc-mods/jei", 238222)


def test_file_page_uses_slug_project_url() -> None:
    assert file_page_url("https://www.curseforge.com/minecraft/mc-mods/jei", 5101366) == "https://www.curseforge.com/minecraft/mc-mods/jei/files/5101366"


def test_file_download_url_uses_slug_project_url() -> None:
    assert file_download_url("https://www.curseforge.com/minecraft/mc-mods/jei", 5101366) == "https://www.curseforge.com/minecraft/mc-mods/jei/download/5101366"


def test_curseforge_manual_link_prefers_download_countdown_page_over_failed_cdn() -> None:
    requirement = SimpleNamespace(
        provider="curseforge",
        direct_url="https://edge.forgecdn.net/files/old.jar",
        version_url="https://www.curseforge.com/minecraft/mc-mods/jei/files/5101366",
        project_url="https://www.curseforge.com/minecraft/mc-mods/jei",
        file_id=5101366,
    )
    assert best_manual_download_url(requirement) == "https://www.curseforge.com/minecraft/mc-mods/jei/download/5101366"


def test_curseforge_manual_link_falls_back_to_download_url_from_version_url() -> None:
    requirement = SimpleNamespace(
        provider="curseforge",
        version_url="https://www.curseforge.com/minecraft/mc-mods/jei/files/5101366",
    )
    assert best_manual_download_url(requirement) == "https://www.curseforge.com/minecraft/mc-mods/jei/download/5101366"


def test_non_curseforge_manual_link_keeps_direct_url_priority() -> None:
    requirement = SimpleNamespace(provider="modrinth", direct_url="https://cdn.modrinth.com/file.jar", version_url="https://modrinth.com/version/1", project_url="")
    assert best_manual_download_url(requirement) == "https://cdn.modrinth.com/file.jar"


def test_search_fallback_is_https_and_contains_project_id() -> None:
    assert project_search_url(238222) == "https://www.curseforge.com/minecraft/search?search=238222"

