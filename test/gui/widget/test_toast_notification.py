import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QWidget

from src.gui.animation.motion_runtime import MotionRuntime
from src.gui.widget.toast_notification import ToastManager


def test_toast_manager_limits_visible_notifications(gui_app) -> None:
    host = QWidget()
    host.resize(900, 600)
    host.show()
    runtime = MotionRuntime()
    runtime.apply("off")
    manager = ToastManager(host, runtime)

    maximum = runtime.definition.toast.max_visible
    for index in range(maximum + 2):
        manager.show(f"Message {index}", "success", "Title")

    assert manager.visible_count == maximum
    manager.clear()
    assert manager.visible_count == 0
    host.close()
