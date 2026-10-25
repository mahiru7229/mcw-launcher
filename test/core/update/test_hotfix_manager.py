from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import httpx
import pytest

from src.core.update.hotfix_manager import (
    HotfixEntry,
    HotfixError,
    HotfixManager,
    HotfixNetworkError,
    HotfixSecurityError,
    HotfixState,
    HotfixVerificationError,
)
from src.core.update.versioning import LauncherVersion


def _create_zip_bytes(file_entries: dict[str, bytes]) -> tuple[bytes, str]:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, data in file_entries.items():
            zf.writestr(path, data)
    raw_bytes = buffer.getvalue()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    return raw_bytes, sha256


@pytest.fixture(autouse=True)
def clean_hotfix_sys_state():
    sys_path_orig = list(sys.path)
    meta_path_orig = list(sys.meta_path)
    callbacks_orig = list(HotfixManager._on_applied_callbacks)
    HotfixManager._on_applied_callbacks.clear()
    yield
    sys.path[:] = sys_path_orig
    sys.meta_path[:] = meta_path_orig
    HotfixManager._on_applied_callbacks[:] = callbacks_orig
    HotfixManager._remove_meta_path_finder()


def test_hotfix_entry_version_parsing() -> None:
    entry = HotfixEntry(
        base_version="1.7.0",
        target_version="1.7.0.1",
        hotfix_id=1,
        release_tag="v1.7.0.1",
        description="Patch crash",
        enabled=True,
        download_url="https://example.com/hf1.zip",
        sha256="abc",
        size_bytes=100,
    )
    assert entry.base_launcher_version == LauncherVersion(1, 7, 0, revision=0)
    assert entry.target_launcher_version == LauncherVersion(1, 7, 0, revision=1)
    assert entry.target_launcher_version > entry.base_launcher_version


def test_fetch_manifest_valid(tmp_path: Path) -> None:
    manifest_data = {
        "schema_version": 1,
        "service": "mcw-hotfix-network",
        "active_hotfixes": [
            {
                "base_version": "1.7.0",
                "target_version": "1.7.0.1",
                "hotfix_id": 1,
                "release_tag": "v1.7.0.1",
                "description": "Fix bug",
                "enabled": True,
                "download_url": "https://example.com/v1.7.0.1.zip",
                "sha256": "abcdef123456",
                "size_bytes": 1024,
                "clean_on_upgrade": True,
                "target_modules": ["src.core.update"],
            }
        ],
    }

    def transport_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=manifest_data)

    client = httpx.Client(transport=httpx.MockTransport(transport_handler))
    manager = HotfixManager(root_directory=tmp_path, client=client)

    entries = manager.fetch_manifest()
    assert len(entries) == 1
    assert entries[0].target_version == "1.7.0.1"
    assert entries[0].hotfix_id == 1
    assert entries[0].enabled is True


def test_fetch_manifest_invalid_schema(tmp_path: Path) -> None:
    def transport_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"schema_version": 99})

    client = httpx.Client(transport=httpx.MockTransport(transport_handler))
    manager = HotfixManager(root_directory=tmp_path, client=client)

    with pytest.raises(HotfixError, match="Unsupported manifest schema_version"):
        manager.fetch_manifest()


