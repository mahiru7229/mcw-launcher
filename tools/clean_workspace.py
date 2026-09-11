from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Directories generated at runtime when running launcher from source
RUNTIME_DIRS = (
    "instances",
    "logs",
    "cache",
    "accounts",
    "runtimes",
    "backups",
    ".mcw",
)

# Config directory generated files to clean (preserving tracked/example files)
CONFIG_DIR = "config"
CONFIG_PRESERVE_FILENAMES = {"curseforge.example.json"}

# Python bytecode & cache directories
BYTECODE_DIR_NAMES = ("__pycache__",)
BYTECODE_FILE_EXTENSIONS = (".pyc", ".pyo", ".pyd")

# Testing and linting artifacts
TEST_CACHE_DIRS = (".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov")
TEST_CACHE_FILES = (".coverage", "coverage.xml")

# Build and distribution artifacts
BUILD_DIRS = ("build", "dist", "release")
BUILD_DIR_PATTERNS = ("*.egg-info",)

# Directories that must NEVER be deleted
PROTECTED_DIRS = {
    ".git",
    "src",
    "mcw_core",
    "test",
    "tools",
    "lang",
    "themes",
    "docs",
}


def format_size(bytes_count: int) -> str:
    """Format bytes into a human-readable string."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    if bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    if bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.1f} MB"
    return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


def _handle_readonly(func, path, _exc_info):
    """Clear readonly file attribute on Windows and retry removal."""
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        func(path)
    except Exception:
        pass


def get_git_tracked_files(root: Path) -> set[Path]:
    """Return the set of all git-tracked files in the workspace."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return {root / line.strip() for line in result.stdout.splitlines() if line.strip()}
    except Exception:
        pass
    return set()


def get_short_workspace_root() -> Path:
    """Return the platform-specific temporary short workspace folder."""
    if sys.platform == "win32":
        local_app_data = str(os.environ.get("LOCALAPPDATA") or "").strip()
        if local_app_data:
            return Path(local_app_data) / "MCW" / "t"
    return Path(tempfile.gettempdir()) / "MCW" / "t"


