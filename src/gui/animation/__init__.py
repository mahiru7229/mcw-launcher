from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.gui.animation.animation_clock import AnimationClock
    from src.gui.animation.motion_runtime import MotionMode, MotionRuntime
    from src.gui.animation.theme_animation_player import ThemeAnimationPlayer

__all__ = ["AnimationClock", "MotionMode", "MotionRuntime", "ThemeAnimationPlayer"]

_LAZY_EXPORTS = {
    "AnimationClock": ("src.gui.animation.animation_clock", "AnimationClock"),
    "MotionMode": ("src.gui.animation.motion_runtime", "MotionMode"),
    "MotionRuntime": ("src.gui.animation.motion_runtime", "MotionRuntime"),
    "ThemeAnimationPlayer": ("src.gui.animation.theme_animation_player", "ThemeAnimationPlayer"),
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
