from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.gui.widget.themed_animated_label import ThemedAnimatedLabel
    from src.gui.widget.themed_progress_bar import ThemedProgressBar

__all__ = ["ThemedAnimatedLabel", "ThemedProgressBar"]

_LAZY_EXPORTS = {
    "ThemedAnimatedLabel": ("src.gui.widget.themed_animated_label", "ThemedAnimatedLabel"),
    "ThemedProgressBar": ("src.gui.widget.themed_progress_bar", "ThemedProgressBar"),
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
