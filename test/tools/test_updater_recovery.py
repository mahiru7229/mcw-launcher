from pathlib import Path
import sys

from updater import _clear_stale_locks, _restore_backup


def test_restore_backup_restores_files(tmp_path: Path) -> None:
    launcher_dir = tmp_path / "launcher"
    launcher_dir.mkdir()
    (launcher_dir / "MCW Launcher.exe").write_text("broken executable", encoding="utf-8")

    backup_dir = launcher_dir / "updater" / "backup"
    backup_dir.mkdir(parents=True)
    (backup_dir / "MCW Launcher.exe").write_text("working executable", encoding="utf-8")
    (backup_dir / "data.txt").write_text("data", encoding="utf-8")

    success, message = _restore_backup(launcher_dir)
    assert success
    assert "Đã khôi phục thành công" in message
    assert (launcher_dir / "MCW Launcher.exe").read_text(encoding="utf-8") == "working executable"
    assert (launcher_dir / "data.txt").read_text(encoding="utf-8") == "data"


def test_restore_backup_missing_or_empty(tmp_path: Path) -> None:
    launcher_dir = tmp_path / "launcher"
    launcher_dir.mkdir()

    success, message = _restore_backup(launcher_dir)
    assert not success
    assert "Không tìm thấy thư mục sao lưu" in message

    (launcher_dir / "updater" / "backup").mkdir(parents=True)
    success, message = _restore_backup(launcher_dir)
    assert not success
    assert "Thư mục sao lưu trống" in message


def test_clear_stale_locks(tmp_path: Path) -> None:
    launcher_dir = tmp_path / "launcher"
    launcher_dir.mkdir()

    (launcher_dir / "test.part").write_text("part", encoding="utf-8")
    (launcher_dir / ".run_lock").write_text("lock", encoding="utf-8")
    (launcher_dir / "normal.txt").write_text("normal", encoding="utf-8")

    cleared = _clear_stale_locks(launcher_dir)
    assert cleared == 2
    assert not (launcher_dir / "test.part").exists()
    assert not (launcher_dir / ".run_lock").exists()
    assert (launcher_dir / "normal.txt").exists()
