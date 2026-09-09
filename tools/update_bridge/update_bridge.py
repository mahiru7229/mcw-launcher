from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:  # Core/test helpers can still be imported on minimal Python builds.
    tk = None
    filedialog = messagebox = ttk = None
from typing import Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid
import zipfile


BRIDGE_VERSION = "1.1.0"
REPOSITORY = "mahiru7229/mcw-launcher"
TARGET_TAG = "v1.5.1-beta.3"
TARGET_VERSION = TARGET_TAG.removeprefix("v")
PLATFORM_ID = "windows-x64"
LAUNCHER_EXE = "MCW Launcher.exe"
USER_AGENT = f"MCW-Update-Bridge/{BRIDGE_VERSION} (+https://github.com/{REPOSITORY})"
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_EXTRACTED_BYTES = 4 * 1024 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 20_000
REPLACE_TIMEOUT_SECONDS = 60.0
REPLACE_RETRY_DELAY_SECONDS = 0.5


class BridgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    size: int


@dataclass(frozen=True)
class ReleasePackage:
    archive: ReleaseAsset
    checksum: ReleaseAsset


@dataclass
class InstallTransaction:
    install_directory: Path
    backup_directory: Path
    changed: list[Path]
    created: set[Path]
    backed_up: set[Path]

    @classmethod
    def create(cls, install_directory: Path) -> "InstallTransaction":
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_directory = install_directory / "cache" / "update-bridge" / f"backup-{stamp}"
        backup_directory.mkdir(parents=True, exist_ok=False)
        return cls(install_directory=install_directory, backup_directory=backup_directory, changed=[], created=set(), backed_up=set())

    def backup_before_change(self, relative_path: Path) -> None:
        destination = self.install_directory / relative_path
        if destination in self.backed_up:
            return
        self.backed_up.add(destination)
        if destination.is_file():
            backup = self.backup_directory / relative_path
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)
        elif not destination.exists():
            self.created.add(destination)
        else:
            raise BridgeError(f"Expected a file or missing path, but found another object: {destination}")

    def mark_changed(self, relative_path: Path) -> None:
        destination = self.install_directory / relative_path
        if destination not in self.changed:
            self.changed.append(destination)

    def rollback(self, logger: Callable[[str], None]) -> None:
        logger("Rollback started")
        errors: list[str] = []
        for destination in reversed(self.changed):
            try:
                relative = destination.relative_to(self.install_directory)
                if destination in self.created:
                    destination.unlink(missing_ok=True)
                    continue
                backup = self.backup_directory / relative
                if backup.is_file():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    replace_file_with_retry(backup, destination, timeout_seconds=REPLACE_TIMEOUT_SECONDS)
            except Exception as error:  # best-effort recovery, report all failures
                errors.append(f"{destination}: {error}")
        if errors:
            raise BridgeError("Rollback was incomplete: " + "; ".join(errors))
        logger("Rollback completed")


class BridgeLogger:
    def __init__(self, install_directory: Path, callback: Callable[[str], None] | None = None) -> None:
        self.path = install_directory / "logs" / "update-bridge.log"
        self.callback = callback

    def __call__(self, message: str) -> None:
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            pass
        if self.callback is not None:
            self.callback(message)


def normalize_tag(tag: str) -> str:
    value = str(tag).strip()
    if not value:
        raise BridgeError("The target release tag is empty.")
    return value if value.startswith("v") else f"v{value}"


def parse_checksum(text: str, expected_filename: str) -> str:
    expected = expected_filename.strip()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if match and Path(match.group(2)).name == expected:
            return match.group(1).lower()
        if re.fullmatch(r"[0-9a-fA-F]{64}", line):
            return line.lower()
    raise BridgeError(f"The checksum asset does not contain a SHA-256 value for {expected_filename}.")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def github_json(url: str) -> dict:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise BridgeError(f"GitHub returned HTTP {error.code} while reading the release.") from error
    except (URLError, TimeoutError, UnicodeError, json.JSONDecodeError) as error:
        raise BridgeError(f"Could not read GitHub release metadata: {error}") from error
    if not isinstance(payload, dict):
        raise BridgeError("GitHub returned an invalid release response.")
    return payload


