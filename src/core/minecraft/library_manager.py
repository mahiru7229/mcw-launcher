from src.models.minecraft.version import Version
from src.models.minecraft.download import DownloadClient
from src.core.network.httpx_downloader import HttpDownloader
from pathlib import Path
import hashlib
import httpx
import json
PROJECT_ROOT = Path(__file__).resolve().parents[3]
class DownloadLibraryManager:

    @staticmethod
    def load(version: Version) -> Path:
        library_data = DownloadLibraryManager._load_download(version.path)
        library_list = DownloadLibraryManager._load_download_object(library_data)

        libraries_dir = PROJECT_ROOT / "downloads" / "libraries"

        for library in library_list:

            library_path = libraries_dir / library.path

            if (
                library_path.exists()
                and HttpDownloader.verify_sha1(
                    library_path,
                    library.sha1,
                )
            ):
                continue

            HttpDownloader.delete_file(library_path)

            downloaded = HttpDownloader.download(
                library,
                library_path,
            )

            if downloaded is None:
                raise RuntimeError(
                    f"Cannot download library: {library.path}"
                )

        return libraries_dir

    @staticmethod
    def _load_download(path:Path) -> dict:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    
    @staticmethod
    def _load_download_object(download_dict:dict) -> list[DownloadClient]:
        download_content:list[DownloadClient] = []
        for download in download_dict["libraries"]:
            download_content.extend(
                [DownloadClient(
                    url=download["downloads"]["artifact"]["url"],
                    sha1=download["downloads"]["artifact"]["sha1"],
                    size=download["downloads"]["artifact"]["size"],
                    path=Path(download["downloads"]["artifact"]["path"])
                )]
            )


        return download_content
        # return DownloadClient(
        #     url= download_dict["downloads"]["client"]["url"],
        #     sha1=download_dict["downloads"]["client"]["sha1"],
        #     size=int(download_dict["downloads"]["client"]["size"])
        # )






    