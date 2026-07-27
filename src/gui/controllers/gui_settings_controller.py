from __future__ import annotations

from PySide6.QtCore import QByteArray, Signal

from src.core.config.curseforge_config_manager import CurseForgeConfigManager
from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.core.config.managed_content_policy import ManagedContentPolicy
from src.core.language.language_manager import tr
from src.core.network.download_bandwidth_limiter import download_bandwidth_limiter
from src.core.network.download_manager import download_manager
from src.core.network.network_session import DEFAULT_MAX_CONCURRENT_DOWNLOADS
from src.gui.controllers.base_controller import BaseController


class GuiSettingsController(BaseController):
    settings_changed = Signal(dict)

    DEFAULTS = {
        "start_page": "home",
        "show_snapshots": False,
        "debug_mode": False,
        "remember_window_size": True,
        "language": "en-US",
        "auto_check_updates": True,
        "update_channel": "stable",
        "tester_mode": False,
        "theme": "mcw-default",
        "show_static_text": False,
        "modrinth_include_beta": False,
        "modrinth_include_alpha": False,
        "block_launch_on_modrinth_failure": True,
        "block_launch_on_curseforge_failure": True,
        "allow_launch_on_forge_preflight_failure": False,
        "curseforge_gateway_urls": (),
        "download_limit_mbps": 0.0,
        "download_concurrency": 0,
    }

    def __init__(self) -> None:
        super().__init__()
        self._settings = LauncherSettingsManager()
        self._current = dict(self.DEFAULTS)

    @property
    def current(self) -> dict:
        return dict(self._current)

    def raw_settings(self) -> dict:
        return self._settings.load()

    def load(self) -> dict:
        data = self._settings.load()
        gui = data.get("gui", {})
        launch = data.get("launch", {})
        updates = data.get("updates", {})
        appearance = data.get("appearance", {})
        modrinth = data.get("modrinth", {})
        managed_content = data.get("managed_content", {})
        network = data.get("network", {})
        try:
            curseforge_gateway_urls = CurseForgeConfigManager.gateway_urls()
        except (RuntimeError, ValueError):
            curseforge_gateway_urls = ()
        self._current = {
            "start_page": str(gui.get("start_page", self.DEFAULTS["start_page"])),
            "show_snapshots": bool(gui.get("show_snapshots", self.DEFAULTS["show_snapshots"])),
            "debug_mode": bool(launch.get("debug_mode", self.DEFAULTS["debug_mode"])),
            "remember_window_size": bool(gui.get("remember_window_size", self.DEFAULTS["remember_window_size"])),
            "language": str(gui.get("language", self.DEFAULTS["language"])),
            "auto_check_updates": bool(updates.get("auto_check", self.DEFAULTS["auto_check_updates"])),
            "update_channel": str(updates.get("channel", self.DEFAULTS["update_channel"])),
            "tester_mode": str(updates.get("channel", self.DEFAULTS["update_channel"])).strip().lower() == "beta",
            "theme": str(appearance.get("theme", self.DEFAULTS["theme"])),
            "show_static_text": bool(appearance.get("show_static_text", self.DEFAULTS["show_static_text"])),
            "modrinth_include_beta": bool(modrinth.get("include_beta", self.DEFAULTS["modrinth_include_beta"])),
            "modrinth_include_alpha": bool(modrinth.get("include_alpha", self.DEFAULTS["modrinth_include_alpha"])),
            "block_launch_on_modrinth_failure": ManagedContentPolicy.normalize_global(managed_content.get("modrinth_failure_policy")) == ManagedContentPolicy.BLOCK,
            "block_launch_on_curseforge_failure": ManagedContentPolicy.normalize_global(managed_content.get("curseforge_failure_policy")) == ManagedContentPolicy.BLOCK,
            "allow_launch_on_forge_preflight_failure": ManagedContentPolicy.normalize_global(managed_content.get("forge_preflight_failure_policy")) == ManagedContentPolicy.ALLOW,
            "curseforge_gateway_urls": tuple(curseforge_gateway_urls),
            "download_limit_mbps": float(network.get("download_limit_mbps", self.DEFAULTS["download_limit_mbps"]) or 0.0),
            "download_concurrency": int(network.get("download_concurrency", self.DEFAULTS["download_concurrency"]) or 0),
        }
        download_bandwidth_limiter.configure_mbps(self._current["download_limit_mbps"])
        download_manager.configure(self._current["download_concurrency"] or DEFAULT_MAX_CONCURRENT_DOWNLOADS)
        self.settings_changed.emit(dict(self._current))
        return dict(self._current)

    def save(self, data: dict) -> None:
        try:
            CurseForgeConfigManager.save_local(data.get("curseforge_gateway_urls", self.DEFAULTS["curseforge_gateway_urls"]))
            curseforge_gateway_urls = CurseForgeConfigManager.gateway_urls()
        except (OSError, RuntimeError, ValueError) as error:
            self._emit_error(tr("curseforge.gateway.save.error.title"), error)
            return
        download_limit_mbps = download_bandwidth_limiter.configure_mbps(data.get("download_limit_mbps", self.DEFAULTS["download_limit_mbps"]))
        try:
            download_concurrency = int(data.get("download_concurrency", self.DEFAULTS["download_concurrency"]) or 0)
        except (TypeError, ValueError):
            download_concurrency = 0
        download_concurrency = 0 if download_concurrency <= 0 else min(download_concurrency, 16)
        download_manager.configure(download_concurrency or DEFAULT_MAX_CONCURRENT_DOWNLOADS)
        tester_mode = bool(data.get("tester_mode", self.DEFAULTS["tester_mode"]))
        update_channel = "beta" if tester_mode else "stable"
        self._current = {
            "start_page": str(data.get("start_page", self.DEFAULTS["start_page"])),
            "show_snapshots": bool(data.get("show_snapshots", self.DEFAULTS["show_snapshots"])),
            "debug_mode": bool(data.get("debug_mode", self.DEFAULTS["debug_mode"])),
            "remember_window_size": bool(data.get("remember_window_size", self.DEFAULTS["remember_window_size"])),
            "language": str(data.get("language", self.DEFAULTS["language"])),
            "auto_check_updates": bool(data.get("auto_check_updates", self.DEFAULTS["auto_check_updates"])),
            "update_channel": update_channel,
            "tester_mode": tester_mode,
            "theme": str(data.get("theme", self.DEFAULTS["theme"])),
            "show_static_text": bool(data.get("show_static_text", self.DEFAULTS["show_static_text"])),
            "modrinth_include_beta": bool(data.get("modrinth_include_beta", self.DEFAULTS["modrinth_include_beta"])),
            "modrinth_include_alpha": bool(data.get("modrinth_include_alpha", self.DEFAULTS["modrinth_include_alpha"])),
            "block_launch_on_modrinth_failure": bool(data.get("block_launch_on_modrinth_failure", self.DEFAULTS["block_launch_on_modrinth_failure"])),
            "block_launch_on_curseforge_failure": bool(data.get("block_launch_on_curseforge_failure", self.DEFAULTS["block_launch_on_curseforge_failure"])),
            "allow_launch_on_forge_preflight_failure": bool(data.get("allow_launch_on_forge_preflight_failure", self.DEFAULTS["allow_launch_on_forge_preflight_failure"])),
            "curseforge_gateway_urls": tuple(curseforge_gateway_urls),
            "download_limit_mbps": download_limit_mbps,
            "download_concurrency": download_concurrency,
        }
        self._settings.save({
            "gui": {
                "start_page": self._current["start_page"],
                "show_snapshots": self._current["show_snapshots"],
                "remember_window_size": self._current["remember_window_size"],
                "language": self._current["language"],
            },
            "launch": {"debug_mode": self._current["debug_mode"]},
            "updates": {
                "auto_check": self._current["auto_check_updates"],
                "channel": self._current["update_channel"],
            },
            "appearance": {"theme": self._current["theme"], "show_static_text": self._current["show_static_text"]},
            "modrinth": {
                "include_beta": self._current["modrinth_include_beta"],
                "include_alpha": self._current["modrinth_include_alpha"],
            },
            "managed_content": {
                "modrinth_failure_policy": ManagedContentPolicy.BLOCK if self._current["block_launch_on_modrinth_failure"] else ManagedContentPolicy.ALLOW,
                "curseforge_failure_policy": ManagedContentPolicy.BLOCK if self._current["block_launch_on_curseforge_failure"] else ManagedContentPolicy.ALLOW,
                "forge_preflight_failure_policy": ManagedContentPolicy.ALLOW if self._current["allow_launch_on_forge_preflight_failure"] else ManagedContentPolicy.BLOCK,
            },
            "network": {
                "download_limit_mbps": self._current["download_limit_mbps"],
                "download_concurrency": self._current["download_concurrency"],
            },
        })
        self.settings_changed.emit(dict(self._current))
        self.status_changed.emit(tr("Launcher settings saved"))
        self.log_created.emit(tr("GUI preferences saved"))

    def set_auto_check_updates(self, enabled: bool) -> None:
        self._current["auto_check_updates"] = bool(enabled)
        self._settings.update_section("updates", {"auto_check": bool(enabled)})
        self.settings_changed.emit(dict(self._current))

    def set_modrinth_channels(self, include_beta: bool, include_alpha: bool) -> None:
        self._current["modrinth_include_beta"] = bool(include_beta)
        self._current["modrinth_include_alpha"] = bool(include_alpha)
        self._settings.update_section("modrinth", {"include_beta": bool(include_beta), "include_alpha": bool(include_alpha)})
        self.settings_changed.emit(dict(self._current))

    def reset(self) -> None:
        self._settings.reset()
        self.load()
        self.status_changed.emit(tr("Launcher settings saved"))
        self.log_created.emit(tr("GUI preferences saved"))

    def saved_geometry(self) -> QByteArray | None:
        geometry = self._settings.load_window_geometry()
        return QByteArray(geometry) if geometry is not None else None

    def save_geometry(self, geometry: QByteArray) -> None:
        self._settings.save_window_geometry(bytes(geometry))
