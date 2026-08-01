import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.animation.animation_clock import AnimationClock


def test_animation_clock_uses_motion_mode_fps(gui_app) -> None:
    clock = AnimationClock()

    clock.configure("full", full_fps=60, reduced_fps=30, pause_when_hidden=False)
    assert clock.interval_ms == 17
    assert not clock.is_suspended

    clock.configure("reduced", full_fps=60, reduced_fps=30, pause_when_hidden=False)
    assert clock.interval_ms == 33
    assert not clock.is_suspended

    clock.configure("off", full_fps=60, reduced_fps=30, pause_when_hidden=False)
    assert clock.is_suspended
