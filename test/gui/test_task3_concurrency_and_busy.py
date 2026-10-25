from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock
import httpx

import pytest

pytest.importorskip("PySide6")

from src.core.atlauncher.atlauncher_client import ATLauncherClient
from src.core.ftb.ftb_client import FTBClient
from src.gui.controllers.content_pack_controller import ContentPackController
from src.gui.controllers.curseforge_controller import CurseForgeController
from src.gui.controllers.mod_catalog_controller import ModCatalogController
from src.gui.controllers.modrinth_controller import ModrinthController
from src.gui.main_window import MainWindow
from src.gui.pages.logs_page import LogsPage
from src.gui.task_runner import TaskRunner


def test_main_window_metadata_lookup_task_filter() -> None:
    assert MainWindow._is_metadata_lookup_task("modrinth.details.mod.fabric.sodium") is True
    assert MainWindow._is_metadata_lookup_task("modrinth.versions.mod.fabric.sodium") is True
    assert MainWindow._is_metadata_lookup_task("curseforge.files.dialog.mod.12345.forge") is True
    assert MainWindow._is_metadata_lookup_task("content.details.modrinth.shaderpack.abc") is True
    assert MainWindow._is_metadata_lookup_task("mod_catalog.versions.fabric.sodium") is True
    # Non-lookup tasks:
    assert MainWindow._is_metadata_lookup_task("modrinth.search.mod.fabric") is False
    assert MainWindow._is_metadata_lookup_task("curseforge.search.mod") is False
    assert MainWindow._is_metadata_lookup_task("content.search.modrinth.resourcepack") is False


def test_logs_page_maximum_block_count(gui_app) -> None:
    page = LogsPage()
    assert page.output.document().maximumBlockCount() == 2000


def test_controllers_pass_expected_task_group(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = TaskRunner()
    captured_groups: dict[str, str | None] = {}

    def fake_run_network_task(controller, task_runner, task_id, task, message="", blocking=False, group=None):
        captured_groups[task_id] = group
        return True

    monkeypatch.setattr(ModrinthController, "_run_network_task", fake_run_network_task)
    monkeypatch.setattr(CurseForgeController, "_run_network_task", fake_run_network_task)
    monkeypatch.setattr(ModCatalogController, "_run_network_task", fake_run_network_task)
    monkeypatch.setattr(ContentPackController, "_run_network_task", fake_run_network_task)

    # Modrinth
    mc = ModrinthController(runner)
    mc.load_versions("mod", "sodium")
    assert any(g == "modrinth.versions.mod" for g in captured_groups.values())

    mc.load_project_details("mod", "sodium")
    assert any(g == "modrinth.details.mod" for g in captured_groups.values())

    # CurseForge
    cc = CurseForgeController(runner)
    cc.load_project_details("mod", 12345)
    assert any(g == "curseforge.details.mod" for g in captured_groups.values())

    cc.load_files("mod", 12345, "1.20.1", "forge", ("release",))
    assert any(g == "curseforge.files.dialog.mod" for g in captured_groups.values())

    # ModCatalog
    mcc = ModCatalogController(runner)
    mcc.load_versions("sodium")
    assert any(g == "mod_catalog.versions" for g in captured_groups.values())

    # ContentPack
    cpc = ContentPackController(runner)
    cpc.load_project_details("modrinth", "shaderpack", "iris")
    assert any(g == "content.details.modrinth.shader" for g in captured_groups.values())

    cpc.load_versions("modrinth", "shaderpack", "iris")
    assert any(g == "content.versions.modrinth.shader" for g in captured_groups.values())


def test_ftb_concurrent_get_project_sends_only_one_request(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core.ftb.ftb_cache import FTBApiCache
    FTBApiCache.clear()
    request_count = 0
    lock = threading.Lock()

    def slow_get(*args, **kwargs):
        nonlocal request_count
        with lock:
            request_count += 1
        time.sleep(0.06)
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.json.return_value = {
            "id": 888888,
            "name": "Test Modpack",
            "synopsis": "Test",
            "description": "Test",
            "authors": [],
            "versions": [{"id": 1, "name": "1.0", "type": "release"}],
        }
        return resp

    mock_client = MagicMock()
    mock_client.get = slow_get
    monkeypatch.setattr("src.core.network.httpx_downloader.HttpDownloader.get_client", lambda: mock_client)

    threads = []
    for _ in range(2):
        t = threading.Thread(target=lambda: FTBClient.get_project(888888, force_refresh=False))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Thanks to the lock and FTBApiCache, only 1 HTTP request was sent
    assert request_count == 1


def test_atlauncher_concurrent_get_project_sends_only_one_request(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core.atlauncher.atlauncher_cache import ATLauncherApiCache
    ATLauncherApiCache.clear()
    request_count = 0
    lock = threading.Lock()

    def slow_get(*args, **kwargs):
        nonlocal request_count
        with lock:
            request_count += 1
        time.sleep(0.06)
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.json.return_value = {
            "data": {
                "id": 100,
                "name": "Test AT Pack",
                "safeName": "test-at-pack-unique",
                "description": "Test",
                "versions": [],
            }
        }
        return resp

    mock_client = MagicMock()
    mock_client.get = slow_get
    monkeypatch.setattr("src.core.network.httpx_downloader.HttpDownloader.get_client", lambda: mock_client)

    threads = []
    for _ in range(2):
        t = threading.Thread(target=lambda: ATLauncherClient.get_project("test-at-pack-unique", force_refresh=False))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Thanks to the lock and ATLauncherApiCache, only 1 HTTP request was sent
    assert request_count == 1
