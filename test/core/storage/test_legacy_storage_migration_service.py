from pathlib import Path
import json
import os
import time

from src.core.fs.paths import Paths
from src.core.storage.legacy_storage_migration_service import LegacyStorageMigrationService


def _write_instance(root: Path, name: str, version: str, loader=("vanilla", "-1")) -> Path:
    directory = root / "instances" / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "instance.json").write_text(json.dumps({
        "id": name,
        "name": name,
        "version_id": version,
        "mod_loader": list(loader),
    }), encoding="utf-8")
    return directory


def _make_old(path: Path, age_days: int = 30) -> None:
    timestamp = time.time() - age_days * 24 * 60 * 60
    candidates = [path]
    if path.is_dir():
        candidates.extend(path.rglob("*"))
    for candidate in candidates:
        try:
            os.utime(candidate, (timestamp, timestamp))
        except OSError:
            pass


def test_scan_protects_referenced_versions_and_provider_api_cache(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        _write_instance(tmp_path, "Live", "1.20.1", ("forge", "47.2.0"))
        live = Paths.CACHE_ROOT / "versions" / "1.20.1"
        live.mkdir(parents=True)
        (live / "1.20.1.json").write_text('{"id":"1.20.1"}', encoding="utf-8")
        live_loader = Paths.CACHE_ROOT / "versions" / "forge-1.20.1-47.2.0"
        live_loader.mkdir(parents=True)
        (live_loader / "forge.json").write_text('{"id":"forge-1.20.1-47.2.0","inheritsFrom":"1.20.1"}', encoding="utf-8")
        stale = Paths.CACHE_ROOT / "versions" / "1.0"
        stale.mkdir(parents=True)
        (stale / "1.0.jar").write_bytes(b"old-version")
        _make_old(stale)

        api_cache = Paths.CACHE_ROOT / "content" / "curseforge" / "api-v2" / "entries"
        api_cache.mkdir(parents=True)
        (api_cache / "cached-response.json").write_bytes(b"x" * 4096)
        _make_old(api_cache.parent)

        plan = LegacyStorageMigrationService.scan()
        paths = {item.path.resolve() for item in plan.candidates}

        assert stale.resolve() in paths
        assert live.resolve() not in paths
        assert live_loader.resolve() not in paths
        assert all(api_cache.resolve() not in [candidate, *candidate.parents] for candidate in paths)


def test_scan_reports_loader_staging_old_updates_items_and_total_size(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        staging = Paths.CACHE_ROOT / "modloaders" / "forge" / "staging" / "1.18.2-40.2.0"
        staging.mkdir(parents=True)
        (staging / "client.jar").write_bytes(b"a" * 1024)
        _make_old(staging)

        updates = Paths.CACHE_ROOT / "updates" / "downloads"
        for version, size in (("v1.0.0", 2048), ("v1.1.0", 3072), ("v1.2.0", 4096)):
            directory = updates / version
            directory.mkdir(parents=True)
            (directory / "launcher.zip").write_bytes(b"u" * size)

        plan = LegacyStorageMigrationService.scan()
        categories = plan.by_category()

        assert categories["loader_staging"] == 1024
        # v1.2.0 is the newest rollback candidate; older packages are reclaimable.
        assert categories["old_launcher_update"] == 2048 + 3072
        assert plan.total_bytes >= 1024 + 2048 + 3072
        assert plan.file_count >= 3
        assert any(item.reason for item in plan.candidates)


def test_provider_binary_cleanup_only_marks_unreferenced_artifact_versions(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        instance = _write_instance(tmp_path, "Pack", "1.20.1")
        mcw = instance / ".mcw"
        mcw.mkdir()
        (mcw / "curseforge.json").write_text(json.dumps({"mods": {
            "10": {"projectId": 10, "fileId": 20, "fileName": "live.jar"}
        }}), encoding="utf-8")

        live = Paths.CACHE_ROOT / "content" / "curseforge" / "files" / "10" / "20"
        old = Paths.CACHE_ROOT / "content" / "curseforge" / "files" / "10" / "19"
        live.mkdir(parents=True)
        old.mkdir(parents=True)
        (live / "live.jar").write_bytes(b"live")
        (old / "old.jar").write_bytes(b"old")
        _make_old(live)
        _make_old(old)

        plan = LegacyStorageMigrationService.scan()
        provider = [item for item in plan.candidates if item.category == "unreferenced_provider_content"]

        assert [item.path for item in provider] == [old]
        assert "API metadata cache is not included" in provider[0].reason


def test_apply_revalidates_before_deleting_and_skips_newly_referenced_version(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        _write_instance(tmp_path, "Live", "1.20.1")
        old = Paths.CACHE_ROOT / "versions" / "1.0"
        old.mkdir(parents=True)
        (old / "1.0.jar").write_bytes(b"old")
        _make_old(old)
        plan = LegacyStorageMigrationService.scan()
        candidate = next(item for item in plan.candidates if item.path == old)

        _write_instance(tmp_path, "NewlyAdded", "1.0")
        result = LegacyStorageMigrationService.apply(plan, [candidate.candidate_id])

        assert old.exists()
        assert result.reclaimed_bytes == 0
        assert result.skipped == (candidate,)


def test_probe_detects_legacy_staging_without_counting_api_cache(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        staging = Paths.CACHE_ROOT / "modloaders" / "neoforge" / "staging" / "1.21.1-21.1.0"
        staging.mkdir(parents=True)
        (staging / "generated.jar").write_bytes(b"z" * 1500)
        _make_old(staging)
        api = Paths.CACHE_ROOT / "content" / "curseforge" / "api-v2" / "entries"
        api.mkdir(parents=True)
        (api / "huge.json").write_bytes(b"a" * 5000)

        probe = LegacyStorageMigrationService.probe()

        assert probe.has_candidates is True
        assert probe.candidate_count == 1
        assert probe.estimated_bytes == 0


def test_recent_loader_staging_is_protected_from_cleanup(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        staging = Paths.CACHE_ROOT / "modloaders" / "forge" / "staging" / "1.20.1-47.2.0"
        staging.mkdir(parents=True)
        (staging / "active.jar").write_bytes(b"active")

        plan = LegacyStorageMigrationService.scan()

        assert staging not in {item.path for item in plan.candidates}


def test_unreferenced_content_store_blob_is_cleanup_candidate_after_retention(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        blob = Paths.CACHE_ROOT / "content-store" / "sha256" / "aa" / ("a" * 64)
        blob.parent.mkdir(parents=True)
        blob.write_bytes(b"orphan")
        _make_old(blob)

        plan = LegacyStorageMigrationService.scan()

        candidate = next(item for item in plan.candidates if item.path == blob)
        assert candidate.category == "unreferenced_content_store"
        assert candidate.safety == LegacyStorageMigrationService.SAFE


def test_candidate_reclaimable_bytes_do_not_count_storage_still_hardlinked_elsewhere(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        candidate_root = Paths.CACHE_ROOT / "content" / "curseforge" / "files" / "10" / "19"
        candidate_root.mkdir(parents=True)
        artifact = candidate_root / "managed.jar"
        artifact.write_bytes(b"shared-artifact" * 512)
        outside = tmp_path / "outside-managed.jar"
        os.link(artifact, outside)

        candidate = LegacyStorageMigrationService._candidate(
            candidate_root,
            "unreferenced_provider_content",
            "test",
            LegacyStorageMigrationService.REVIEWED,
        )

        assert candidate.size_bytes == artifact.stat().st_size
        assert candidate.effective_reclaimable_bytes == 0


def test_apply_removes_selected_safe_candidate_and_reports_actual_reclaimed_bytes(tmp_path: Path) -> None:
    with Paths.configured(tmp_path):
        staging = Paths.CACHE_ROOT / "modloaders" / "forge" / "staging" / "1.18.2-40.2.0"
        staging.mkdir(parents=True)
        payload = b"legacy-staging" * 256
        (staging / "generated.jar").write_bytes(payload)
        _make_old(staging)

        plan = LegacyStorageMigrationService.scan()
        candidate = next(item for item in plan.candidates if item.path == staging)
        result = LegacyStorageMigrationService.apply(plan, [candidate.candidate_id])

        assert not staging.exists()
        assert result.reclaimed_bytes == len(payload)
        assert result.removed and result.removed[0].candidate_id == candidate.candidate_id
        assert result.skipped == ()
        assert result.failures == ()
