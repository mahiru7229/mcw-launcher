from pathlib import Path
from threading import Lock
from uuid import uuid4
import json
import shutil

from src.core.java.adoptium_client import AdoptiumClient
from src.core.java.java_archive_downloader import JavaArchiveDownloader
from src.core.java.java_archive_extractor import JavaArchiveExtractor
from src.core.java.java_major_policy import JavaMajorPolicy
from src.core.java.java_manager import JavaManager
from src.core.java.managed_java_repository import ManagedJavaRepository
from src.core.progress.progress_reporter import ProgressReporter
from src.models.java.java_release import JavaRelease
from src.models.progress.progress_stage import ProgressStage


class JavaProvisioner:
    _locks: dict[int, Lock] = {}
    _locks_guard = Lock()

    @classmethod
    def ensure(cls, required_major: int | None, reporter: ProgressReporter | None = None) -> Path:
        managed_major = JavaMajorPolicy.resolve(required_major)
        with cls._get_lock(managed_major):
            installed = cls._find_installed(managed_major)
            if installed is not None:
                return installed

            if reporter is not None:
                reporter.status(stage=ProgressStage.SELECTING_JAVA, message=f"Java {managed_major} is missing. Preparing automatic installation...")

            release = AdoptiumClient.get_latest_windows_x64_jdk(managed_major)
            archive_path = ManagedJavaRepository.archive_path(managed_major)
            JavaArchiveDownloader.download(release, archive_path, reporter)

            if reporter is not None:
                reporter.status(stage=ProgressStage.INSTALLING_JAVA, message=f"Installing Java {managed_major}...")

            executable = cls._install_release(release, archive_path)
            archive_path.unlink(missing_ok=True)
            return executable

    @classmethod
    def _get_lock(cls, major: int) -> Lock:
        with cls._locks_guard:
            return cls._locks.setdefault(major, Lock())

    @staticmethod
    def _find_installed(major: int) -> Path | None:
        managed_executable = ManagedJavaRepository.executable(major)
        if managed_executable.is_file():
            return managed_executable

        exact_matches = [java for java in JavaManager.find_installation() if java.version == major]
        if exact_matches:
            return exact_matches[0].executable
        return None

    @staticmethod
    def _install_release(release: JavaRelease, archive_path: Path) -> Path:
        runtime_root = ManagedJavaRepository.root()
        target_dir = ManagedJavaRepository.runtime_dir(release.major)
        staging_dir = runtime_root / f".java-{release.major}.installing-{uuid4().hex}"

        try:
            extracted_java_home = JavaArchiveExtractor.extract(archive_path, staging_dir)
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.move(str(extracted_java_home), str(target_dir))
            JavaProvisioner._write_marker(target_dir, release)
        finally:
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)

        executable = target_dir / "bin" / "javaw.exe"
        if not executable.is_file():
            shutil.rmtree(target_dir, ignore_errors=True)
            raise RuntimeError(f"Java {release.major} installation finished without javaw.exe.")
        return executable

    @staticmethod
    def _write_marker(target_dir: Path, release: JavaRelease) -> None:
        marker = {"major": release.major, "release_name": release.release_name, "sha256": release.sha256, "source": "Eclipse Temurin / Adoptium"}
        (target_dir / ".mcw-runtime.json").write_text(json.dumps(marker, indent=4), encoding="utf-8")
