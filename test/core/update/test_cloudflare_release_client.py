from pathlib import Path
from unittest.mock import MagicMock
import httpx
import pytest

from src.core.update.cloudflare_release_client import CloudflareReleaseClient


def cf_release(tag: str, prerelease: bool, assets: list[dict], draft: bool = False, notes: str = "notes") -> dict:
    return {
        "tag_name": tag,
        "name": tag,
        "notes": notes,
        "html_url": f"https://github.com/example/repo/releases/tag/{tag}",
        "published_at": "2026-10-18T00:00:00Z",
        "prerelease": prerelease,
        "draft": draft,
        "assets": assets,
    }


def cf_asset(name: str, size: int = 1234, digest: str | None = None, dl_url: str | None = None) -> dict:
    url = dl_url or f"https://mcw-download.pages.dev/releases/v/{name}"
    return {
        "name": name,
        "size": size,
        "digest": digest,
        "browser_download_url": url,
    }


def test_cloudflare_client_selects_update_from_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "cache.json"
    client = CloudflareReleaseClient(
        current_version="1.8.2",
        channel="stable",
        endpoint_url="https://mcw-download.pages.dev/releases/manifest.json",
        repository="example/repo",
        cache_path=cache,
        platform_id="windows-x64",
    )

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [
        cf_release(
            "v1.8.3",
            False,
            [
                cf_asset("MCW-Launcher-v1.8.3-windows-x64.zip", 5000, digest="sha256:" + "b" * 64),
                cf_asset("MCW-Launcher-v1.8.3-linux-x64.zip", 6000),
            ],
            notes="Stable release 1.8.3",
        ),
    ]

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    monkeypatch.setattr("src.core.network.httpx_downloader.HttpDownloader.get_client", lambda: mock_client)

    info = client.check(force_refresh=True)
    assert info is not None
    assert info.version == "1.8.3"
    assert info.tag_name == "v1.8.3"
    assert info.release_notes == "Stable release 1.8.3"
    assert info.asset.name == "MCW-Launcher-v1.8.3-windows-x64.zip"
    assert info.asset.download_url == "https://mcw-download.pages.dev/releases/v/MCW-Launcher-v1.8.3-windows-x64.zip"
    assert info.asset.sha256 == "b" * 64
    # Check that GitHub fallback mirror was automatically populated
    assert "https://github.com/example/repo/releases/download/v1.8.3/MCW-Launcher-v1.8.3-windows-x64.zip" in info.asset.mirror_urls


def test_cloudflare_client_selects_update_from_manifest_dict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "cache.json"
    client = CloudflareReleaseClient(
        current_version="1.8.2",
        channel="stable",
        endpoint_url="https://mcw-download.pages.dev/releases/manifest.json",
        repository="example/repo",
        cache_path=cache,
        platform_id="windows-x64",
    )

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "schema_version": 1,
        "service": "mcw-release-network",
        "updated_at": "2026-10-18T00:00:00Z",
        "releases": [
            {
                "version": "1.8.3",
                "tag_name": "v1.8.3",
                "title": "MCW Launcher 1.8.3",
                "notes": "Fast update notes",
                "prerelease": False,
                "assets": {
                    "windows-x64": {
                        "name": "MCW-Launcher-v1.8.3-windows-x64.zip",
                        "size": 75000000,
                        "url": "https://mcw-download.pages.dev/releases/v1.8.3/MCW-Launcher-v1.8.3-windows-x64.zip",
                        "digest": "sha256:" + "c" * 64,
                    }
                },
            }
        ],
    }

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    monkeypatch.setattr("src.core.network.httpx_downloader.HttpDownloader.get_client", lambda: mock_client)

    info = client.check(force_refresh=True)
    assert info is not None
    assert info.version == "1.8.3"
    assert info.title == "MCW Launcher 1.8.3"
    assert info.asset.name == "MCW-Launcher-v1.8.3-windows-x64.zip"
    assert info.asset.sha256 == "c" * 64
    assert info.asset.download_url == "https://mcw-download.pages.dev/releases/v1.8.3/MCW-Launcher-v1.8.3-windows-x64.zip"
    assert "https://github.com/example/repo/releases/download/v1.8.3/MCW-Launcher-v1.8.3-windows-x64.zip" in info.asset.mirror_urls


def test_cloudflare_client_uses_local_cache_when_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "cache.json"
    client = CloudflareReleaseClient(
        current_version="1.8.2",
        channel="stable",
        endpoint_url="https://mcw-download.pages.dev/releases/manifest.json",
        repository="example/repo",
        cache_path=cache,
        platform_id="windows-x64",
    )

    call_count = 0

    def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.json.return_value = [
            cf_release("v1.8.3", False, [cf_asset("MCW-Launcher-v1.8.3-windows-x64.zip", digest="sha256:" + "a" * 64)]),
        ]
        return resp

    mock_client = MagicMock()
    mock_client.get = mock_get
    monkeypatch.setattr("src.core.network.httpx_downloader.HttpDownloader.get_client", lambda: mock_client)

    info1 = client.check(force_refresh=False)
    assert info1 is not None
    assert call_count == 1

    # Second check without force_refresh uses cache: get client should not be called again
    info2 = client.check(force_refresh=False)
    assert info2 is not None
    assert call_count == 1


def test_cloudflare_client_raises_on_invalid_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "cache.json"
    client = CloudflareReleaseClient(
        current_version="1.8.2",
        channel="stable",
        endpoint_url="https://mcw-download.pages.dev/releases/manifest.json",
        repository="example/repo",
        cache_path=cache,
    )

    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = "invalid-non-dict-non-list"

    mock_client = MagicMock()
    mock_client.get.return_value = resp
    monkeypatch.setattr("src.core.network.httpx_downloader.HttpDownloader.get_client", lambda: mock_client)

    with pytest.raises(RuntimeError, match="invalid releases payload"):
        client.check(force_refresh=True)
