from pathlib import Path
from threading import Lock
from typing import Protocol

import hashlib
import httpx
import time

from src.core.progress.progress_reporter import ProgressReporter
from src.models.progress.progress_stage import ProgressStage


CHUNK_SIZE = 64 * 1024


class DownloadInfo(Protocol):
    url: str
    sha1: str
    size: int


class HttpDownloader:
    _client: httpx.Client | None = None
    _client_lock = Lock()

    _path_locks: dict[Path, Lock] = {}
    _path_locks_guard = Lock()

    @classmethod
    def get_client(cls) -> httpx.Client:
        with cls._client_lock:
            if cls._client is None or cls._client.is_closed:
                cls._client = httpx.Client(
                    follow_redirects=True,
                )

            return cls._client

    @classmethod
    def close_client(cls) -> None:
        with cls._client_lock:
            if cls._client is not None and not cls._client.is_closed:
                cls._client.close()

            cls._client = None

    @classmethod
    def _get_path_lock(cls, path: Path) -> Lock:
        try:
            normalized_path = path.resolve(
                strict=False,
            )
        except OSError:
            normalized_path = path.absolute()

        with cls._path_locks_guard:
            return cls._path_locks.setdefault(
                normalized_path,
                Lock(),
            )

    @staticmethod
    def download(
        download_info: DownloadInfo,
        path: Path,
        max_retry: int = 2,
        timeout: float = 20.0,
        reporter: ProgressReporter | None = None,
        progress_stage: ProgressStage | None = None,
        progress_message: str | None = None,
    ) -> Path:
        path_lock = HttpDownloader._get_path_lock(path)

        with path_lock:
            return HttpDownloader._download_and_verify(
                download_info=download_info,
                path=path,
                max_retry=max_retry,
                timeout=timeout,
                reporter=reporter,
                progress_stage=progress_stage,
                progress_message=progress_message,
            )

    @staticmethod
    def _download_stream(
        download_info: DownloadInfo,
        path: Path,
        timeout: float,
        reporter: ProgressReporter | None = None,
        progress_stage: ProgressStage | None = None,
        progress_message: str | None = None,
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        client = HttpDownloader.get_client()

        with client.stream(
            "GET",
            download_info.url,
            timeout=timeout,
        ) as response:
            response.raise_for_status()

            downloaded_bytes = 0

            content_length = response.headers.get(
                "Content-Length"
            )

            if content_length is not None:
                try:
                    total_bytes = int(content_length)
                except ValueError:
                    total_bytes = download_info.size
            else:
                total_bytes = download_info.size

            last_reported_percentage = -1

            HttpDownloader._report_progress(
                reporter=reporter,
                stage=progress_stage,
                message=progress_message,
                current=0,
                total=total_bytes,
            )

            with path.open("wb") as file:
                for chunk in response.iter_bytes(
                    chunk_size=CHUNK_SIZE,
                ):
                    if not chunk:
                        continue

                    file.write(chunk)
                    downloaded_bytes += len(chunk)

                    if total_bytes <= 0:
                        continue

                    current_percentage = min(
                        int(
                            downloaded_bytes
                            * 100
                            / total_bytes
                        ),
                        100,
                    )

                    if (
                        current_percentage
                        == last_reported_percentage
                    ):
                        continue

                    last_reported_percentage = (
                        current_percentage
                    )

                    HttpDownloader._report_progress(
                        reporter=reporter,
                        stage=progress_stage,
                        message=progress_message,
                        current=downloaded_bytes,
                        total=total_bytes,
                    )

            if (
                total_bytes > 0
                and downloaded_bytes >= total_bytes
                and last_reported_percentage < 100
            ):
                HttpDownloader._report_progress(
                    reporter=reporter,
                    stage=progress_stage,
                    message=progress_message,
                    current=total_bytes,
                    total=total_bytes,
                )

    @staticmethod
    def _report_progress(
        reporter: ProgressReporter | None,
        stage: ProgressStage | None,
        message: str | None,
        current: int,
        total: int,
    ) -> None:
        if reporter is None:
            return

        if stage is None:
            return

        reporter.bytes(
            stage=stage,
            message=message or "Downloading file...",
            current=current,
            total=total,
        )

    @staticmethod
    def verify_sha1(
        path: Path,
        expected_sha1: str,
    ) -> bool:
        if not path.is_file():
            return False

        sha1 = hashlib.sha1()

        try:
            with path.open("rb") as file:
                while chunk := file.read(8192):
                    sha1.update(chunk)

        except OSError:
            return False

        return (
            sha1.hexdigest().lower()
            == expected_sha1.lower()
        )

    @staticmethod
    def delete_file(path: Path) -> None:
        try:
            path.unlink(
                missing_ok=True,
            )
        except OSError:
            pass

    @staticmethod
    def _download_and_verify(
        download_info: DownloadInfo,
        path: Path,
        max_retry: int,
        timeout: float,
        reporter: ProgressReporter | None = None,
        progress_stage: ProgressStage | None = None,
        progress_message: str | None = None,
    ) -> Path:
        if max_retry < 1:
            raise ValueError(
                "max_retry must be at least 1"
            )

        if HttpDownloader.verify_sha1(
            path,
            download_info.sha1,
        ):
            return path

        temp_path = path.with_name(
            f"{path.name}.part"
        )

        last_error: Exception | None = None

        for attempt in range(
            1,
            max_retry + 1,
        ):
            try:
                HttpDownloader.delete_file(
                    temp_path
                )

                HttpDownloader._download_stream(
                    download_info=download_info,
                    path=temp_path,
                    timeout=timeout,
                    reporter=reporter,
                    progress_stage=progress_stage,
                    progress_message=progress_message,
                )

                if not HttpDownloader.verify_sha1(
                    temp_path,
                    download_info.sha1,
                ):
                    raise RuntimeError(
                        f"SHA1 mismatch for: {path.name}"
                    )

                temp_path.replace(path)

                return path

            except (
                httpx.HTTPError,
                OSError,
                RuntimeError,
            ) as error:
                last_error = error

                HttpDownloader.delete_file(
                    temp_path
                )

                if attempt < max_retry:
                    delay = min(
                        2 ** (attempt - 1),
                        8,
                    )

                    time.sleep(delay)

        raise RuntimeError(
            f"Failed to download '{path.name}' "
            f"after {max_retry} attempts"
        ) from last_error
