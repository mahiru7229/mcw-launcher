from src.core.java.java_manager import JavaManager
from src.core.java.java_runtime import JavaRuntime
from src.core.minecraft.version_manifest_manager import VersionManifestManager
import requests
import json







# req = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json", timeout=10)
# print(json.loads(req.text)["versions"][0].keys())
print(VersionManifestManager.get()[0])