def test_check_for_hotfix_selection(tmp_path: Path) -> None:
    manifest_data = {
        "schema_version": 1,
        "active_hotfixes": [
            {
                "base_version": "1.7.0",
                "target_version": "1.7.0.1",
                "hotfix_id": 1,
                "enabled": True,
                "download_url": "https://example.com/1.zip",
                "sha256": "111",
            },
            {
                "base_version": "1.7.0",
                "target_version": "1.7.0.2",
                "hotfix_id": 2,
                "enabled": True,
                "download_url": "https://example.com/2.zip",
                "sha256": "222",
            },
            {
                "base_version": "1.7.0",
                "target_version": "1.7.0.3",
                "hotfix_id": 3,
                "enabled": False,  # disabled hotfix
                "download_url": "https://example.com/3.zip",
                "sha256": "333",
            },
            {
                "base_version": "1.7.1",
                "target_version": "1.7.1.1",
                "hotfix_id": 1,
                "enabled": True,
                "download_url": "https://example.com/171.zip",
                "sha256": "444",
            },
        ],
    }

    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=manifest_data)))
    manager = HotfixManager(root_directory=tmp_path, client=client)

    # Base 1.7.0 with no hotfix installed -> should choose 1.7.0.2 (id=2, latest enabled)
    best = manager.check_for_hotfix("1.7.0", current_hotfix_id=0)
    assert best is not None
    assert best.target_version == "1.7.0.2"
    assert best.hotfix_id == 2

    # If already on hotfix_id=2 -> no newer enabled hotfix (id=3 is disabled)
    assert manager.check_for_hotfix("1.7.0", current_hotfix_id=2) is None

    # Base 1.7.1 -> should choose 1.7.1.1
    best_171 = manager.check_for_hotfix("1.7.1", current_hotfix_id=0)
    assert best_171 is not None
    assert best_171.target_version == "1.7.1.1"


def test_apply_hotfix_success_and_sys_path_injection(tmp_path: Path) -> None:
    patch_code = b"PATCHED_CONSTANT = 'HOTFIX_APPLIED_1_7_0_1'\n"
    zip_bytes, sha256 = _create_zip_bytes({"test_patch_mod.py": patch_code})

    entry = HotfixEntry(
        base_version="1.7.0",
        target_version="1.7.0.1",
        hotfix_id=1,
        release_tag="v1.7.0.1",
        description="Fix test issue",
        enabled=True,
        download_url="https://example.com/patch.zip",
        sha256=sha256,
        size_bytes=len(zip_bytes),
        target_modules=["test_patch_mod"],
    )

    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=zip_bytes)))
    manager = HotfixManager(root_directory=tmp_path, client=client)

    try:
        state = manager.apply_hotfix(entry)
        assert state.target_version == "1.7.0.1"
        assert state.applied_hotfix_id == 1

        # Verify extracted file exists in live/
        live_patch_file = manager.live_dir / "test_patch_mod.py"
        assert live_patch_file.is_file()
        assert live_patch_file.read_bytes() == patch_code

        # Effective version
        assert manager.get_effective_version("1.7.0") == "1.7.0.1"
        assert manager.get_effective_version("1.7.1") == "1.7.1"

        # Test bootstrap sys.path injection
        injected = HotfixManager.bootstrap_sys_path(root_directory=tmp_path, current_base_version="1.7.0")
        assert injected is True
        assert str(manager.live_dir.resolve()) == sys.path[0]
    finally:
        manager.rollback()



def test_apply_hotfix_checksum_failure(tmp_path: Path) -> None:
    zip_bytes, _ = _create_zip_bytes({"file.py": b"content"})
    wrong_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"

    entry = HotfixEntry(
        base_version="1.7.0",
        target_version="1.7.0.1",
        hotfix_id=1,
        release_tag="v1.7.0.1",
        description="Test wrong hash",
        enabled=True,
        download_url="https://example.com/patch.zip",
        sha256=wrong_sha256,
        size_bytes=len(zip_bytes),
    )

    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=zip_bytes)))
    manager = HotfixManager(root_directory=tmp_path, client=client)

    with pytest.raises(HotfixVerificationError, match="Checksum mismatch"):
        manager.apply_hotfix(entry)

    # Live dir and state must not be created
    assert not manager.live_dir.exists()
    assert not manager.state_file.exists()


