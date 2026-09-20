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


def test_button_events_do_not_leak_graphics_effect(gui_app) -> None:
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QPushButton

    runtime = MotionRuntime()
    button = QPushButton("Test")
    assert button.graphicsEffect() is None

    # Simulate hover event
    enter_event = QEvent(QEvent.Type.Enter)
    runtime._handle_button_event(button, enter_event)

    # Button should NOT have persistent conflicting graphics effect
    assert button.graphicsEffect() is None


def test_animate_visibility_finish_does_not_crash_on_deleted_effect(gui_app) -> None:
    from PySide6.QtWidgets import QWidget

    runtime = MotionRuntime()
    widget = QWidget()
    runtime.animate_visibility(widget, True)
    anim = getattr(widget, "_mcw_visibility_animation", None)
    assert anim is not None
    # Trigger finished signal to ensure finish() does not raise RuntimeError
    anim.finished.emit()
    assert getattr(widget, "_mcw_visibility_animation", None) is None
    assert widget.graphicsEffect() is None


