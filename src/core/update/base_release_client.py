from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

from src.core.fs.atomic_file import atomic_write_text
from src.core.update.versioning import LauncherVersion
from src.models.update import update_info as _update_info_mod
from src.models.update.update_info import ReleaseAsset, UpdateInfo

logger = logging.getLogger(__name__)


class BaseReleaseClient:
    """Base release client providing release evaluation, filtering, and cache lifecycle."""

    CACHE_SCHEMA_VERSION = 1
    CACHE_TTL_SECONDS = 15 * 60

    def __init__(
        self,
        current_version: str,
        channel: str = "stable",
        cache_path: Path | None = None,
        platform_id: str = "windows-x64",
        source_key: str = "",
    ) -> None:
        self.current_version = str(current_version).strip()
        self.channel = str(channel).strip().lower() or "stable"
        self.platform_id = self._normalize_platform_id(platform_id)
        self.cache_path = Path(cache_path) if cache_path is not None else None
        self.source_key = str(source_key).strip()

    def check(self, force_refresh: bool = False) -> UpdateInfo | None:
        releases = self._load_releases(force_refresh=force_refresh)
        return self._select_update(releases)

    def _load_releases(self, force_refresh: bool) -> list[dict[str, Any]]:
        cached = self._read_cache()
        if not force_refresh and cached is not None and not self._cache_expired(cached):
            payload = cached.get("releases")
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]

        try:
            releases = self._fetch_releases()
        except Exception:
            if cached is not None:
                payload = cached.get("releases")
                if isinstance(payload, list):
                    return [item for item in payload if isinstance(item, dict)]
            raise

        self._write_cache(releases)
        return releases

    def _fetch_releases(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _select_update(self, releases: list[dict[str, Any]]) -> UpdateInfo | None:
        current = LauncherVersion.parse(self.current_version)
        candidates: list[tuple[LauncherVersion, dict[str, Any], ReleaseAsset, str, bool]] = []

        for release in releases:
            if release.get("draft") is True:
                continue
            prerelease = bool(release.get("prerelease"))
            if self.channel == "stable" and prerelease:
                continue

            tag_name = str(release.get("tag_name") or "").strip()
            try:
                version = LauncherVersion.parse(tag_name)
            except ValueError:
                continue
            if self.channel == "beta" and version.prerelease in {"alpha", "pre"} and current.prerelease not in {"alpha", "pre"}:
                continue

            raw_assets = release.get("assets")
            is_emergency = self._release_is_emergency_hotfix(raw_assets)
            if not is_emergency and version <= current:
                continue
            if is_emergency and str(version) == str(current):
                continue

            asset = self._select_asset(raw_assets)
            if asset is None:
                continue
            strategy = "updater"
            if self._release_uses_bridge(raw_assets):
                bridge_asset = self._select_bridge_asset(raw_assets)
                if bridge_asset is None:
                    raise RuntimeError(
                        f"Release {tag_name} requests MCW Update Bridge, but no verified {self.platform_id} bridge asset is attached."
                    )
                asset = bridge_asset
                strategy = "bridge"
            candidates.append((version, release, asset, strategy, is_emergency))

        if not candidates:
            return None

        emergency_candidates = [c for c in candidates if c[4]]
        selection_pool = emergency_candidates if emergency_candidates else candidates
        version, release, asset, strategy, is_emergency = max(selection_pool, key=lambda item: item[0].comparison_key())
        return _update_info_mod.UpdateInfo(
            current_version=self.current_version,
            version=str(version),
            tag_name=str(release.get("tag_name") or version),
            title=str(release.get("name") or release.get("tag_name") or version),
            release_notes=str(release.get("body") or "").strip(),
            release_url=str(release.get("html_url") or ""),
            published_at=str(release.get("published_at") or release.get("created_at") or ""),
            prerelease=bool(release.get("prerelease")),
            asset=asset,
            install_strategy=strategy,
            emergency=is_emergency,
        )

    @staticmethod
    def _release_is_emergency_hotfix(raw_assets: object) -> bool:
        if not isinstance(raw_assets, list):
            return False
        return any(
            isinstance(item, dict)
            and str(item.get("name") or "").strip().casefold() in {"mcw-emergency-hotfix", "mcw-emergency-rollback"}
            for item in raw_assets
        )

    @staticmethod
    def _release_uses_bridge(raw_assets: object) -> bool:
        if not isinstance(raw_assets, list):
            return False
        return any(
            isinstance(item, dict) and str(item.get("name") or "").strip().casefold() == "mcw-use-bridge"
            for item in raw_assets
        )

    def _select_bridge_asset(self, raw_assets: object) -> ReleaseAsset | None:
        if not isinstance(raw_assets, list):
            return None
        candidates: list[dict[str, Any]] = []
        for item in raw_assets:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            lowered = name.casefold()
            url = str(
                item.get("browser_download_url")
                or item.get("download_url")
                or item.get("url")
                or ""
            ).strip()
            if not url.startswith("https://") or not lowered.startswith("mcw-update-bridge-"):
                continue
            if lowered.endswith(".sha256"):
                continue
            if self.platform_id == "windows-x64":
                if not lowered.endswith("-windows-x64.exe"):
                    continue
            elif not lowered.endswith("-linux-x64"):
                continue
            candidates.append(item)
        if len(candidates) != 1:
            return None
        raw_asset = candidates[0]
        name = str(raw_asset.get("name") or "")
        download_url = str(
            raw_asset.get("browser_download_url")
            or raw_asset.get("download_url")
            or raw_asset.get("url")
            or ""
        ).strip()
        digest = str(raw_asset.get("digest") or raw_asset.get("sha256") or "").strip().casefold()
        sha256 = (
            digest.removeprefix("sha256:")
            if digest.startswith("sha256:") and len(digest) == 71
            else (digest if len(digest) == 64 and all(character in "0123456789abcdef" for character in digest) else None)
        )
        sidecar_name = f"{name}.sha256".casefold()
        sha256_url = str(raw_asset.get("sha256_url") or "").strip() or None
        if sha256_url is None:
            for candidate in raw_assets:
                if not isinstance(candidate, dict):
                    continue
                if str(candidate.get("name") or "").strip().casefold() != sidecar_name:
                    continue
                candidate_url = str(
                    candidate.get("browser_download_url")
                    or candidate.get("download_url")
                    or candidate.get("url")
                    or ""
                ).strip()
                if candidate_url.startswith("https://"):
                    sha256_url = candidate_url
                    break
        if sha256 is None and sha256_url is None:
            return None

        mirror_urls: list[str] = []
        raw_mirrors = raw_asset.get("mirror_urls") or raw_asset.get("mirrors")
        if isinstance(raw_mirrors, (list, tuple)):
            for mirror in raw_mirrors:
                m_str = str(mirror or "").strip()
                if m_str.startswith("https://") and m_str != download_url and m_str not in mirror_urls:
                    mirror_urls.append(m_str)
        elif isinstance(raw_asset.get("mirror_url"), str):
            m_str = str(raw_asset.get("mirror_url") or "").strip()
            if m_str.startswith("https://") and m_str != download_url:
                mirror_urls.append(m_str)

        return _update_info_mod.ReleaseAsset(
            name=name,
            download_url=download_url,
            size=max(0, int(raw_asset.get("size") or 0)),
            sha256=sha256,
            sha256_url=sha256_url,
            mirror_urls=tuple(mirror_urls),
        )

    def _select_asset(self, raw_assets: object) -> ReleaseAsset | None:
        if not isinstance(raw_assets, list):
            return None

        scored: list[tuple[int, dict[str, Any]]] = []
        for raw_asset in raw_assets:
            if not isinstance(raw_asset, dict):
                continue
            name = str(raw_asset.get("name") or "").strip()
            download_url = str(
                raw_asset.get("browser_download_url")
                or raw_asset.get("download_url")
                or raw_asset.get("url")
                or ""
            ).strip()
            if not name.lower().endswith(".zip") or not download_url.startswith("https://"):
                continue

            lowered = name.casefold()
            if not self._asset_matches_platform(lowered):
                continue
            score = 20 if lowered.endswith(f"-{self.platform_id}.zip") else 10
            if "mcw" in lowered or "launcher" in lowered:
                score += 2
            if "legacy" in lowered or "bridge" in lowered:
                score -= 10
            scored.append((score, raw_asset))

        if not scored:
            return None

        raw_asset = max(scored, key=lambda item: item[0])[1]
        asset_name = str(raw_asset.get("name") or "update.zip")
        download_url = str(
            raw_asset.get("browser_download_url")
            or raw_asset.get("download_url")
            or raw_asset.get("url")
            or ""
        ).strip()
        digest = str(raw_asset.get("digest") or raw_asset.get("sha256") or "").strip().lower()
        sha256 = (
            digest.removeprefix("sha256:")
            if digest.startswith("sha256:") and len(digest) == 71
            else (digest if len(digest) == 64 and all(character in "0123456789abcdef" for character in digest) else None)
        )
        sidecar_name = f"{asset_name}.sha256".casefold()
        sha256_url = str(raw_asset.get("sha256_url") or "").strip() or None
        if sha256_url is None:
            for candidate in raw_assets:
                if not isinstance(candidate, dict):
                    continue
                if str(candidate.get("name") or "").strip().casefold() != sidecar_name:
                    continue
                candidate_url = str(
                    candidate.get("browser_download_url")
                    or candidate.get("download_url")
                    or candidate.get("url")
                    or ""
                ).strip()
                if candidate_url.startswith("https://"):
                    sha256_url = candidate_url
                    break

        mirror_urls: list[str] = []
        raw_mirrors = raw_asset.get("mirror_urls") or raw_asset.get("mirrors")
        if isinstance(raw_mirrors, (list, tuple)):
            for mirror in raw_mirrors:
                m_str = str(mirror or "").strip()
                if m_str.startswith("https://") and m_str != download_url and m_str not in mirror_urls:
                    mirror_urls.append(m_str)
        elif isinstance(raw_asset.get("mirror_url"), str):
            m_str = str(raw_asset.get("mirror_url") or "").strip()
            if m_str.startswith("https://") and m_str != download_url:
                mirror_urls.append(m_str)

        return _update_info_mod.ReleaseAsset(
            name=asset_name,
            download_url=download_url,
            size=max(0, int(raw_asset.get("size") or 0)),
            sha256=sha256,
            sha256_url=sha256_url,
            mirror_urls=tuple(mirror_urls),
        )

    @staticmethod
    def _normalize_platform_id(platform_id: str) -> str:
        normalized = str(platform_id or "").strip().casefold()
        if normalized not in {"windows-x64", "linux-x64"}:
            raise ValueError(f"Unsupported launcher update platform: {platform_id!r}")
        return normalized

    def _asset_matches_platform(self, lowered_name: str) -> bool:
        is_x64 = "x64" in lowered_name or "amd64" in lowered_name or "x86_64" in lowered_name
        if not is_x64:
            return False
        if self.platform_id == "windows-x64":
            return "windows" in lowered_name or "win-x64" in lowered_name
        return "linux" in lowered_name

    def _read_cache(self) -> dict[str, Any] | None:
        if self.cache_path is None:
            return None
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict) or payload.get("schema_version") != self.CACHE_SCHEMA_VERSION:
            return None
        key = payload.get("source_key") or payload.get("repository")
        if key != self.source_key:
            return None
        return payload

    def _write_cache(self, releases: list[dict[str, Any]]) -> None:
        if self.cache_path is None:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.CACHE_SCHEMA_VERSION,
            "source_key": self.source_key,
            "repository": self.source_key,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "releases": releases,
        }
        atomic_write_text(self.cache_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    def _cache_expired(self, payload: dict[str, Any]) -> bool:
        fetched_at = payload.get("fetched_at")
        if not isinstance(fetched_at, str):
            return True
        try:
            timestamp = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        except ValueError:
            return True
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)
        return age.total_seconds() >= self.CACHE_TTL_SECONDS