def test_apply_hotfix_zip_slip_rejection(tmp_path: Path) -> None:
    # Build a malicious zip with traversal path
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("../../escape.txt", b"malicious content")
    zip_bytes = buffer.getvalue()
    sha256 = hashlib.sha256(zip_bytes).hexdigest()

    entry = HotfixEntry(
        base_version="1.7.0",
        target_version="1.7.0.1",
        hotfix_id=1,
        release_tag="v1.7.0.1",
        description="Malicious traversal",
        enabled=True,
        download_url="https://example.com/evil.zip",
        sha256=sha256,
        size_bytes=len(zip_bytes),
    )

    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=zip_bytes)))
    manager = HotfixManager(root_directory=tmp_path, client=client)

    with pytest.raises(HotfixSecurityError, match="Zip Slip"):
        manager.apply_hotfix(entry)

    assert not manager.live_dir.exists()


def test_cleanup_on_base_version_upgrade(tmp_path: Path) -> None:
    zip_bytes, sha256 = _create_zip_bytes({"patch.py": b"print(1)"})
    entry = HotfixEntry(
        base_version="1.7.0",
        target_version="1.7.0.1",
        hotfix_id=1,
        release_tag="v1.7.0.1",
        description="Patch 1.7.0.1",
        enabled=True,
        download_url="https://example.com/p.zip",
        sha256=sha256,
        size_bytes=len(zip_bytes),
        clean_on_upgrade=True,
    )

    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=zip_bytes)))
    manager = HotfixManager(root_directory=tmp_path, client=client)
    manager.apply_hotfix(entry)

    assert manager.live_dir.is_dir()
    assert manager.state_file.is_file()

    # If launcher starts with current base 1.7.1 -> base version changed, cleanup must trigger!
    cleaned = HotfixManager.bootstrap_sys_path(root_directory=tmp_path, current_base_version="1.7.1")
    assert cleaned is False
    assert not manager.live_dir.exists()
    assert not manager.state_file.exists()


def test_rollback(tmp_path: Path) -> None:
    zip_bytes, sha256 = _create_zip_bytes({"mod.py": b"x=1"})
    entry = HotfixEntry(
        base_version="1.7.0",
        target_version="1.7.0.1",
        hotfix_id=1,
        release_tag="v1.7.0.1",
        description="Patch",
        enabled=True,
        download_url="https://example.com/p.zip",
        sha256=sha256,
        size_bytes=len(zip_bytes),
    )

    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=zip_bytes)))
    manager = HotfixManager(root_directory=tmp_path, client=client)
    manager.apply_hotfix(entry)

    assert manager.live_dir.is_dir()
    assert manager.state_file.is_file()

    assert manager.rollback() is True
    assert not manager.live_dir.exists()
    assert not manager.state_file.exists()
    assert manager.get_effective_version("1.7.0") == "1.7.0"


def test_prerelease_base_version_matching(tmp_path: Path) -> None:
    manifest_data = {
        "schema_version": 1,
        "active_hotfixes": [
            {
                "base_version": "1.7.0",
                "target_version": "1.7.0.1",
                "hotfix_id": 1,
                "enabled": True,
                "download_url": "https://example.com/1.zip",
                "sha256": "111",
            },
        ],
    }

    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=manifest_data)))
    manager = HotfixManager(root_directory=tmp_path, client=client)

    # A launcher running 1.7.0-alpha.1 should match base 1.7.0
    best = manager.check_for_hotfix("1.7.0-alpha.1", current_hotfix_id=0)
    assert best is not None
    assert best.target_version == "1.7.0.1"


def test_meta_path_finder_submodule_interception(tmp_path: Path) -> None:
    patch_code = b"FLAG_VALUE = 'patched_from_hotfix'\n"
    zip_bytes, sha256 = _create_zip_bytes({"testpkg/subpkg/worker.py": patch_code})

    entry = HotfixEntry(
        base_version="1.7.0",
        target_version="1.7.0.1",
        hotfix_id=1,
        release_tag="v1.7.0.1",
        description="Patch worker",
        enabled=True,
        download_url="https://example.com/p.zip",
        sha256=sha256,
        size_bytes=len(zip_bytes),
    )

    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=zip_bytes)))
    manager = HotfixManager(root_directory=tmp_path, client=client)
    manager.apply_hotfix(entry)

    # Clean any leftover sys.modules
    for mod in list(sys.modules.keys()):
        if mod.startswith("testpkg"):
            del sys.modules[mod]

    HotfixManager.bootstrap_sys_path(root_directory=tmp_path, current_base_version="1.7.0")

    import testpkg.subpkg.worker as worker
    assert getattr(worker, "FLAG_VALUE") == "patched_from_hotfix"
    assert str(manager.live_dir.resolve()) in str(Path(worker.__file__).resolve())

    # Rollback clears finder
    assert manager.rollback() is True
    from src.core.update.hotfix_manager import HotfixMetaPathFinder
    assert not any(isinstance(f, HotfixMetaPathFinder) for f in sys.meta_path)


