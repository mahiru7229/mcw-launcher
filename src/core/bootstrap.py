from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.core.account.database.account_database import AccountDatabase
from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.core.fs.paths import Paths
from src.core.network.download_bandwidth_limiter import download_bandwidth_limiter
from src.core.security.account_security_manager import AccountSecurityManager

BootstrapProgressCallback = Callable[[int, str], None]


def _report(callback: BootstrapProgressCallback | None, percent: int, message_key: str) -> None:
    if callback is not None:
        callback(percent, message_key)


def initialize_application(progress_callback: BootstrapProgressCallback | None = None) -> dict[str, Any]:
    """Prepare persistent application resources and report startup progress when requested."""
    _report(progress_callback, 8, "startup.preparing_directories")
    Paths.initialize()

    _report(progress_callback, 24, "startup.loading_settings")
    settings_manager = LauncherSettingsManager()
    settings_manager.initialize()
    settings = settings_manager.load()

    _report(progress_callback, 42, "startup.configuring_downloads")
    download_bandwidth_limiter.configure_mbps(settings.get("network", {}).get("download_limit_mbps", 0.0))

    _report(progress_callback, 62, "startup.preparing_accounts")
    AccountDatabase.initialize()

    _report(progress_callback, 80, "startup.protecting_accounts")
    AccountSecurityManager.migrate_if_needed()

    _report(progress_callback, 90, "startup.core_ready")
    return settings
