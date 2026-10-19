from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.fs.paths import Paths
from src.core.network.httpx_downloader import HttpDownloader
from src.core.update.base_release_client import BaseReleaseClient


class GitHubReleaseClient(BaseReleaseClient):
    API_ROOT = "https://api.github.com"

    def __init__(
        self,
        repository: str,
        current_version: str,
        channel: str = "stable",
        cache_path: Path | None = None,
        platform_id: str = "windows-x64",
    ) -> None:
        repository_name = str(repository).strip().strip("/")
        if repository_name.count("/") != 1:
            raise ValueError("GitHub repository must use the 'owner/name' format.")

        self.repository = repository_name
        cache_file = Path(cache_path) if cache_path is not None else Paths.update_release_cache()
        super().__init__(
            current_version=current_version,
            channel=channel,
            cache_path=cache_file,
            platform_id=platform_id,
            source_key=repository_name,
        )

    def _fetch_releases(self) -> list[dict[str, Any]]:
        client = HttpDownloader.get_client()
        response = client.get(
            f"{self.API_ROOT}/repos/{self.repository}/releases",
            params={"per_page": 30},
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": f"{self.repository}/{self.current_version}",
            },
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("GitHub returned an invalid releases response.")
        return [item for item in payload if isinstance(item, dict)]
