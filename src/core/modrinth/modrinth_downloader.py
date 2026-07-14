from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import hashlib
import time

import httpx

from src.core.network.httpx_downloader import CHUNK_SIZE, HttpDownloader
from src.models.modrinth.version import ModrinthFile


class ModrinthDownloader:
    ALLOWED_PACK_HOSTS = {"cdn.modrinth.com", "github.com", "raw.githubusercontent.com", "gitlab.com"}

    @staticmethod
    def download_file(file: ModrinthFile, destination: Path, force: bool = False) -> Path:
        return ModrinthDownloader.download_urls(urls=(file.url,), destination=destination, sha1=file.sha1, sha512=file.sha512, expected_size=file.size, force=force, restrict_hosts=False)

    @staticmethod
    def download_urls(urls: tuple[str, ...] | list[str], destination: Path, sha1: str = "", sha512: str = "", expected_size: int = 0, force: bool = False, restrict_hosts: bool = True, max_retry: int = 2) -> Path:
        normalized_urls = tuple(str(url).strip() for url in urls if str(url).strip())
        if not normalized_urls:
            raise RuntimeError(f"No download URL is available for '{destination.name}'.")
        if not sha1 and not sha512:
            raise RuntimeError(f"No checksum is available for '{destination.name}'.")

        if destination.is_file() and not force and ModrinthDownloader.verify(destination, sha1=sha1, sha512=sha512, expected_size=expected_size):
            return destination

        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_name(destination.name + ".part")
        last_error: Exception | None = None

        for url in normalized_urls:
            if restrict_hosts:
                ModrinthDownloader._validate_pack_url(url)
            for attempt in range(1, max_retry + 1):
                try:
                    temp.unlink(missing_ok=True)
                    client = HttpDownloader.get_client()
                    sha1_hash = hashlib.sha1()
                    sha512_hash = hashlib.sha512()
                    size = 0
                    with client.stream("GET", url, timeout=30.0) as response:
                        response.raise_for_status()
                        with temp.open("wb") as output:
                            for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                                if not chunk:
                                    continue
                                output.write(chunk)
                                sha1_hash.update(chunk)
                                sha512_hash.update(chunk)
                                size += len(chunk)

                    ModrinthDownloader._validate_digest(temp.name, size, sha1_hash.hexdigest(), sha512_hash.hexdigest(), sha1, sha512, expected_size)
                    temp.replace(destination)
                    return destination
                except (httpx.HTTPError, OSError, RuntimeError) as error:
                    last_error = error
                    temp.unlink(missing_ok=True)
                    if attempt < max_retry:
                        time.sleep(min(2 ** (attempt - 1), 4))

        raise RuntimeError(f"Failed to download '{destination.name}' from all available sources.") from last_error

    @staticmethod
    def verify(path: Path, sha1: str = "", sha512: str = "", expected_size: int = 0) -> bool:
        if not path.is_file():
            return False
        if expected_size > 0:
            try:
                if path.stat().st_size != expected_size:
                    return False
            except OSError:
                return False
        sha1_hash = hashlib.sha1()
        sha512_hash = hashlib.sha512()
        try:
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    sha1_hash.update(chunk)
                    sha512_hash.update(chunk)
        except OSError:
            return False
        if sha1 and sha1_hash.hexdigest().lower() != sha1.lower():
            return False
        if sha512 and sha512_hash.hexdigest().lower() != sha512.lower():
            return False
        return True

    @staticmethod
    def _validate_digest(name: str, size: int, actual_sha1: str, actual_sha512: str, expected_sha1: str, expected_sha512: str, expected_size: int) -> None:
        if expected_size > 0 and size != expected_size:
            raise RuntimeError(f"Size mismatch for '{name}'.")
        if expected_sha1 and actual_sha1.lower() != expected_sha1.lower():
            raise RuntimeError(f"SHA-1 mismatch for '{name}'.")
        if expected_sha512 and actual_sha512.lower() != expected_sha512.lower():
            raise RuntimeError(f"SHA-512 mismatch for '{name}'.")

    @staticmethod
    def _validate_pack_url(url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme.lower() != "https":
            raise RuntimeError("Modpack files must use HTTPS URLs.")
        if host not in ModrinthDownloader.ALLOWED_PACK_HOSTS:
            raise RuntimeError(f"Modpack download host is not allowed: {host or 'unknown'}")
