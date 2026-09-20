from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")

from src.gui.dialogs.curseforge_manual_download_dialog import CurseForgeManualDownloadDialog


def test_manual_dialog_disables_add_files_while_import_is_running(gui_app):
    dialog = CurseForgeManualDownloadDialog()
    dialog.set_requirements([SimpleNamespace(provider="curseforge", project_id=1, file_id=2, managed_path="mods/example.jar", file_name="example.jar")])

    assert dialog.add_files_button.isEnabled() is True
    dialog.set_import_busy(True)
    assert dialog.add_files_button.isEnabled() is False
    dialog.set_import_busy(False)
    assert dialog.add_files_button.isEnabled() is True


def test_manual_dialog_auto_accepts_when_all_installed(gui_app):
    dialog = CurseForgeManualDownloadDialog()
    req = SimpleNamespace(provider="curseforge", project_id=1, file_id=2, managed_path="mods/example.jar", file_name="example.jar")
    dialog.set_requirements([req])

    accepted = False
    def on_accepted():
        nonlocal accepted
        accepted = True
    dialog.accepted.connect(on_accepted)

    assert dialog.remaining_count == 1
    dialog.mark_installed(req)
    assert dialog.remaining_count == 0
    assert accepted is True


def test_manual_dialog_emits_cancelled_when_closed_with_remaining(gui_app):
    dialog = CurseForgeManualDownloadDialog()
    req = SimpleNamespace(provider="curseforge", project_id=1, file_id=2, managed_path="mods/example.jar", file_name="example.jar")
    dialog.set_requirements([req])

    cancelled_fired = False
    def on_cancelled():
        nonlocal cancelled_fired
        cancelled_fired = True
    dialog.cancelled.connect(on_cancelled)

    dialog.reject()
    assert cancelled_fired is True


def test_manual_dialog_scan_downloads_finds_matching_file(tmp_path, monkeypatch, gui_app):
    dialog = CurseForgeManualDownloadDialog()
    req = SimpleNamespace(provider="curseforge", project_id=1, file_id=2, managed_path="mods/example.jar", file_name="example.jar")
    dialog.set_requirements([req])

    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    downloaded_file = downloads_dir / "example (1).jar"
    downloaded_file.write_bytes(b"mod content")

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    emitted: list[list] = []
    dialog.files_selected.connect(emitted.append)

    dialog._scan_downloads_folder()

    assert len(emitted) == 1
    assert emitted[0] == [downloaded_file]
    assert dialog.last_files_auto_detected is True


def test_manual_dialog_scan_downloads_ignores_older_files(tmp_path, monkeypatch, gui_app):
    import os
    import time
    dialog = CurseForgeManualDownloadDialog()
    req = SimpleNamespace(provider="curseforge", project_id=1, file_id=2, managed_path="mods/example.jar", file_name="example.jar")

    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    old_file = downloads_dir / "example.jar"
    old_file.write_bytes(b"old mod content")
    # Set old timestamp: 1 hour ago
    old_mtime = time.time() - 3600
    os.utime(old_file, (old_mtime, old_mtime))

    dialog.set_requirements([req])
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    emitted: list[list] = []
    dialog.files_selected.connect(emitted.append)

    dialog._scan_downloads_folder()

    assert len(emitted) == 0


def test_manual_dialog_emits_auto_files_selected_signal(tmp_path, monkeypatch, gui_app):
    dialog = CurseForgeManualDownloadDialog()
    req = SimpleNamespace(provider="curseforge", project_id=1, file_id=2, managed_path="mods/example.jar", file_name="example.jar")
    dialog.set_requirements([req])

    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    downloaded_file = downloads_dir / "example.jar"
    downloaded_file.write_bytes(b"mod content")

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    auto_emitted: list[list] = []
    dialog.auto_files_selected.connect(auto_emitted.append)

    dialog._scan_downloads_folder()

    assert len(auto_emitted) == 1
    assert auto_emitted[0] == [downloaded_file]
    assert dialog.last_files_auto_detected is True


def test_manual_dialog_does_not_match_unrelated_jar(tmp_path, monkeypatch, gui_app):
    dialog = CurseForgeManualDownloadDialog()
    req = SimpleNamespace(provider="curseforge", project_id=1, file_id=2, managed_path="mods/example.jar", file_name="example.jar")
    dialog.set_requirements([req])

    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    unrelated_file = downloads_dir / "completely_unrelated.jar"
    unrelated_file.write_bytes(b"unrelated")

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    emitted: list[list] = []
    dialog.files_selected.connect(emitted.append)

    dialog._scan_downloads_folder()

    assert len(emitted) == 0


