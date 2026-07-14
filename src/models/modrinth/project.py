from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModrinthProject:
    project_id: str
    slug: str
    title: str
    description: str
    project_type: str
    author: str = ""
    downloads: int = 0
    icon_url: str = ""
    categories: tuple[str, ...] = ()
    versions: tuple[str, ...] = ()
    latest_version: str = ""
    client_side: str = "unknown"
    server_side: str = "unknown"
    date_modified: str = ""


@dataclass(frozen=True, slots=True)
class ModrinthSearchResult:
    projects: tuple[ModrinthProject, ...]
    total_hits: int
    offset: int
    limit: int
