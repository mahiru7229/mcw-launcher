import hashlib
import json
import os
from pathlib import Path
import zipfile

files_to_pack = [
    "mcw_core/api/update/update_manager.py",
    "src/core/update/update_manager.py",
]


def make_config(version_id: str) -> str:
    return f'''from __future__ import annotations

VERSION = "v{version_id}"
VERSION_ID = "{version_id}"
VERSION_TAG = f"v{{VERSION_ID}}"
UPDATE_CHANNEL = "stable"
GITHUB_REPOSITORY = "mahiru7229/mcw-launcher"
DEFAULT_CLOUDFLARE_RELEASES_URL = "https://mcw-download.pages.dev/releases/manifest.json"
DEFAULT_UPDATE_SOURCE = "cloudflare"
DEVELOPER_NAME = "mahiru7229"
LAUNCHER_SLUG = "mcw-launcher"
LAUNCHER_NAME = f"MCW LAUNCHER {{VERSION}}"
MODRINTH_USER_AGENT = f"{{DEVELOPER_NAME}}/{{LAUNCHER_SLUG}}/{{VERSION_ID}} (https://github.com/{{GITHUB_REPOSITORY}})"
CURSEFORGE_USER_AGENT = MODRINTH_USER_AGENT
FTB_USER_AGENT = MODRINTH_USER_AGENT
ATLAUNCHER_USER_AGENT = MODRINTH_USER_AGENT

# CurseForge Core API v1 configuration.
CURSEFORGE_OFFICIAL_API_URL = "https://api.curseforge.com"
CURSEFORGE_DEFAULT_GATEWAY_URL = ""
CURSEFORGE_BUNDLED_API_KEY = ""
CURSEFORGE_CACHE_MAX_BYTES = 10 * 1024 * 1024
CURSEFORGE_MANUAL_REFRESH_COOLDOWN_SECONDS = 60

# Microsoft authentication is available in public builds.
MICROSOFT_AUTH_ENABLED = True
MICROSOFT_AUTH_STATUS = "available"
MICROSOFT_CLIENT_ID = "cd379605-ee06-466a-a588-7a1f7c23b48a"

# Security: Minecraft access tokens are short-lived and are kept in memory only.
PERSIST_MICROSOFT_ACCESS_TOKEN = False
'''


def build_hotfix_zip(version_id: str) -> tuple[Path, int, str]:
    dest_zip = Path(f"d:/WORKBASE/mcw-download/public/hotfixes/v{version_id}.zip")
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("src/config.py", make_config(version_id))
        for rel_path in files_to_pack:
            p = Path(rel_path)
            zf.writestr(rel_path.replace(os.sep, "/"), p.read_bytes())

    zip_bytes = dest_zip.read_bytes()
    sha256 = hashlib.sha256(zip_bytes).hexdigest()
    size = len(zip_bytes)
    print(f"CREATED: {dest_zip} | SIZE: {size} | SHA256: {sha256}")
    return dest_zip, size, sha256


if __name__ == "__main__":
    _, size_1861, sha_1861 = build_hotfix_zip("1.8.6.1")
    _, size_1871, sha_1871 = build_hotfix_zip("1.8.7.1")

    hf_path = Path("d:/WORKBASE/mcw-download/public/hotfixes/manifest.json")
    if hf_path.is_file():
        hf_data = json.loads(hf_path.read_text(encoding="utf-8"))
        hf_data["updated_at"] = "2026-11-17T02:44:00Z"
        entry_1871 = {
            "base_version": "1.8.7",
            "target_version": "1.8.7.1",
            "hotfix_id": 1871,
            "release_tag": "v1.8.7.1",
            "description": "Hotfix v1.8.7.1: Khắc phục lỗi kiểm tra cập nhật trên kênh Stable không tự động chuyển dự phòng sang GitHub API khi Cloudflare CDN trả về rỗng.",
            "enabled": True,
            "download_url": "https://mcw-download.pages.dev/hotfixes/v1.8.7.1.zip",
            "sha256": sha_1871,
            "size_bytes": size_1871,
            "clean_on_upgrade": True,
            "target_modules": [
                "mcw_core/api/update/update_manager.py",
                "src/config.py",
                "src/core/update/update_manager.py",
            ],
        }
        entry_1861 = {
            "base_version": "1.8.6",
            "target_version": "1.8.6.1",
            "hotfix_id": 1861,
            "release_tag": "v1.8.6.1",
            "description": "Hotfix v1.8.6.1: Khắc phục lỗi kiểm tra cập nhật trên kênh Stable không tự động chuyển dự phòng sang GitHub API khi Cloudflare CDN trả về rỗng.",
            "enabled": True,
            "download_url": "https://mcw-download.pages.dev/hotfixes/v1.8.6.1.zip",
            "sha256": sha_1861,
            "size_bytes": size_1861,
            "clean_on_upgrade": True,
            "target_modules": [
                "mcw_core/api/update/update_manager.py",
                "src/config.py",
                "src/core/update/update_manager.py",
            ],
        }
        others = [x for x in hf_data.get("active_hotfixes", []) if x.get("hotfix_id") not in (1861, 1871)]
        hf_data["active_hotfixes"] = [entry_1871, entry_1861] + others
        hf_path.write_text(json.dumps(hf_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Updated hotfixes/manifest.json with both 1871 and 1861.")
