import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication

from src.gui.controllers.modrinth_controller import ModrinthController
from src.gui.task_runner import TaskRunner


def test_controller_ignores_unrelated_task_result():
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = ModrinthController(TaskRunner())
    emitted = []
    controller.search_results_changed.connect(lambda *args: emitted.append(args))

    controller._on_task_succeeded("versions.load", "x" * 901)

    assert emitted == []
