from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_download_fallback import CurseForgeDownloadFallback
from src.core.network.httpx_downloader import HttpDownloader
from src.core.progress.progress_reporter import ProgressReporter
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.manual_download import CurseForgeManualDownload
from src.models.progress.progress_stage import ProgressStage


class CurseForgeManualDownloadRequired(RuntimeError):
    def __init__(self, requirement: CurseForgeManualDownload) -> None:
        super().__init__(requirement.reason)
        self.requirement = requirement


class CurseForgeDownloader:
    @staticmethod
    def download_file(file: CurseForgeFile, destination: Path, reporter: ProgressReporter | None = None, stage: ProgressStage = ProgressStage.DOWNLOADING_MODS, message: str | None = None, project_name: str = "") -> Path:
        resolved = file
        gateway_error: RuntimeError | None = None
        if not resolved.download_url and resolved.is_available:
            try:
                download_url = CurseForgeClient.get_download_url(resolved.project_id, resolved.file_id, force_refresh=True)
            except RuntimeError as error:
                gateway_error = error
                download_url = ""
            resolved = replace(resolved, download_url=download_url)

        if not resolved.download_url and resolved.sha1:
            fallback = CurseForgeDownloadFallback.find_exact_hash_mirror(
                resolved.sha1,
                expected_name=resolved.file_name,
                expected_size=resolved.file_length,
            )
            if fallback is not None:
                resolved = replace(
                    resolved,
                    download_url=fallback.url,
                    file_name=fallback.file_name or resolved.file_name,
                    file_length=fallback.size or resolved.file_length,
                    is_available=True,
                )

        if not resolved.is_available or not resolved.download_url:
            name = str(project_name).strip() or f"CurseForge project {resolved.project_id}"
            project_url = f"https://www.curseforge.com/minecraft/mc-mods/{resolved.project_id}"
            if gateway_error is not None:
                reason = (
                    f"'{name}' could not be downloaded through the CurseForge gateway ({gateway_error}). "
                    f"No exact SHA-1 mirror was found. Open the project page, download '{resolved.file_name}', and select it in MCW Launcher."
                )
            else:
                reason = (
                    f"'{name}' cannot be downloaded automatically because its author disabled third-party distribution or no public download URL is available. "
                    f"Download '{resolved.file_name}' from CurseForge and select it in MCW Launcher."
                )
            raise CurseForgeManualDownloadRequired(
                CurseForgeManualDownload(
                    project_id=resolved.project_id,
                    file_id=resolved.file_id,
                    project_name=name,
                    file_name=resolved.file_name,
                    file_size=resolved.file_length,
                    sha1=resolved.sha1,
                    project_url=project_url,
                    reason=reason,
                )
            )
        if not resolved.sha1:
            raise RuntimeError(f"CurseForge file '{resolved.file_name}' does not provide a SHA-1 hash.")
        return HttpDownloader.download(
            resolved,
            destination,
            max_retry=5,
            timeout=60.0,
            reporter=reporter,
            progress_stage=stage,
            progress_message=message or f"Downloading {resolved.file_name}...",
        )
