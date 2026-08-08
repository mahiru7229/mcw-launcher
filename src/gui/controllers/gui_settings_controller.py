from __future__ import annotations

import copy

from PySide6.QtCore import QByteArray, Signal

from mcw_core.api.config.curseforge_config_manager import CurseForgeConfigManager
from mcw_core.api.config.launcher_settings_manager import LauncherSettingsManager
from mcw_core.api.config.managed_content_policy import ManagedContentPolicy
from mcw_core.api.instance.settings_manager import SettingsManager, default_instance_settings
from mcw_core.api.language.language_manager import tr
from mcw_core.api.network.download_bandwidth_limiter import download_bandwidth_limiter
from mcw_core.api.network.download_manager import download_manager
from mcw_core.api.network.network_session import DEFAULT_MAX_CONCURRENT_DOWNLOADS
from src.gui.controllers.base_controller import BaseController


class GuiSettingsController(BaseController):
    settings_changed = Signal(dict)

    DEFAULTS = {
        "start_page": "instances",
        "show_snapshots": False,
        "debug_mode": False,
        "prefer_dedicated_gpu": False,
        "remember_window_size": True,
        "language": "en-US",
        "show_content_descriptions": False,
        "auto_check_updates": True,
        "update_channel": "stable",
        "tester_mode": False,
        "theme": "mcw-default",
        "show_static_text": False,
        "motion_mode": "full",
        "live_theme_reload": False,
        "accent_mode": "theme",
        "accent_color": "#8ed35b",
        "text_color_mode": "theme",
        "text_color": "#f4f4f4",
        "modrinth_include_beta": False,
        "modrinth_include_alpha": False,
        "block_launch_on_modrinth_failure": True,
        "block_launch_on_curseforge_failure": True,
        "allow_launch_on_forge_preflight_failure": False,
        "forge_preflight_failure_policy": ManagedContentPolicy.ASK,
        "curseforge_gateway_urls": (),
        "download_limit_mbps": 0.0,
        "download_concurrency": 0,
        "notify_legacy_cache_cleanup": True,
        "instance_defaults": default_instance_settings(),
    }

    def __init__(self) -> None:
        super().__init__()
        self._settings = LauncherSettingsManager()
        self._current = copy.deepcopy(self.DEFAULTS)

    @property
    def current(self) -> dict:
        return copy.deepcopy(self._current)

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
        storage = data.get("storage", {})
        try:
            curseforge_gateway_urls = CurseForgeConfigManager.gateway_urls()
        except (RuntimeError, ValueError):
            curseforge_gateway_urls = ()
        self._current = {
            "start_page": self._normalize_start_page(gui.get("start_page")),
            "show_snapshots": bool(gui.get("show_snapshots", self.DEFAULTS["show_snapshots"])),
            "debug_mode": bool(launch.get("debug_mode", self.DEFAULTS["debug_mode"])),
            "prefer_dedicated_gpu": bool(launch.get("prefer_dedicated_gpu", self.DEFAULTS["prefer_dedicated_gpu"])),
            "remember_window_size": bool(gui.get("remember_window_size", self.DEFAULTS["remember_window_size"])),
            "language": str(gui.get("language", self.DEFAULTS["language"])),
            "show_content_descriptions": bool(gui.get("show_content_descriptions", self.DEFAULTS["show_content_descriptions"])),
            "auto_check_updates": bool(updates.get("auto_check", self.DEFAULTS["auto_check_updates"])),
            "update_channel": str(updates.get("channel", self.DEFAULTS["update_channel"])),
            "tester_mode": str(updates.get("channel", self.DEFAULTS["update_channel"])).strip().lower() == "beta",
            "theme": str(appearance.get("theme", self.DEFAULTS["theme"])),
            "show_static_text": bool(appearance.get("show_static_text", self.DEFAULTS["show_static_text"])),
            "motion_mode": str(appearance.get("motion_mode", self.DEFAULTS["motion_mode"])),
            "live_theme_reload": bool(appearance.get("live_theme_reload", self.DEFAULTS["live_theme_reload"])),
            "accent_mode": str(appearance.get("accent_mode", self.DEFAULTS["accent_mode"])),
            "accent_color": str(appearance.get("accent_color", self.DEFAULTS["accent_color"])),
            "text_color_mode": str(appearance.get("text_color_mode", self.DEFAULTS["text_color_mode"])),
            "text_color": str(appearance.get("text_color", self.DEFAULTS["text_color"])),
            "modrinth_include_beta": bool(modrinth.get("include_beta", self.DEFAULTS["modrinth_include_beta"])),
            "modrinth_include_alpha": bool(modrinth.get("include_alpha", self.DEFAULTS["modrinth_include_alpha"])),
            "block_launch_on_modrinth_failure": ManagedContentPolicy.normalize_global(managed_content.get("modrinth_failure_policy")) == ManagedContentPolicy.BLOCK,
            "block_launch_on_curseforge_failure": ManagedContentPolicy.normalize_global(managed_content.get("curseforge_failure_policy")) == ManagedContentPolicy.BLOCK,
            "allow_launch_on_forge_preflight_failure": ManagedContentPolicy.normalize_global(managed_content.get("forge_preflight_failure_policy"), ManagedContentPolicy.ASK) == ManagedContentPolicy.ALLOW,
            "forge_preflight_failure_policy": ManagedContentPolicy.normalize_global(managed_content.get("forge_preflight_failure_policy"), ManagedContentPolicy.ASK),
            "curseforge_gateway_urls": tuple(curseforge_gateway_urls),
            "download_limit_mbps": float(network.get("download_limit_mbps", self.DEFAULTS["download_limit_mbps"]) or 0.0),
            "download_concurrency": int(network.get("download_concurrency", self.DEFAULTS["download_concurrency"]) or 0),
            "notify_legacy_cache_cleanup": bool(storage.get("notify_legacy_cache_cleanup", self.DEFAULTS["notify_legacy_cache_cleanup"])),
            "instance_defaults": SettingsManager.normalize_dict(data.get("instance_defaults")),
        }
        download_bandwidth_limiter.configure_mbps(self._current["download_limit_mbps"])
        download_manager.configure(self._current["download_concurrency"] or DEFAULT_MAX_CONCURRENT_DOWNLOADS)
        self.settings_changed.emit(copy.deepcopy(self._current))
        return copy.deepcopy(self._current)

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
            "start_page": self._normalize_start_page(data.get("start_page")),
            "show_snapshots": bool(data.get("show_snapshots", self.DEFAULTS["show_snapshots"])),
            "debug_mode": bool(data.get("debug_mode", self.DEFAULTS["debug_mode"])),
            "prefer_dedicated_gpu": bool(data.get("prefer_dedicated_gpu", self.DEFAULTS["prefer_dedicated_gpu"])),
            "remember_window_size": bool(data.get("remember_window_size", self.DEFAULTS["remember_window_size"])),
            "language": str(data.get("language", self.DEFAULTS["language"])),
            "show_content_descriptions": bool(data.get("show_content_descriptions", self.DEFAULTS["show_content_descriptions"])),
            "auto_check_updates": bool(data.get("auto_check_updates", self.DEFAULTS["auto_check_updates"])),
            "update_channel": update_channel,
            "tester_mode": tester_mode,
            "theme": str(data.get("theme", self.DEFAULTS["theme"])),
            "show_static_text": bool(data.get("show_static_text", self.DEFAULTS["show_static_text"])),
            "motion_mode": str(data.get("motion_mode", self.DEFAULTS["motion_mode"])),
            "live_theme_reload": bool(data.get("live_theme_reload", self.DEFAULTS["live_theme_reload"])),
            "accent_mode": str(data.get("accent_mode", self.DEFAULTS["accent_mode"])),
            "accent_color": str(data.get("accent_color", self.DEFAULTS["accent_color"])),
            "text_color_mode": str(data.get("text_color_mode", self.DEFAULTS["text_color_mode"])),
            "text_color": str(data.get("text_color", self.DEFAULTS["text_color"])),
            "modrinth_include_beta": bool(data.get("modrinth_include_beta", self.DEFAULTS["modrinth_include_beta"])),
            "modrinth_include_alpha": bool(data.get("modrinth_include_alpha", self.DEFAULTS["modrinth_include_alpha"])),
            "block_launch_on_modrinth_failure": bool(data.get("block_launch_on_modrinth_failure", self.DEFAULTS["block_launch_on_modrinth_failure"])),
            "block_launch_on_curseforge_failure": bool(data.get("block_launch_on_curseforge_failure", self.DEFAULTS["block_launch_on_curseforge_failure"])),
            "allow_launch_on_forge_preflight_failure": bool(data.get("allow_launch_on_forge_preflight_failure", self.DEFAULTS["allow_launch_on_forge_preflight_failure"])),
            "forge_preflight_failure_policy": ManagedContentPolicy.normalize_global(
                data.get("forge_preflight_failure_policy", ManagedContentPolicy.ALLOW if data.get("allow_launch_on_forge_preflight_failure") else ManagedContentPolicy.ASK),
                ManagedContentPolicy.ASK,
            ),
            "curseforge_gateway_urls": tuple(curseforge_gateway_urls),
            "download_limit_mbps": download_limit_mbps,
            "download_concurrency": download_concurrency,
            "notify_legacy_cache_cleanup": bool(data.get("notify_legacy_cache_cleanup", self.DEFAULTS["notify_legacy_cache_cleanup"])),
            "instance_defaults": SettingsManager.normalize_dict(data.get("instance_defaults")),
        }
        self._settings.save({
            "gui": {
                "start_page": self._current["start_page"],
                "show_snapshots": self._current["show_snapshots"],
                "remember_window_size": self._current["remember_window_size"],
                "language": self._current["language"],
                "show_content_descriptions": self._current["show_content_descriptions"],
            },
            "launch": {"debug_mode": self._current["debug_mode"], "prefer_dedicated_gpu": self._current["prefer_dedicated_gpu"]},
            "updates": {
                "auto_check": self._current["auto_check_updates"],
                "channel": self._current["update_channel"],
            },
            "appearance": {"theme": self._current["theme"], "show_static_text": self._current["show_static_text"], "motion_mode": self._current["motion_mode"], "live_theme_reload": self._current["live_theme_reload"], "accent_mode": self._current["accent_mode"], "accent_color": self._current["accent_color"], "text_color_mode": self._current["text_color_mode"], "text_color": self._current["text_color"]},
            "modrinth": {
                "include_beta": self._current["modrinth_include_beta"],
                "include_alpha": self._current["modrinth_include_alpha"],
            },
            "managed_content": {
                "modrinth_failure_policy": ManagedContentPolicy.BLOCK if self._current["block_launch_on_modrinth_failure"] else ManagedContentPolicy.ALLOW,
                "curseforge_failure_policy": ManagedContentPolicy.BLOCK if self._current["block_launch_on_curseforge_failure"] else ManagedContentPolicy.ALLOW,
                "forge_preflight_failure_policy": self._current["forge_preflight_failure_policy"],
            },
            "network": {
                "download_limit_mbps": self._current["download_limit_mbps"],
                "download_concurrency": self._current["download_concurrency"],
            },
            "storage": {
                "notify_legacy_cache_cleanup": self._current["notify_legacy_cache_cleanup"],
            },
            "instance_defaults": self._current["instance_defaults"],
        })
        self.settings_changed.emit(copy.deepcopy(self._current))
        self.status_changed.emit(tr("Launcher settings saved"))
        self.log_created.emit(tr("GUI preferences saved"))


    @classmethod
    def _normalize_start_page(cls, value: object) -> str:
        page = str(value or cls.DEFAULTS["start_page"]).strip()
        return page if page in {"instances", "accounts", "launcher_settings", "logs", "about"} else "instances"

    def set_auto_check_updates(self, enabled: bool) -> None:
        self._current["auto_check_updates"] = bool(enabled)
        self._settings.update_section("updates", {"auto_check": bool(enabled)})
        self.settings_changed.emit(copy.deepcopy(self._current))

    def set_modrinth_channels(self, include_beta: bool, include_alpha: bool) -> None:
        self._current["modrinth_include_beta"] = bool(include_beta)
        self._current["modrinth_include_alpha"] = bool(include_alpha)
        self._settings.update_section("modrinth", {"include_beta": bool(include_beta), "include_alpha": bool(include_alpha)})
        self.settings_changed.emit(copy.deepcopy(self._current))

    def set_notify_legacy_cache_cleanup(self, enabled: bool) -> None:
        self._current["notify_legacy_cache_cleanup"] = bool(enabled)
        self._settings.update_section("storage", {"notify_legacy_cache_cleanup": bool(enabled)})
        self.settings_changed.emit(copy.deepcopy(self._current))

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