def test_apply_hotfix_invokes_registered_callback(tmp_path: Path) -> None:
    zip_bytes, sha256 = _create_zip_bytes({"testpkg/mod.py": b"X = 42\n"})
    entry = HotfixEntry(
        base_version="1.8.2",
        target_version="1.8.2.1",
        hotfix_id=1,
        release_tag="v1.8.2.1",
        description="Patch",
        enabled=True,
        download_url="https://example.com/p.zip",
        sha256=sha256,
        size_bytes=len(zip_bytes),
    )

    received: list[HotfixState] = []

    def on_applied(state: HotfixState) -> None:
        received.append(state)

    HotfixManager.register_apply_callback(on_applied)
    try:
        client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=zip_bytes)))
        manager = HotfixManager(root_directory=tmp_path, client=client)
        manager.apply_hotfix(entry)

        assert len(received) == 1
        assert received[0].target_version == "1.8.2.1"
    finally:
        HotfixManager.unregister_apply_callback(on_applied)
        manager.rollback()


def test_bootstrap_sys_path_with_auto_sync_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    called_timeout: list[float] = []

    def mock_sync(self, current_base_version: str, timeout: float = 3.0):
        called_timeout.append(timeout)
        return None

    monkeypatch.setattr(HotfixManager, "sync_active_hotfix", mock_sync)
    HotfixManager.bootstrap_sys_path(
        root_directory=tmp_path,
        current_base_version="1.8.2",
        auto_sync=True,
        sync_timeout=1.5,
    )

    assert called_timeout == [1.5]

def test_hotfix_meta_path_finder_preserves_original_package_path(tmp_path: Path) -> None:
    live_dir = tmp_path / "live"
    orig_dir = tmp_path / "orig"
    live_pkg = live_dir / "mypkg"
    orig_pkg = orig_dir / "mypkg"

    live_pkg.mkdir(parents=True)
    orig_pkg.mkdir(parents=True)
    (live_pkg / "__init__.py").write_text("# live init", encoding="utf-8")
    (orig_pkg / "__init__.py").write_text("# orig init", encoding="utf-8")

    sys.path.insert(0, str(live_dir.resolve()))
    sys.path.append(str(orig_dir.resolve()))

    from src.core.update.hotfix_manager import HotfixMetaPathFinder
    finder = HotfixMetaPathFinder(live_dir)
    sys.meta_path.insert(0, finder)

    spec = finder.find_spec("mypkg", None)
    assert spec is not None
    assert spec.submodule_search_locations is not None
    locations = list(spec.submodule_search_locations)
    assert str(live_pkg) in locations
    assert str(orig_pkg) in locations


def test_evict_cached_hotfix_modules_refreshes_mcw_core_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import types
    live_dir = tmp_path / "live"
    core_dir = live_dir / "src" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "sample_mod.py").write_text("VALUE = 999\n", encoding="utf-8")

    fake_core = types.ModuleType("src.core.sample_mod")
    fake_core.VALUE = 111
    fake_api = types.ModuleType("mcw_core.api.sample_mod")
    fake_api.VALUE = 111

    monkeypatch.setitem(sys.modules, "src.core.sample_mod", fake_core)
    monkeypatch.setitem(sys.modules, "mcw_core.api.sample_mod", fake_api)

    reloaded_names = []

    def mock_import(name, *args, **kwargs):
        reloaded_names.append(name)
        mod = types.ModuleType(name)
        mod.VALUE = 999
        sys.modules[name] = mod
        return mod

    monkeypatch.setattr("importlib.import_module", mock_import)

    HotfixManager._evict_cached_hotfix_modules(live_dir)

    assert "src.core.sample_mod" in reloaded_names
    assert "mcw_core.api.sample_mod" in reloaded_names

