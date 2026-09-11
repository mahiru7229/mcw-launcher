from __future__ import annotations

from pathlib import Path

from tools.clean_workspace import clean_workspace, format_size


def test_format_size():
    assert format_size(500) == "500 B"
    assert format_size(2048) == "2.0 KB"
    assert format_size(1024 * 1024 * 5) == "5.0 MB"
    assert format_size(1024 * 1024 * 1024 * 2) == "2.00 GB"


def test_clean_workspace_dry_run_leaves_files_intact(tmp_path: Path):
    # Setup test workspace structure
    (tmp_path / "instances" / "test_instance").mkdir(parents=True)
    (tmp_path / "instances" / "test_instance" / "instance.json").write_text("{}", encoding="utf-8")
    (tmp_path / "logs").mkdir(parents=True)
    (tmp_path / "logs" / "launcher.log").write_text("log content", encoding="utf-8")
    (tmp_path / "src" / "pkg" / "__pycache__").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__pycache__" / "mod.cpython-314.pyc").write_bytes(b"\x00" * 20)
    (tmp_path / "src" / "pkg" / "mod.py").write_text("print(1)", encoding="utf-8")

    files, dirs, size = clean_workspace(tmp_path, dry_run=True, quiet=True)

    assert files >= 3
    assert dirs >= 3
    assert size > 0

    # Verify nothing was deleted
    assert (tmp_path / "instances" / "test_instance" / "instance.json").exists()
    assert (tmp_path / "logs" / "launcher.log").exists()
    assert (tmp_path / "src" / "pkg" / "__pycache__").exists()
    assert (tmp_path / "src" / "pkg" / "mod.py").exists()


def test_clean_workspace_deletes_runtime_and_caches_safely(tmp_path: Path):
    # Setup runtime dirs
    (tmp_path / "instances" / "test_instance").mkdir(parents=True)
    (tmp_path / "instances" / "test_instance" / "instance.json").write_text("{}", encoding="utf-8")
    (tmp_path / "logs").mkdir(parents=True)
    (tmp_path / "logs" / "launcher.log").write_text("log content", encoding="utf-8")
    (tmp_path / "cache").mkdir(parents=True)
    (tmp_path / "cache" / "cached.bin").write_bytes(b"\x01\x02\x03")
    (tmp_path / "accounts").mkdir(parents=True)
    (tmp_path / "accounts" / "accounts.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".mcw" / "launch").mkdir(parents=True)
    (tmp_path / ".mcw" / "launch" / "temp.jar").write_bytes(b"\x00" * 10)

    # Setup config dir with generated file and preserved file
    (tmp_path / "config" / "private").mkdir(parents=True)
    (tmp_path / "config" / "gui_settings.json").write_text("{}", encoding="utf-8")
    (tmp_path / "config" / "private" / "credential.key").write_bytes(b"key")
    (tmp_path / "config" / "curseforge.example.json").write_text("{}", encoding="utf-8")

    # Setup source and bytecode
    (tmp_path / "src" / "pkg" / "__pycache__").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__pycache__" / "mod.cpython-314.pyc").write_bytes(b"\x00" * 20)
    (tmp_path / "src" / "pkg" / "mod.py").write_text("print('hello')", encoding="utf-8")

    # Setup test cache
    (tmp_path / ".pytest_cache" / "v").mkdir(parents=True)
    (tmp_path / ".pytest_cache" / "v" / "cache").write_text("pytest", encoding="utf-8")

    files, dirs, size = clean_workspace(tmp_path, dry_run=False, quiet=True)

    # Verify deletions
    assert not (tmp_path / "instances").exists()
    assert not (tmp_path / "logs").exists()
    assert not (tmp_path / "cache").exists()
    assert not (tmp_path / "accounts").exists()
    assert not (tmp_path / ".mcw").exists()
    assert not (tmp_path / "config" / "gui_settings.json").exists()
    assert not (tmp_path / "config" / "private").exists()
    assert not (tmp_path / "src" / "pkg" / "__pycache__").exists()
    assert not (tmp_path / ".pytest_cache").exists()

    # Verify preserved items
    assert (tmp_path / "config" / "curseforge.example.json").exists()
    assert (tmp_path / "src" / "pkg" / "mod.py").exists()


if __name__ == "__main__":
    import tempfile
    test_format_size()
    with tempfile.TemporaryDirectory() as td:
        test_clean_workspace_dry_run_leaves_files_intact(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_clean_workspace_deletes_runtime_and_caches_safely(Path(td))
    print("test_clean_workspace passed!")
