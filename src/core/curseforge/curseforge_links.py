from __future__ import annotations

import re
from urllib.parse import quote_plus, urlparse, urlunparse

_ALLOWED_HOSTS = {"curseforge.com", "www.curseforge.com", "legacy.curseforge.com"}
_PROJECT_CATEGORIES = {"mc-mods", "modpacks", "texture-packs", "shaders"}


def normalize_project_page(url: object) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
    except ValueError:
        return ""
    host = str(parsed.hostname or "").casefold()
    if parsed.scheme.casefold() != "https" or host not in _ALLOWED_HOSTS or parsed.username or parsed.password:
        return ""
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[0].casefold() != "minecraft" or parts[1].casefold() not in _PROJECT_CATEGORIES:
        return ""
    project_parts = parts[:3]
    if not project_parts[2]:
        return ""
    return urlunparse(("https", "www.curseforge.com", "/" + "/".join(project_parts), "", "", ""))


def is_numeric_project_placeholder(url: object, project_id: int | str) -> bool:
    normalized = normalize_project_page(url)
    if not normalized:
        return False
    return normalized.rstrip("/").rsplit("/", 1)[-1] == str(project_id).strip()


def project_search_url(project_id: int | str) -> str:
    identifier = str(project_id).strip()
    return f"https://www.curseforge.com/minecraft/search?search={quote_plus(identifier)}" if identifier else "https://www.curseforge.com/minecraft"


def file_page_url(project_url: object, file_id: int | str) -> str:
    project_page = normalize_project_page(project_url)
    identifier = str(file_id).strip()
    if project_page and identifier:
        return f"{project_page}/files/{identifier}"
    return str(project_url or "").strip()


def file_download_url(project_url: object, file_id: int | str) -> str:
    project_page = normalize_project_page(project_url)
    identifier = str(file_id).strip()
    if project_page and identifier:
        return f"{project_page}/download/{identifier}"
    return str(project_url or "").strip()


def best_manual_download_url(requirement: object) -> str:
    provider = str(getattr(requirement, "provider", "") or "").strip().casefold()
    direct_url = str(getattr(requirement, "direct_url", "") or "").strip()
    version_url = str(getattr(requirement, "version_url", "") or "").strip()
    project_url = str(getattr(requirement, "project_url", "") or "").strip()
    file_id = getattr(requirement, "file_id", getattr(requirement, "version_id", None))
    file_id_str = str(file_id).strip() if file_id is not None else ""

    if provider == "curseforge":
        # Prefer the CurseForge download countdown page so the user doesn't have
        # to search for the download button.
        candidate_project = normalize_project_page(project_url) or normalize_project_page(version_url)
        if not file_id_str and version_url:
            match = re.search(r"/(?:files|download)/(\d+)", version_url)
            if match:
                file_id_str = match.group(1)

        if candidate_project and file_id_str:
            return file_download_url(candidate_project, file_id_str)
        if candidate_project:
            return candidate_project
        if version_url:
            return re.sub(r"/files/(\d+)", r"/download/\1", version_url)
        return project_url or direct_url

    return direct_url or version_url or project_url