def test_evict_cached_hotfix_modules_preserves_update_info_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    live_dir = tmp_path / "live"
    (live_dir / "src" / "models" / "update").mkdir(parents=True)
    (live_dir / "src" / "core" / "update").mkdir(parents=True)
    (live_dir / "src" / "gui" / "controllers").mkdir(parents=True)

    (live_dir / "src" / "models" / "update" / "update_info.py").write_text("# mod\n", encoding="utf-8")
    (live_dir / "src" / "core" / "update" / "base_release_client.py").write_text("# mod\n", encoding="utf-8")
    (live_dir / "src" / "gui" / "controllers" / "update_controller.py").write_text("# mod\n", encoding="utf-8")

    from src.models.update.update_info import UpdateInfo, ReleaseAsset
    from src.core.update.base_release_client import BaseReleaseClient
    from src.gui.controllers.update_controller import UpdateController
    from src.gui.application import _reload_hotfixed_core_modules

    old_update_info = UpdateInfo(
        current_version="1.8.3",
        version="1.8.4-beta.1",
        tag_name="v1.8.4-beta.1",
        title="1.8.4-beta.1",
        release_notes="",
        release_url="",
        published_at="",
        prerelease=True,
        asset=ReleaseAsset(name="update.zip", download_url="https://example.com/update.zip", size=100),
    )

    HotfixManager._evict_cached_hotfix_modules(live_dir)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "MCW Launcher.exe"))
    HotfixManager._evict_cached_hotfix_modules(live_dir)

    import src.models.update.update_info as m_ui
    import src.core.update.base_release_client as m_brc
    import src.gui.controllers.update_controller as m_uc

    assert m_uc.UpdateInfo is m_brc.UpdateInfo
    assert m_uc.UpdateInfo is m_ui.UpdateInfo
    assert UpdateController._is_valid_update_info(old_update_info) is True

def test_application_reload_resilient_to_legacy_hotfix_manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib
    import types
    from src.core.update.base_release_client import _get_update_info_module

    live_dir = tmp_path / "hotfixes" / "live"
    live_dir.mkdir(parents=True)

    for rel_path in [
        "src/gui/application.py",
        "src/core/update/hotfix_manager.py",
        "mcw_core/api/update/hotfix_manager.py",
        "src/models/update/update_info.py",
        "mcw_core/api/models/update/update_info.py",
        "src/core/update/base_release_client.py",
        "src/gui/controllers/update_controller.py",
    ]:
        dest = live_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(Path(rel_path).read_text(encoding="utf-8"), encoding="utf-8")

    old_mod = types.ModuleType("src.core.update.hotfix_manager")

    class OldHotfixManager:
        @classmethod
        def _install_meta_path_finder(cls, d):
            pass

        @classmethod
        def _evict_cached_hotfix_modules(cls, d):
            sys.modules.pop("src.gui.application", None)

    old_mod.HotfixManager = OldHotfixManager
    monkeypatch.setitem(sys.modules, "src.core.update.hotfix_manager", old_mod)
    monkeypatch.setitem(sys.modules, "mcw_core.api.update.hotfix_manager", old_mod)

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "MCW Launcher.exe"))

    sys.modules.pop("src.gui.application", None)
    app_mod = importlib.import_module("src.gui.application")

    assert "src.gui.application" in sys.modules
    assert sys.modules["src.gui.application"] is app_mod
    assert getattr(sys.modules["src.core.update.hotfix_manager"], "HotfixManager", None) is not OldHotfixManager

    import src.gui.controllers.update_controller as uc_mod
    assert uc_mod.UpdateInfo is _get_update_info_module().UpdateInfo