def select_release_package(payload: dict, target_tag: str) -> ReleasePackage:
    expected_version = normalize_tag(target_tag).removeprefix("v")
    expected_archive = f"MCW-Launcher-v{expected_version}-{PLATFORM_ID}.zip"
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise BridgeError("The GitHub release does not contain an asset list.")

    parsed: dict[str, ReleaseAsset] = {}
    for item in assets:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        url = str(item.get("browser_download_url") or "")
        try:
            size = int(item.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        if name and url:
            parsed[name] = ReleaseAsset(name=name, url=url, size=size)

    archive = parsed.get(expected_archive)
    if archive is None:
        candidates = [asset for asset in parsed.values() if asset.name.lower().endswith(f"-{PLATFORM_ID}.zip") and expected_version in asset.name]
        if len(candidates) == 1:
            archive = candidates[0]
    if archive is None:
        raise BridgeError(f"Release {target_tag} does not contain {expected_archive}.")
    if archive.size <= 0 or archive.size > MAX_ARCHIVE_BYTES:
        raise BridgeError(f"The Windows update archive has an invalid size: {archive.size} bytes.")

    checksum = parsed.get(f"{archive.name}.sha256")
    if checksum is None:
        raise BridgeError(f"Release {target_tag} is missing the required checksum asset {archive.name}.sha256.")
    return ReleasePackage(archive=archive, checksum=checksum)


def download_file(asset: ReleaseAsset, destination: Path, progress: Callable[[int, int], None] | None = None) -> None:
    request = Request(asset.url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=60) as response, destination.open("wb") as handle:
            header_size = response.headers.get("Content-Length")
            try:
                total = int(header_size) if header_size else asset.size
            except (TypeError, ValueError):
                total = asset.size
            downloaded = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                downloaded += len(chunk)
                if downloaded > MAX_ARCHIVE_BYTES and destination.suffix.lower() == ".zip":
                    raise BridgeError("The downloaded archive exceeded the safety size limit.")
                handle.write(chunk)
                if progress is not None:
                    progress(downloaded, max(total, 0))
    except HTTPError as error:
        raise BridgeError(f"Download failed with HTTP {error.code}: {asset.name}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise BridgeError(f"Could not download {asset.name}: {error}") from error


def safe_extract_archive(archive_path: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > MAX_ARCHIVE_ENTRIES:
                raise BridgeError("The update ZIP has an invalid number of entries.")
            total = 0
            for info in entries:
                pure = PurePosixPath(info.filename.replace("\\", "/"))
                if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts) or ":" in pure.parts[0]:
                    raise BridgeError(f"Unsafe path in update ZIP: {info.filename}")
                total += max(int(info.file_size), 0)
                if total > MAX_EXTRACTED_BYTES:
                    raise BridgeError("The extracted update would exceed the safety size limit.")
                target = destination.joinpath(*pure.parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
    except zipfile.BadZipFile as error:
        raise BridgeError("The downloaded update is not a valid ZIP archive.") from error

    children = list(destination.iterdir())
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return destination


def validate_package_manifest(content_directory: Path, target_tag: str) -> list[Path]:
    manifest_path = content_directory / "mcw-update.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BridgeError("The update package does not contain a valid mcw-update.json manifest.") from error
    if not isinstance(payload, dict):
        raise BridgeError("mcw-update.json must contain an object.")

    expected_version = normalize_tag(target_tag).removeprefix("v")
    if payload.get("schema_version") != 2:
        raise BridgeError("Unsupported update package manifest schema; bridge 1.1.0 requires schema 2.")
    if str(payload.get("version") or "") != expected_version:
        raise BridgeError(f"Package version does not match {target_tag}.")
    if str(payload.get("platform") or "").casefold() != PLATFORM_ID:
        raise BridgeError("The package is not a Windows x64 MCW Launcher package.")
    if str(payload.get("executable") or "") != LAUNCHER_EXE:
        raise BridgeError("The package executable contract is invalid.")
    if str(payload.get("updater") or "").replace("\\", "/") != "updater/MCW Updater.exe":
        raise BridgeError("The package bundled-updater contract is invalid.")

    raw_files = payload.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise BridgeError("The update package manifest has no managed file list.")

    managed: list[Path] = []
    normalized: set[str] = set()
    for raw in raw_files:
        value = str(raw or "").replace("\\", "/").strip()
        pure = PurePosixPath(value)
        if not value or pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts) or ":" in pure.parts[0]:
            raise BridgeError(f"Unsafe managed path in manifest: {raw}")
        key = pure.as_posix()
        if key in normalized:
            continue
        normalized.add(key)
        path = Path(*pure.parts)
        if not (content_directory / path).is_file():
            raise BridgeError(f"Managed file is missing from the update package: {key}")
        managed.append(path)

    required = {LAUNCHER_EXE, "mcw-update.json", "updater/MCW Updater.exe"}
    if not required.issubset(normalized):
        raise BridgeError("The update manifest does not manage the launcher, bundled updater, and manifest itself.")

    actual = {
        path.relative_to(content_directory).as_posix()
        for path in content_directory.rglob("*")
        if path.is_file()
    }
    extras = actual.difference(normalized)
    if extras:
        raise BridgeError("The update ZIP contains unlisted files: " + ", ".join(sorted(extras)[:10]))
    return sorted(managed, key=lambda path: path.as_posix().casefold())


def replace_file_with_retry(source: Path, destination: Path, timeout_seconds: float = REPLACE_TIMEOUT_SECONDS) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: OSError | None = None
    temporary = destination.with_name(f".{destination.name}.mcw-bridge-{uuid.uuid4().hex}.tmp")
    try:
        shutil.copy2(source, temporary)
        while True:
            try:
                os.replace(temporary, destination)
                return
            except OSError as error:
                last_error = error
                if time.monotonic() >= deadline:
                    break
                time.sleep(REPLACE_RETRY_DELAY_SECONDS)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
    raise BridgeError(f"Could not replace {destination}: {last_error}") from last_error


def validate_install_directory(path: Path) -> Path:
    install = Path(path).expanduser().resolve()
    launcher = install / LAUNCHER_EXE
    if not install.is_dir():
        raise BridgeError(f"Launcher directory does not exist: {install}")
    if not launcher.is_file():
        raise BridgeError(f"{LAUNCHER_EXE} was not found in {install}")
    return install


def install_package(content_directory: Path, install_directory: Path, managed_files: Iterable[Path], logger: Callable[[str], None], target_tag: str = TARGET_TAG) -> Path:
    transaction = InstallTransaction.create(install_directory)
    managed = list(managed_files)
    executable_relative = Path(LAUNCHER_EXE)
    ordered = [executable_relative] + [path for path in managed if path != executable_relative]
    try:
        logger(f"Backup directory: {transaction.backup_directory}")
        logger("Replacing MCW Launcher.exe first")
        for relative in ordered:
            source = content_directory / relative
            destination = install_directory / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            transaction.backup_before_change(relative)
            replace_file_with_retry(source, destination)
            transaction.mark_changed(relative)
            if relative == executable_relative:
                logger("MCW Launcher.exe replaced successfully")
        launcher = install_directory / LAUNCHER_EXE
        if not launcher.is_file() or launcher.stat().st_size != (content_directory / LAUNCHER_EXE).stat().st_size:
            raise BridgeError("The updated launcher executable failed verification.")
        (transaction.backup_directory / "BRIDGE-SUCCESS.txt").write_text(
            f"Bridge {BRIDGE_VERSION} installed {target_tag} at {datetime.now().isoformat()}\n",
            encoding="utf-8",
        )
        logger(f"Update to {target_tag} installed successfully")
        return transaction.backup_directory
    except Exception:
        try:
            transaction.rollback(logger)
        except Exception as rollback_error:
            logger(f"ROLLBACK FAILED: {rollback_error}")
        raise


def release_api_url(repository: str, target_tag: str) -> str:
    return f"https://api.github.com/repos/{repository}/releases/tags/{normalize_tag(target_tag)}"


def bridge_update(
    install_directory: Path,
    repository: str = REPOSITORY,
    target_tag: str = TARGET_TAG,
    status: Callable[[str], None] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    install = validate_install_directory(install_directory)
    logger = BridgeLogger(install, status)
    logger(f"MCW Update Bridge {BRIDGE_VERSION} started")
    logger(f"Target: {target_tag}")
    logger(f"Install directory: {install}")
    payload = github_json(release_api_url(repository, target_tag))
    package = select_release_package(payload, target_tag)
    logger(f"Selected release asset: {package.archive.name}")

    with tempfile.TemporaryDirectory(prefix="mcw-update-bridge-") as temporary:
        temporary_root = Path(temporary)
        archive_path = temporary_root / package.archive.name
        checksum_path = temporary_root / package.checksum.name
        logger("Downloading Windows update package")
        download_file(package.archive, archive_path, progress)
        download_file(package.checksum, checksum_path)
        expected_hash = parse_checksum(checksum_path.read_text(encoding="utf-8", errors="replace"), package.archive.name)
        actual_hash = sha256_file(archive_path)
        if actual_hash != expected_hash:
            raise BridgeError(f"SHA-256 verification failed for {package.archive.name}.")
        logger(f"SHA-256 verified: {actual_hash}")

        extract_root = temporary_root / "extracted"
        content = safe_extract_archive(archive_path, extract_root)
        managed = validate_package_manifest(content, target_tag)
        logger(f"Package manifest verified ({len(managed)} managed files)")
        backup = install_package(content, install, managed, logger, target_tag=target_tag)

    launcher = install / LAUNCHER_EXE
    try:
        subprocess.Popen(
            [str(launcher)],
            cwd=str(install),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        logger("Updated launcher started")
    except OSError as error:
        logger(f"Update installed, but launcher could not be started automatically: {error}")
    return backup


def _candidate_install_directories() -> list[Path]:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent)
    else:
        candidates.append(Path(__file__).resolve().parent)
    candidates.append(Path.cwd())
    seen: set[str] = set()
    result: list[Path] = []
    for candidate in candidates:
        key = os.path.normcase(str(candidate.resolve()))
        if key not in seen:
            seen.add(key)
            result.append(candidate)
    return result


def auto_detect_install_directory() -> Path | None:
    for candidate in _candidate_install_directories():
        if (candidate / LAUNCHER_EXE).is_file():
            return candidate.resolve()
    return None


# Windows-only process helpers. They intentionally target the exact launcher path,
# not every process named MCW Launcher.exe.
TH32CS_SNAPPROCESS = 0x00000002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
PROCESS_SYNCHRONIZE = 0x00100000
WM_CLOSE = 0x0010
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


def _windows_apis():
    if os.name != "nt":
        return None, None
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    return kernel32, user32


def _process_path(pid: int) -> Path | None:
    if os.name != "nt":
        return None
    kernel32, _ = _windows_apis()
    assert kernel32 is not None
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return None
        return Path(buffer.value)
    finally:
        kernel32.CloseHandle(handle)


def launcher_process_ids(launcher_path: Path) -> list[int]:
    if os.name != "nt":
        return []
    target = os.path.normcase(str(launcher_path.resolve()))
    kernel32, _ = _windows_apis()
    assert kernel32 is not None
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        return []
    result: list[int] = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return result
        while True:
            pid = int(entry.th32ProcessID)
            if pid and pid != os.getpid() and str(entry.szExeFile).casefold() == LAUNCHER_EXE.casefold():
                path = _process_path(pid)
                if path is not None and os.path.normcase(str(path.resolve())) == target:
                    result.append(pid)
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
    finally:
        kernel32.CloseHandle(snapshot)
    return result


def request_graceful_close(pids: Iterable[int]) -> None:
    if os.name != "nt":
        return
    wanted = set(int(pid) for pid in pids)
    _, user32 = _windows_apis()
    assert user32 is not None

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd, _lparam):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) in wanted:
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        return True

    user32.EnumWindows(callback, 0)


def force_terminate_processes(pids: Iterable[int]) -> None:
    if os.name != "nt":
        return
    kernel32, _ = _windows_apis()
    assert kernel32 is not None
    for pid in pids:
        handle = kernel32.OpenProcess(PROCESS_TERMINATE | PROCESS_SYNCHRONIZE, False, int(pid))
        if not handle:
            continue
        try:
            kernel32.TerminateProcess(handle, 1)
            kernel32.WaitForSingleObject(handle, 5000)
        finally:
            kernel32.CloseHandle(handle)


class BridgeWindow:
    def __init__(self, root: tk.Tk, initial_directory: Path | None = None) -> None:
        self.root = root
        self.root.title("MCW Launcher Update Bridge")
        self.root.geometry("640x410")
        self.root.minsize(600, 380)
        self.install_var = tk.StringVar(value=str(initial_directory or auto_detect_install_directory() or ""))
        self.status_var = tk.StringVar(value=f"Recovery bridge for MCW Launcher 1.5.0 → {TARGET_TAG}")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.running = False
        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="MCW Launcher Update Bridge", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text=(
                "One-time recovery tool for installations stuck on the 1.5.0 updater. "
                f"It installs {TARGET_TAG} using the release ZIP and SHA-256 checksum."
            ),
            wraplength=590,
        ).pack(anchor="w", pady=(6, 16))

        path_frame = ttk.Frame(outer)
        path_frame.pack(fill="x")
        ttk.Label(path_frame, text="Launcher folder:").pack(anchor="w")
        row = ttk.Frame(path_frame)
        row.pack(fill="x", pady=(4, 0))
        self.path_entry = ttk.Entry(row, textvariable=self.install_var)
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = ttk.Button(row, text="Browse…", command=self._browse)
        self.browse_button.pack(side="left", padx=(8, 0))

        self.progress = ttk.Progressbar(outer, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=(20, 8))
        ttk.Label(outer, textvariable=self.status_var, wraplength=590).pack(anchor="w")

        self.log = tk.Text(outer, height=9, state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, pady=(10, 12))

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x")
        self.start_button = ttk.Button(buttons, text=f"Update to {TARGET_TAG}", command=self._start)
        self.start_button.pack(side="right")
        ttk.Button(buttons, text="Exit", command=self.root.destroy).pack(side="right", padx=(0, 8))

    def _browse(self) -> None:
        selected = filedialog.askdirectory(title="Select the folder containing MCW Launcher.exe")
        if selected:
            self.install_var.set(selected)

    def _append_log(self, message: str) -> None:
        def apply() -> None:
            self.log.configure(state="normal")
            self.log.insert("end", message + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
            self.status_var.set(message)
        self.root.after(0, apply)

    def _set_progress(self, current: int, total: int) -> None:
        percent = 0.0 if total <= 0 else max(0.0, min(100.0, current * 100.0 / total))
        self.root.after(0, lambda: self.progress_var.set(percent))

    def _set_running(self, value: bool) -> None:
        self.running = value
        state = "disabled" if value else "normal"
        self.start_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.path_entry.configure(state=state)

    def _ensure_launcher_closed(self, install: Path) -> bool:
        pids = launcher_process_ids(install / LAUNCHER_EXE)
        if not pids:
            return True
        if not messagebox.askyesno(
            "Close MCW Launcher",
            "MCW Launcher is still running. The bridge must close it before replacing the executable.\n\nClose it now?",
        ):
            return False
        request_graceful_close(pids)
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            remaining = launcher_process_ids(install / LAUNCHER_EXE)
            if not remaining:
                return True
            self.root.update()
            time.sleep(0.2)
        remaining = launcher_process_ids(install / LAUNCHER_EXE)
        if remaining and messagebox.askyesno(
            "Force close required",
            "MCW Launcher did not close normally. Force close only the launcher process from this installation?",
        ):
            force_terminate_processes(remaining)
            time.sleep(0.5)
            return not launcher_process_ids(install / LAUNCHER_EXE)
        return False

    def _start(self) -> None:
        if self.running:
            return
        if os.name != "nt":
            messagebox.showerror("Unsupported platform", "MCW Update Bridge is intended for Windows x64 installations.")
            return
        try:
            install = validate_install_directory(Path(self.install_var.get()))
        except Exception as error:
            messagebox.showerror("Invalid launcher folder", str(error))
            return
        if not self._ensure_launcher_closed(install):
            messagebox.showwarning("Launcher is still running", "Close MCW Launcher and try again.")
            return
        self.progress_var.set(0)
        self._set_running(True)
        self._append_log(f"Starting bridge update for {install}")

        def worker() -> None:
            try:
                backup = bridge_update(install, status=self._append_log, progress=self._set_progress)
            except Exception as error:
                self.root.after(0, lambda: self._finish_error(error))
            else:
                self.root.after(0, lambda: self._finish_success(backup))

        threading.Thread(target=worker, name="mcw-update-bridge", daemon=True).start()

    def _finish_error(self, error: Exception) -> None:
        self._set_running(False)
        self.status_var.set("Update failed")
        messagebox.showerror(
            "MCW Launcher Update Bridge",
            f"The bridge could not finish the update.\n\n{error}\n\nSee logs/update-bridge.log for details.",
        )

    def _finish_success(self, backup: Path) -> None:
        self._set_running(False)
        self.progress_var.set(100)
        self.status_var.set(f"Updated to {TARGET_TAG}")
        messagebox.showinfo(
            "MCW Launcher updated",
            f"MCW Launcher was updated to {TARGET_TAG}.\n\nA recovery backup was kept at:\n{backup}",
        )


def cli_main(args: argparse.Namespace) -> int:
    try:
        install = validate_install_directory(args.install_dir)
        if os.name == "nt":
            pids = launcher_process_ids(install / LAUNCHER_EXE)
            if pids:
                if not args.force_close:
                    raise BridgeError("MCW Launcher is running. Close it first or pass --force-close.")
                request_graceful_close(pids)
                time.sleep(2)
                remaining = launcher_process_ids(install / LAUNCHER_EXE)
                if remaining:
                    force_terminate_processes(remaining)
        bridge_update(install, target_tag=args.tag, status=print)
        return 0
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="One-time recovery updater for MCW Launcher 1.5.0 installations.")
    parser.add_argument("--install-dir", type=Path, help="Folder containing MCW Launcher.exe")
    parser.add_argument("--tag", default=TARGET_TAG, help=f"Target GitHub release tag (default: {TARGET_TAG})")
    parser.add_argument("--force-close", action="store_true", help="Allow the bridge to terminate the matching launcher process if needed")
    parser.add_argument("--cli", action="store_true", help="Run without the graphical interface")
    args = parser.parse_args()

    if args.cli or args.install_dir is not None:
        if args.install_dir is None:
            parser.error("--install-dir is required in CLI mode")
        return cli_main(args)

    if tk is None:
        print("ERROR: Tk is not available. Use --cli --install-dir <path> or run the packaged Windows bridge.", file=sys.stderr)
        return 2
    root = tk.Tk()
    BridgeWindow(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
