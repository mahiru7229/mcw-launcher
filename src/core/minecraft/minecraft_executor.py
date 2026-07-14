from src.core.fs.paths import Paths
from src.core.instance.settings_manager import SettingsManager
from src.core.java.java_major_policy import JavaMajorPolicy
from src.core.java.java_runtime import JavaRuntime
from src.core.java.java_selector import JavaSelector
from src.core.minecraft.asset_manager import AssetManager
from src.core.minecraft.context_builder import ContextBuilder
from src.core.minecraft.download_manager import DownloadClientManager
from src.core.minecraft.launcher_manager import LauncherManager
from src.core.minecraft.library_manager import DownloadLibraryManager
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.core.progress.progress_reporter import ProgressReporter
from src.models.account.account import Account
from src.models.auth.authentication import Authentication
from src.models.instance.instance import Instance
from src.models.progress.progress_callback import ProgressCallback
from src.models.progress.progress_stage import ProgressStage


class MinecraftExecutor:
    @staticmethod
    def run(instance: Instance, authentication: Authentication, account: Account, debug_mode: bool = False, on_progress: ProgressCallback | None = None) -> dict:
        reporter = ProgressReporter(on_progress)
        reporter.status(stage=ProgressStage.PREPARING, message="Preparing Minecraft...")

        VersionManifestManager.get()
        reporter.status(stage=ProgressStage.LOADING_VERSION, message=f"Loading Minecraft {instance.version_id}...")
        version = VersionManager.load(instance.version_id)

        required_java_major = version.java_version.get("majorVersion") or 8
        managed_java_major = JavaMajorPolicy.resolve(required_java_major)
        reporter.status(stage=ProgressStage.SELECTING_JAVA, message=f"Checking Java {managed_java_major}...")
        java = JavaSelector.select_java(required_java_major, reporter=reporter)

        reporter.status(stage=ProgressStage.DOWNLOADING_CLIENT, message="Checking Minecraft client...")
        DownloadClientManager.load(version=version, reporter=reporter)

        reporter.status(stage=ProgressStage.DOWNLOADING_LIBRARIES, message="Checking Minecraft libraries...")
        DownloadLibraryManager.load(version=version, reporter=reporter)

        reporter.status(stage=ProgressStage.DOWNLOADING_ASSETS, message="Checking Minecraft assets...")
        AssetManager.load(version=version, reporter=reporter)

        reporter.status(stage=ProgressStage.BUILDING_CONTEXT, message="Building launch context...")
        settings = SettingsManager.load(instance)
        context = ContextBuilder.build(instance, version, authentication)

        reporter.status(stage=ProgressStage.BUILDING_COMMAND, message="Building launch command...")
        command = LauncherManager.build(version, context, settings, account)

        reporter.status(stage=ProgressStage.LAUNCHING, message=f"Launching Minecraft {version.id}...")
        JavaRuntime.run(java, command, instance)
        reporter.status(stage=ProgressStage.FINISHED, message=f"Minecraft {version.id} launched successfully.")

        if debug_mode:
            native_dir = Paths.natives(version)
            print("Native directory:", native_dir)
            print("Exists:", native_dir.exists())
            if native_dir.exists():
                print("Native files:", list(native_dir.rglob("*")))

        return {"javaPath": java, "minecraftJavaMajorVersion": managed_java_major, "minecraftRequiredJavaMajorVersion": required_java_major, "minecraftVersion": version.id}
