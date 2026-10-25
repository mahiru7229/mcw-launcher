import hashlib
import os
from pathlib import Path
import zipfile

dest_zip = Path("d:/WORKBASE/mcw-download/public/hotfixes/v1.8.3.3.zip")

files_to_pack = [
    "mcw_core/api/models/update/update_info.py",
    "mcw_core/api/runtime/game_window_activator.py",
    "mcw_core/api/system/platform_info.py",
    "mcw_core/api/update/base_release_client.py",
    "mcw_core/api/update/cloudflare_release_client.py",
    "mcw_core/api/update/update_cleanup.py",
    "src/core/atlauncher/atlauncher_client.py",
    "src/core/config/launcher_settings_manager.py",
    "src/core/ftb/ftb_client.py",
    "src/core/minecraft/asset_manager.py",
    "src/core/minecraft/library_manager.py",
    "src/core/network/download_journal.py",
    "src/core/network/download_manager.py",
    "src/core/network/network_session.py",
    "src/core/progress/file_batch_progress.py",
    "src/core/repair/verification_cache.py",
    "src/core/runtime/game_window_activator.py",
    "src/core/system/platform_info.py",
    "src/core/update/base_release_client.py",
    "src/core/update/cloudflare_release_client.py",
    "src/core/update/github_release_client.py",
    "src/core/update/hotfix_manager.py",
    "src/core/update/update_cleanup.py",
    "src/core/update/update_manager.py",
    "src/gui/application.py",
    "src/gui/controllers/atlauncher_controller.py",
    "src/gui/controllers/base_controller.py",
    "src/gui/controllers/content_pack_controller.py",
    "src/gui/controllers/curseforge_controller.py",
    "src/gui/controllers/ftb_controller.py",
    "src/gui/controllers/gui_settings_controller.py",
    "src/gui/controllers/mod_catalog_controller.py",
    "src/gui/controllers/modrinth_controller.py",
    "src/gui/controllers/update_controller.py",
    "src/gui/dialogs/atlauncher_browser_dialog.py",
    "src/gui/main_window.py",
    "src/gui/pages/base_page.py",
    "src/gui/pages/instance_settings_page.py",
    "src/gui/pages/launcher_settings_page.py",
    "src/gui/pages/logs_page.py",
    "src/gui/presenters/progress_presenter.py",
    "src/gui/style.py",
    "src/gui/widget/compact_progress_widget.py",
    "src/gui/widget/global_task_indicator.py",
    "src/gui/widget/launch_control_widget.py",
    "src/models/update/update_info.py",
]

config_content = '''from __future__ import annotations

VERSION = "v1.8.3.3"
VERSION_ID = "1.8.3.3"
VERSION_TAG = f"v{VERSION_ID}"
UPDATE_CHANNEL = "beta"
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

CURSEFORGE_DEFAULT_GATEWAY_URL = ""
CURSEFORGE_CACHE_MAX_BYTES = 10 * 1024 * 1024
CURSEFORGE_MANUAL_REFRESH_COOLDOWN_SECONDS = 60

MICROSOFT_AUTH_ENABLED = True
MICROSOFT_AUTH_STATUS = "available"
MICROSOFT_CLIENT_ID = "cd379605-ee06-466a-a588-7a1f7c23b48a"

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
