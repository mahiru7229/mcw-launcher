"""MCW Launcher GUI Core subsystem.

Provides centralized state management, a unified task/download queue, and a
high-level facade for UI views and components.
"""

from src.gui.core.app_state import AppState
from src.gui.core.gui_context import GuiContext, get_default_gui_context, set_default_gui_context
from src.gui.core.task_queue import TaskQueue, TaskQueueItem

__all__ = [
    "AppState",
    "GuiContext",
    "TaskQueue",
    "TaskQueueItem",
    "get_default_gui_context",
    "set_default_gui_context",
]
