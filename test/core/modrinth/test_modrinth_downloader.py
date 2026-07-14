from pathlib import Path
import hashlib

import pytest

from src.core.modrinth.modrinth_downloader import ModrinthDownloader


def test_verify_checks_sha1_sha512_and_size(tmp_path: Path):
    path = tmp_path / "file.jar"
    content = b"modrinth-test"
    path.write_bytes(content)

    assert ModrinthDownloader.verify(path, sha1=hashlib.sha1(content).hexdigest(), sha512=hashlib.sha512(content).hexdigest(), expected_size=len(content))
    assert not ModrinthDownloader.verify(path, sha1="0" * 40)


def test_pack_urls_require_https_and_allowed_hosts():
    with pytest.raises(RuntimeError, match="HTTPS"):
        ModrinthDownloader._validate_pack_url("http://cdn.modrinth.com/file.jar")
    with pytest.raises(RuntimeError, match="not allowed"):
        ModrinthDownloader._validate_pack_url("https://example.com/file.jar")

    ModrinthDownloader._validate_pack_url("https://cdn.modrinth.com/data/project/file.jar")
