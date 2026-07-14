from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse
from typing import Any
import re

from src.core.java.java_major_policy import JavaMajorPolicy
from src.core.network.httpx_downloader import HttpDownloader
from src.models.java.java_release import JavaRelease


class AdoptiumClient:
    ASSETS_URL = "https://api.adoptium.net/v3/assets/latest/{major}/hotspot"
    ASSETS_PARAMS = {
        "architecture": "x64",
        "heap_size": "normal",
        "image_type": "jdk",
        "jvm_impl": "hotspot",
        "os": "windows",
        "project": "jdk",
        "vendor": "eclipse",
    }

    @staticmethod
    def get_latest_windows_x64_jdk(major: int, timeout: float = 30.0) -> JavaRelease:
        managed_major = JavaMajorPolicy.resolve(major)
        api_url = AdoptiumClient.ASSETS_URL.format(major=managed_major)
        client = HttpDownloader.get_client()
        response = client.get(api_url, params=AdoptiumClient.ASSETS_PARAMS, timeout=timeout)
        response.raise_for_status()

        try:
            payload = response.json()
        except ValueError as error:
            raise RuntimeError(f"Invalid Adoptium metadata response for Java {managed_major}.") from error

        asset, package = AdoptiumClient._select_package(payload, managed_major)
        download_url = AdoptiumClient._required_string(package.get("link"), "download URL", managed_major)
        sha256 = AdoptiumClient._parse_sha256(package.get("checksum"), managed_major)
        filename = AdoptiumClient._package_filename(package.get("name"), download_url, managed_major)
        size = AdoptiumClient._content_length(package.get("size"))
        release_name = AdoptiumClient._release_name(asset.get("release_name"), filename)

        return JavaRelease(major=managed_major, url=download_url, sha256=sha256, size=size, filename=filename, release_name=release_name)

    @staticmethod
    def _select_package(payload: Any, major: int) -> tuple[dict[str, Any], dict[str, Any]]:
        assets = payload if isinstance(payload, list) else [payload]

        for asset in assets:
            if not isinstance(asset, dict):
                continue

            for binary in AdoptiumClient._iter_binaries(asset):
                if not AdoptiumClient._is_windows_x64_jdk(binary):
                    continue

                package = binary.get("package")
                if not isinstance(package, dict):
                    continue

                link = package.get("link")
                if isinstance(link, str) and link.lower().split("?", 1)[0].endswith(".zip"):
                    return asset, package

        raise RuntimeError(f"Adoptium did not return a Windows x64 JDK ZIP package for Java {major}.")

    @staticmethod
    def _iter_binaries(asset: dict[str, Any]) -> list[dict[str, Any]]:
        binaries: list[dict[str, Any]] = []
        binary = asset.get("binary")
        if isinstance(binary, dict):
            binaries.append(binary)

        legacy_binaries = asset.get("binaries")
        if isinstance(legacy_binaries, list):
            binaries.extend(item for item in legacy_binaries if isinstance(item, dict))

        return binaries

    @staticmethod
    def _is_windows_x64_jdk(binary: dict[str, Any]) -> bool:
        expected_values = {
            "architecture": "x64",
            "image_type": "jdk",
            "jvm_impl": "hotspot",
            "os": "windows",
        }

        for key, expected in expected_values.items():
            actual = binary.get(key)
            if actual is not None and str(actual).lower() != expected:
                return False
        return True

    @staticmethod
    def _parse_sha256(content: Any, major: int) -> str:
        if not isinstance(content, str):
            raise RuntimeError(f"Adoptium metadata is missing the SHA-256 checksum for Java {major}.")

        match = re.search(r"\b[0-9a-fA-F]{64}\b", content)
        if match is None:
            raise RuntimeError(f"Invalid Adoptium SHA-256 checksum for Java {major}.")
        return match.group(0).lower()

    @staticmethod
    def _package_filename(raw_name: Any, url: str, major: int) -> str:
        if isinstance(raw_name, str) and raw_name.strip():
            filename = raw_name.strip()
        else:
            filename = unquote(PurePosixPath(urlparse(url).path).name)

        if not filename.lower().endswith(".zip"):
            raise RuntimeError(f"Adoptium did not return a Windows ZIP package for Java {major}.")
        return filename

    @staticmethod
    def _required_string(value: Any, field_name: str, major: int) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"Adoptium metadata is missing the {field_name} for Java {major}.")
        return value.strip()

    @staticmethod
    def _release_name(raw_name: Any, filename: str) -> str:
        if isinstance(raw_name, str) and raw_name.strip():
            return raw_name.strip()
        return filename.removesuffix(".zip")

    @staticmethod
    def _content_length(raw_length: Any) -> int:
        try:
            return max(0, int(raw_length))
        except (TypeError, ValueError):
            return 0
