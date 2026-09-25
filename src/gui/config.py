from __future__ import annotations

import sys
from pathlib import Path

from src.config import DEVELOPER_NAME, GITHUB_REPOSITORY, LAUNCHER_NAME, UPDATE_CHANNEL, VERSION, VERSION_ID

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
MINIMUM_WIDTH = 1180
MINIMUM_HEIGHT = 700
SIDEBAR_WIDTH = 220
RIGHT_PANEL_WIDTH = 400

NAVIGATION_ITEMS = (
    ("instances", "navigation.instances"),
    ("accounts", "navigation.accounts"),
    ("launcher_settings", "navigation.launcher_settings"),
    ("logs", "navigation.logs"),
    ("about", "navigation.about"),
)


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> Path:
    return application_root().joinpath("assets", *parts)


MAIN_LOGO_PATH = asset_path("images", "logo", "main_launcher_logo.png")


def get_active_hotfix_version() -> str | None:
    try:
        from mcw_core.api.update.hotfix_manager import HotfixManager

        manager = HotfixManager()
        state = manager.load_state()
        if state is not None and HotfixManager._matches_base_version(state.base_version, VERSION_ID):
            return state.target_version
    except Exception:
        pass
    return None


def get_display_version(include_hotfix: bool = True) -> str:
    if include_hotfix:
        hotfix_ver = get_active_hotfix_version()
        if hotfix_ver:
            return f"{VERSION} (Hotfix {hotfix_ver})"
    return VERSION