def clean_workspace(
    root: Path = PROJECT_ROOT,
    *,
    clean_runtime: bool = True,
    clean_bytecode: bool = True,
    clean_test_cache: bool = True,
    clean_build: bool = False,
    clean_temp_short_workspace: bool = False,
    dry_run: bool = False,
    quiet: bool = False,
) -> tuple[int, int, int]:
    """Clean generated files from the workspace.

    Returns (files_deleted, dirs_deleted, bytes_freed).
    """
    root = root.resolve()
    tracked_files = get_git_tracked_files(root)

    total_files = 0
    total_dirs = 0
    total_bytes = 0

    def log_item(item_type: str, path: Path, file_count: int, size: int) -> None:
        if quiet:
            return
        prefix = "[DRY-RUN] Would remove" if dry_run else "Removed"
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            rel_path = path
        if file_count > 0:
            print(f"  {prefix} {item_type}: {rel_path} ({file_count} files, {format_size(size)})")
        else:
            print(f"  {prefix} {item_type}: {rel_path} ({format_size(size)})")

    # 1. Clean runtime directories
    if clean_runtime:
        for name in RUNTIME_DIRS:
            target_dir = root / name
            if not target_dir.is_dir() or target_dir.name in PROTECTED_DIRS:
                continue
            # Safety: skip if any tracked file lives inside
            if any(target_dir in f.parents or f == target_dir for f in tracked_files):
                continue
            files_in_dir = 0
            bytes_in_dir = 0
            for item in target_dir.rglob("*"):
                if item.is_file():
                    files_in_dir += 1
                    try:
                        bytes_in_dir += item.stat().st_size
                    except OSError:
                        pass
            log_item("runtime dir", target_dir, files_in_dir, bytes_in_dir)
            total_files += files_in_dir
            total_dirs += 1
            total_bytes += bytes_in_dir
            if not dry_run:
                shutil.rmtree(target_dir, onerror=_handle_readonly)

        # Clean runtime config files (excluding tracked / example files)
        config_dir = root / CONFIG_DIR
        if config_dir.is_dir():
            for item in list(config_dir.iterdir()):
                if item.name in CONFIG_PRESERVE_FILENAMES or item in tracked_files:
                    continue
                if item.is_dir():
                    # Safety check
                    if any(item in f.parents or f == item for f in tracked_files):
                        continue
                    dir_files = sum(1 for f in item.rglob("*") if f.is_file())
                    dir_bytes = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    log_item("runtime config dir", item, dir_files, dir_bytes)
                    total_files += dir_files
                    total_dirs += 1
                    total_bytes += dir_bytes
                    if not dry_run:
                        shutil.rmtree(item, onerror=_handle_readonly)
                elif item.is_file():
                    try:
                        size = item.stat().st_size
                    except OSError:
                        size = 0
                    log_item("runtime config file", item, 1, size)
                    total_files += 1
                    total_bytes += size
                    if not dry_run:
                        try:
                            os.chmod(item, stat.S_IWRITE | stat.S_IREAD)
                            item.unlink(missing_ok=True)
                        except OSError:
                            pass

    # 2. Clean build directories
    if clean_build:
        for name in BUILD_DIRS:
            target_dir = root / name
            if not target_dir.is_dir() or target_dir.name in PROTECTED_DIRS:
                continue
            if any(target_dir in f.parents or f == target_dir for f in tracked_files):
                continue
            files_in_dir = sum(1 for f in target_dir.rglob("*") if f.is_file())
            bytes_in_dir = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
            log_item("build dir", target_dir, files_in_dir, bytes_in_dir)
            total_files += files_in_dir
            total_dirs += 1
            total_bytes += bytes_in_dir
            if not dry_run:
                shutil.rmtree(target_dir, onerror=_handle_readonly)

    # 3. Clean python bytecode & test caches by walking directory tree
    for current_root, dirnames, filenames in os.walk(root, topdown=True):
        current_path = Path(current_root)

        # Never enter .git
        dirnames[:] = [d for d in dirnames if d != ".git"]

        # Check directories to delete
        dirs_to_remove = []
        for dname in list(dirnames):
            dpath = current_path / dname
            if dname in PROTECTED_DIRS or dpath in tracked_files:
                continue
            should_remove = False
            label = ""

            if clean_bytecode and dname in BYTECODE_DIR_NAMES:
                should_remove = True
                label = "pycache dir"
            elif clean_test_cache and dname in TEST_CACHE_DIRS:
                should_remove = True
                label = "test cache dir"
            elif clean_build and any(fnmatch.fnmatch(dname, pat) for pat in BUILD_DIR_PATTERNS):
                should_remove = True
                label = "egg-info dir"

            if should_remove:
                # Safety check
                if any(dpath in f.parents or f == dpath for f in tracked_files):
                    continue
                files_count = sum(1 for f in dpath.rglob("*") if f.is_file())
                bytes_count = sum(f.stat().st_size for f in dpath.rglob("*") if f.is_file())
                log_item(label, dpath, files_count, bytes_count)
                total_files += files_count
                total_dirs += 1
                total_bytes += bytes_count
                if not dry_run:
                    shutil.rmtree(dpath, onerror=_handle_readonly)
                dirs_to_remove.append(dname)

        for d in dirs_to_remove:
            dirnames.remove(d)

        # Check standalone files to delete
        for fname in filenames:
            fpath = current_path / fname
            if fpath in tracked_files:
                continue

            should_remove = False
            label = ""
            if clean_bytecode and fpath.suffix.casefold() in BYTECODE_FILE_EXTENSIONS:
                should_remove = True
                label = "bytecode file"
            elif clean_test_cache and fname in TEST_CACHE_FILES:
                should_remove = True
                label = "test cache file"

            if should_remove:
                try:
                    size = fpath.stat().st_size
                except OSError:
                    size = 0
                log_item(label, fpath, 1, size)
                total_files += 1
                total_bytes += size
                if not dry_run:
                    try:
                        os.chmod(fpath, stat.S_IWRITE | stat.S_IREAD)
                        fpath.unlink(missing_ok=True)
                    except OSError:
                        pass

    # 4. Clean temporary short workspace
    if clean_temp_short_workspace:
        short_root = get_short_workspace_root()
        if short_root.is_dir():
            files_count = sum(1 for f in short_root.rglob("*") if f.is_file())
            bytes_count = sum(f.stat().st_size for f in short_root.rglob("*") if f.is_file())
            log_item("temp short workspace", short_root, files_count, bytes_count)
            total_files += files_count
            total_dirs += 1
            total_bytes += bytes_count
            if not dry_run:
                shutil.rmtree(short_root, onerror=_handle_readonly)

    return total_files, total_dirs, total_bytes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clean files and directories generated when running MCW Launcher from source.",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Scan and display files that would be removed without deleting them.",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Clean everything: runtime data, bytecode caches, test caches, build artifacts, and OS temp folders.",
    )
    parser.add_argument(
        "--runtime-only",
        action="store_true",
        help="Only clean runtime directories (instances, logs, cache, accounts, runtimes, backups, config).",
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Only clean Python bytecode (__pycache__, *.pyc) and test caches.",
    )
    parser.add_argument(
        "--include-build",
        action="store_true",
        help="Include build and packaging directories (build, dist, release).",
    )
    parser.add_argument(
        "--include-temp",
        action="store_true",
        help="Include OS short workspace temporary directory (%%LOCALAPPDATA%%/MCW/t).",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress itemized file listing and only show summary.",
    )

    args = parser.parse_args()

    clean_runtime = True
    clean_bytecode = True
    clean_test_cache = True
    clean_build = False
    clean_temp = False

    if args.all:
        clean_runtime = True
        clean_bytecode = True
        clean_test_cache = True
        clean_build = True
        clean_temp = True
    elif args.runtime_only:
        clean_runtime = True
        clean_bytecode = False
        clean_test_cache = False
    elif args.cache_only:
        clean_runtime = False
        clean_bytecode = True
        clean_test_cache = True

    if args.include_build:
        clean_build = True
    if args.include_temp:
        clean_temp = True

    action_label = "Scanning (dry-run)" if args.dry_run else "Cleaning"
    if not args.quiet:
        print(f"=== MCW Launcher Workspace Cleaner ===")
        print(f"Mode: {action_label}")
        print(f"Target: {PROJECT_ROOT}\n")

    files, dirs, size = clean_workspace(
        PROJECT_ROOT,
        clean_runtime=clean_runtime,
        clean_bytecode=clean_bytecode,
        clean_test_cache=clean_test_cache,
        clean_build=clean_build,
        clean_temp_short_workspace=clean_temp,
        dry_run=args.dry_run,
        quiet=args.quiet,
    )

    print("\n--- Summary ---")
    if args.dry_run:
        print(f"Would delete: {files} file(s), {dirs} directory(ies)")
        print(f"Estimated space to reclaim: {format_size(size)}")
        print("No files were removed.")
    else:
        print(f"Deleted: {files} file(s), {dirs} directory(ies)")
        print(f"Reclaimed space: {format_size(size)}")
        print("Workspace is clean!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
