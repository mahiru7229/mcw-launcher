from src.models.minecraft.version import Version
from src.models.minecraft.assets_index import DownloadAssetIndex
from src.core.network.httpx_downloader import HttpDownloader
from pathlib import Path
from src.core.fs.paths import Paths


class AssetIndexManager:

    @staticmethod
    def load(version: Version) -> Path:
        assets_index_data = AssetIndexManager._parse_assets_index(version)
        asset_index_path = Paths.asset_index(version)
        if asset_index_path.exists():
            if HttpDownloader.verify_sha1(asset_index_path,assets_index_data.sha1):
                return asset_index_path
            HttpDownloader.delete_file(asset_index_path)

        download = HttpDownloader.download(assets_index_data, asset_index_path, 2,20.0)
        if download is not None:
            return download
        raise RuntimeError(f"Cannot download {version.assets}.json")
        
               

    @staticmethod
    def _parse_assets_index(version: Version):
        return DownloadAssetIndex(
            url=version.asset_index["url"],
            sha1=version.asset_index["sha1"],
            size=int(version.asset_index["size"]),
            id=version.asset_index["id"]
        )
    
