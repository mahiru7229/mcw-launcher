from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.network.download_journal import DownloadJournal
from src.core.network.download_manager import DownloadManager
from src.core.network.download_models import DownloadRequest, DownloadState
from src.core.network.network_session import NetworkSession
from src.core.repair.verification_cache import VerificationCache


def test_network_session_client_has_no_identity_accept_encoding() -> None:
    session = NetworkSession()
    client = session.get_client()
    try:
        assert client.headers.get("Accept-Encoding") != "identity"
    finally:
        session.close()


def test_download_journal_complete_fast_path_avoids_disk_reads(tmp_path: Path) -> None:
    journal_file = tmp_path / "journal.json"
    journal = DownloadJournal(journal_file)

    request = DownloadRequest(
        urls=("https://example.com/asset.ogg",),
        destination=tmp_path / "asset.ogg",
        display_name="asset.ogg",
    )

    # When file does not exist on disk, complete should not create or read it
    with patch.object(journal, "_read", wraps=journal._read) as mock_read:
        journal.complete(request, 1024)
        mock_read.assert_not_called()
        assert not journal_file.exists()


def test_download_manager_hash_limit_is_widened() -> None:
    dm = DownloadManager()
    assert dm._hash_limit >= 2
    assert dm._hash_limit <= 8


def test_verification_cache_record_verified_and_subsequent_hit(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    cache = VerificationCache(cache_file)

    sample_file = tmp_path / "test.jar"
    sample_content = b"minecraft test content"
    sample_file.write_bytes(sample_content)

    import hashlib
    expected_sha1 = hashlib.sha1(sample_content).hexdigest()

    # Record verified
    success = cache.record_verified("lib:test.jar", sample_file, expected_sha1, "sha1")
    assert success is True

    # Subsequent verify with force_hash=False or True should be a cache hit and NOT re-hash
    res = cache.verify("lib:test.jar", sample_file, expected_size=len(sample_content), expected_hash=expected_sha1, algorithm="sha1", force_hash=True)
    assert res.valid is True
    assert res.cache_hit is True
    assert res.hashed is False
