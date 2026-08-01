from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.gui.theme.accent_runtime import ThemeAccentRuntime, theme_accent_runtime
    from src.gui.theme.font_runtime import ThemeFontRuntime, theme_font_runtime
    from src.gui.theme.runtime import ThemeRuntime, set_theme_icon, set_theme_pixmap, set_theme_static_text

__all__ = [
    "ThemeAccentRuntime",
    "ThemeFontRuntime",
    "ThemeRuntime",
    "set_theme_icon",
    "set_theme_pixmap",
    "set_theme_static_text",
    "theme_accent_runtime",
    "theme_font_runtime",
]

_LAZY_EXPORTS = {
    "ThemeAccentRuntime": ("src.gui.theme.accent_runtime", "ThemeAccentRuntime"),
    "ThemeFontRuntime": ("src.gui.theme.font_runtime", "ThemeFontRuntime"),
    "ThemeRuntime": ("src.gui.theme.runtime", "ThemeRuntime"),
    "set_theme_icon": ("src.gui.theme.runtime", "set_theme_icon"),
    "set_theme_pixmap": ("src.gui.theme.runtime", "set_theme_pixmap"),
    "set_theme_static_text": ("src.gui.theme.runtime", "set_theme_static_text"),
    "theme_accent_runtime": ("src.gui.theme.accent_runtime", "theme_accent_runtime"),
    "theme_font_runtime": ("src.gui.theme.font_runtime", "theme_font_runtime"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _LAZY_EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
