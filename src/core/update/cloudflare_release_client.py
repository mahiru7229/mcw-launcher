from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from src.config import DEFAULT_CLOUDFLARE_RELEASES_URL, GITHUB_REPOSITORY
from src.core.fs.paths import Paths
from src.core.network.httpx_downloader import HttpDownloader
from src.core.update.base_release_client import BaseReleaseClient

logger = logging.getLogger(__name__)


class CloudflareReleaseClient(BaseReleaseClient):
    """Fetches launcher release manifests directly from Cloudflare Pages / Edge CDN.

    Provides unthrottled release evaluation to avoid GitHub API rate limits (HTTP 403),
    while automatically attaching GitHub download mirrors as secondary failover paths.
    """

    def __init__(
        self,
        current_version: str,
        channel: str = "stable",
        endpoint_url: str | None = None,
        repository: str = GITHUB_REPOSITORY,
        cache_path: Path | None = None,
        platform_id: str = "windows-x64",
    ) -> None:
        self.repository = str(repository).strip().strip("/")
        resolved_endpoint = (
            str(endpoint_url).strip()
            if endpoint_url
            else os.environ.get("MCW_CLOUDFLARE_RELEASES_URL", DEFAULT_CLOUDFLARE_RELEASES_URL).strip()
        )
        if not resolved_endpoint.startswith("https://") and not resolved_endpoint.startswith("http://"):
            raise ValueError(f"Cloudflare release endpoint must be an HTTP(S) URL: {resolved_endpoint!r}")

        self.endpoint_url = resolved_endpoint
        cache_file = (
            Path(cache_path)
            if cache_path is not None
            else Paths.update_release_cache().with_name("cloudflare_releases.json")
        )
        super().__init__(
            current_version=current_version,
            channel=channel,
            cache_path=cache_file,
            platform_id=platform_id,
            source_key=self.endpoint_url,
        )

    def _fetch_releases(self) -> list[dict[str, Any]]:
        client = HttpDownloader.get_client()
        response = client.get(
            self.endpoint_url,
            headers={
                "Accept": "application/json",
                "User-Agent": f"{self.repository}/{self.current_version} (Cloudflare-Release-Client)",
            },
            timeout=15.0,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except Exception as error:
            raise RuntimeError(f"Cloudflare releases endpoint returned invalid JSON: {error}") from error

        raw_releases = self._extract_releases_list(payload)
        return [self._normalize_release_item(item) for item in raw_releases if isinstance(item, dict)]

    @staticmethod
    def _extract_releases_list(payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for candidate_key in ("releases", "active_releases", "items", "data"):
                items = payload.get(candidate_key)
                if isinstance(items, list):
                    return items
            if "tag_name" in payload or "version" in payload:
                return [payload]
        raise RuntimeError("Cloudflare API returned an invalid releases payload format.")

    def _normalize_release_item(self, item: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(item)
        tag_name = str(normalized.get("tag_name") or "").strip()
        version = str(normalized.get("version") or "").strip()
        if not tag_name and version:
            tag_name = f"v{version}" if not version.startswith("v") else version
            normalized["tag_name"] = tag_name
        elif not version and tag_name:
            version = tag_name.removeprefix("v")
            normalized["version"] = version

        if not normalized.get("name") and normalized.get("title"):
            normalized["name"] = normalized["title"]
        if not normalized.get("body") and normalized.get("notes"):
            normalized["body"] = normalized["notes"]

        raw_assets = normalized.get("assets")
        if isinstance(raw_assets, dict):
            asset_list: list[dict[str, Any]] = []
            for plat_key, asset_info in raw_assets.items():
                if isinstance(asset_info, dict):
                    entry = dict(asset_info)
                    entry.setdefault("platform", plat_key)
                    asset_list.append(entry)
            raw_assets = asset_list

        if isinstance(raw_assets, list):
            normalized_assets: list[dict[str, Any]] = []
            for asset in raw_assets:
                if not isinstance(asset, dict):
                    continue
                asset_copy = dict(asset)
                name = str(asset_copy.get("name") or "").strip()
                dl_url = str(
                    asset_copy.get("browser_download_url")
                    or asset_copy.get("download_url")
                    or asset_copy.get("url")
                    or ""
                ).strip()
                if dl_url:
                    asset_copy["browser_download_url"] = dl_url

                # If asset doesn't explicitly declare mirrors, synthesize GitHub fallback mirror
                existing_mirrors = asset_copy.get("mirror_urls") or asset_copy.get("mirrors") or []
                if isinstance(existing_mirrors, (list, tuple)):
                    mirrors = list(existing_mirrors)
                elif isinstance(asset_copy.get("mirror_url"), str):
                    mirrors = [asset_copy["mirror_url"]]
                else:
                    mirrors = []

                if tag_name and name and self.repository:
                    github_fallback = f"https://github.com/{self.repository}/releases/download/{tag_name}/{name}"
                    if dl_url != github_fallback and github_fallback not in mirrors:
                        mirrors.append(github_fallback)

                asset_copy["mirror_urls"] = mirrors
                normalized_assets.append(asset_copy)
            normalized["assets"] = normalized_assets

        return normalized
