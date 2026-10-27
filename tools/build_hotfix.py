import hashlib
import os
from pathlib import Path
import zipfile

dest_zip = Path("d:/WORKBASE/mcw-download/public/hotfixes/v1.8.5.1.zip")

files_to_pack = [
    "mcw_core/api/config/curseforge_config_manager.py",
    "mcw_core/api/curseforge/curseforge_client.py",
    "mcw_core/api/security/bundled_secrets.py",
    "mcw_core/api/security/sensitive_data_redactor.py",
    "src/core/config/curseforge_config_manager.py",
    "src/core/curseforge/curseforge_client.py",
    "src/core/security/bundled_secrets.py",
    "src/core/security/sensitive_data_redactor.py",
]

config_content = '''from __future__ import annotations

VERSION = "v1.8.5.1"
VERSION_ID = "1.8.5.1"
VERSION_TAG = f"v{VERSION_ID}"
UPDATE_CHANNEL = "stable"
GITHUB_REPOSITORY = "mahiru7229/mcw-launcher"
DEFAULT_CLOUDFLARE_RELEASES_URL = "https://mcw-download.pages.dev/releases/manifest.json"
DEFAULT_UPDATE_SOURCE = "cloudflare"
DEVELOPER_NAME = "mahiru7229"
LAUNCHER_SLUG = "mcw-launcher"
LAUNCHER_NAME = f"MCW LAUNCHER {VERSION}"
MODRINTH_USER_AGENT = f"{DEVELOPER_NAME}/{LAUNCHER_SLUG}/{VERSION_ID} (https://github.com/{GITHUB_REPOSITORY})"
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

dest_zip.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    zf.writestr("src/config.py", config_content)
    for rel_path in files_to_pack:
        p = Path(rel_path)
        zf.writestr(rel_path.replace(os.sep, "/"), p.read_bytes())

zip_bytes = dest_zip.read_bytes()
sha256 = hashlib.sha256(zip_bytes).hexdigest()
size = len(zip_bytes)

print(f"CREATED: {dest_zip}")
print(f"SIZE: {size}")
print(f"SHA256: {sha256}")
print(f"FILE COUNT: {len(files_to_pack) + 1}")
