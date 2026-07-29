import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.animation.motion_runtime import MotionMode, MotionRuntime


def test_motion_mode_normalizes_unknown_values() -> None:
    assert MotionMode.normalize("full") == "full"
    assert MotionMode.normalize("REDUCED") == "reduced"
    assert MotionMode.normalize("off") == "off"
    assert MotionMode.normalize("unknown") == "full"


def test_reduced_motion_shortens_duration(gui_app) -> None:
    runtime = MotionRuntime()

    runtime.apply("full")
    assert runtime.duration(200) == 200

    runtime.apply("reduced")
    assert runtime.duration(200) == 90
    assert runtime.duration(0) == 0

    runtime.apply("off")
    assert runtime.duration(200) == 0
