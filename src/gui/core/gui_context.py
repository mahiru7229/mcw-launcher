from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject

from src.gui.core.app_state import AppState
from src.gui.core.task_queue import TaskQueue
from src.gui.task_runner import TaskRunner


class GuiContext(QObject):
    """Unified GUI Context and Facade for MCW Launcher.

    Aggregates the centralized AppState, TaskQueue, and registered controllers.
    Serves as the single facade for UI views and widgets to query state and
    dispatch operations without relying on MainWindow as a god object.
    """

    def __init__(self, task_runner: TaskRunner | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.state = AppState(parent=self)
        self.runner = task_runner
        self.tasks = TaskQueue(runner=task_runner, parent=self)
        self._controllers: dict[str, Any] = {}

    def set_task_runner(self, runner: TaskRunner) -> None:
        self.runner = runner
        self.tasks.attach_runner(runner)

    def register_controller(self, name: str, controller: Any) -> None:
        key = str(name).strip().casefold()
        self._controllers[key] = controller
        self._wire_controller_to_state(key, controller)

    def controller(self, name: str) -> Any:
        return self._controllers.get(str(name).strip().casefold())

    # --- Convenience Accessors for Primary Subsystems ---

    @property
    def instances(self) -> Any:
        return self.controller("instances")

    @property
    def accounts(self) -> Any:
        return self.controller("accounts")

    @property
    def launch(self) -> Any:
        return self.controller("launch")

    @property
    def settings(self) -> Any:
        return self.controller("settings")

    @property
    def updates(self) -> Any:
        return self.controller("updates")

    @property
    def modrinth(self) -> Any:
        return self.controller("modrinth")

    @property
    def curseforge(self) -> Any:
        return self.controller("curseforge")

    # --- Internal Signal Wiring ---

    def _wire_controller_to_state(self, name: str, controller: Any) -> None:
        if name == "instances":
            if hasattr(controller, "instances_changed"):
                controller.instances_changed.connect(self.state.set_instances)
            if hasattr(controller, "selected_instance_changed"):
                controller.selected_instance_changed.connect(self.state.set_selected_instance)
            if hasattr(controller, "running_instances_changed"):
                controller.running_instances_changed.connect(self.state.set_running_instances)
            if hasattr(controller, "health_reports_changed"):
                controller.health_reports_changed.connect(self.state.set_health_reports)

        elif name == "accounts":
            if hasattr(controller, "accounts_changed"):
                controller.accounts_changed.connect(self.state.set_accounts)
            if hasattr(controller, "selected_account_changed"):
                controller.selected_account_changed.connect(self.state.set_selected_account)

        elif name == "connectivity":
            if hasattr(controller, "connectivity_changed"):
                controller.connectivity_changed.connect(self.state.set_online)


_default_gui_context: GuiContext | None = None


def get_default_gui_context() -> GuiContext | None:
    return _default_gui_context


def set_default_gui_context(context: GuiContext | None) -> None:
    global _default_gui_context
    _default_gui_context = context
