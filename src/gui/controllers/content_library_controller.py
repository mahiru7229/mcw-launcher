from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr

from mcw_core.api.content.installed_content_library import InstalledContentLibraryManager
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner
from src.models.instance.instance import Instance


class ContentLibraryController(BaseController):
    library_changed = Signal(object)
    instance_changed = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._instance: Instance | None = None
        self._refresh_pending = False
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    @property
    def current_instance(self) -> Instance | None:
        return self._instance

    def set_instance(self, instance: Instance | None, *, refresh: bool = True) -> None:
        self._instance = instance
        self._refresh_pending = False
        self.instance_changed.emit(instance)
        if instance is None:
            self.library_changed.emit(None)
            return
        if refresh:
            self.refresh()

    def refresh(self) -> bool:
        instance = self._instance
        if instance is None:
            self._emit_error("Content Library", "Select an instance first.")
            return False
        if self._task_runner.is_task_active("content.library.scan"):
            self._refresh_pending = True
            return False
        instance_id = instance.instance_id
        return self._task_runner.run("content.library.scan", lambda: (instance_id, InstalledContentLibraryManager.scan(instance)), tr("task.content_library.scan", instance=instance.name), blocking=False)

    def import_local(self, content_type: str, paths: list[Path]) -> bool:
        instance = self._instance
        if instance is None or not paths:
            return False
        instance_id = instance.instance_id
        normalized_paths = [Path(path) for path in paths]
        return self._task_runner.run(
            "content.library.import",
            lambda: (instance_id, InstalledContentLibraryManager.import_local(instance, content_type, normalized_paths)),
            tr("task.content_library.import_local", count=len(normalized_paths)),
        )

    def set_enabled(self, item_ids: list[str], enabled: bool) -> bool:
        instance = self._instance
        if instance is None or not item_ids:
            return False
        instance_id = instance.instance_id
        action = "Enabling" if enabled else "Disabling"
        return self._task_runner.run("content.library.toggle", lambda: (instance_id, InstalledContentLibraryManager.set_enabled(instance, item_ids, enabled)), tr("task.content_library.change_state", action=action, count=len(item_ids)))

    def remove(self, item_ids: list[str]) -> bool:
        instance = self._instance
        if instance is None or not item_ids:
            return False
        instance_id = instance.instance_id
        return self._task_runner.run("content.library.remove", lambda: (instance_id, InstalledContentLibraryManager.remove(instance, item_ids)), tr("task.content_library.remove", count=len(item_ids)))

    def set_pinned(self, item_ids: list[str], pinned: bool) -> bool:
        instance = self._instance
        if instance is None or not item_ids:
            return False
        instance_id = instance.instance_id
        return self._task_runner.run("content.library.pin", lambda: (instance_id, InstalledContentLibraryManager.set_pinned(instance, item_ids, pinned)), tr("task.content_library.update_pins"), blocking=False)

    def set_ignored_update(self, item_ids: list[str], ignored: bool) -> bool:
        instance = self._instance
        if instance is None or not item_ids:
            return False
        instance_id = instance.instance_id
        return self._task_runner.run("content.library.ignore", lambda: (instance_id, InstalledContentLibraryManager.set_ignored_update(instance, item_ids, ignored)), tr("task.content_library.update_preferences"), blocking=False)

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == "content.library.scan":
            instance_id, library = result
            if self._matches_instance(instance_id):
                self.library_changed.emit(library)
            self._run_pending_refresh()
            return
        if task_id in {"content.library.import", "content.library.toggle", "content.library.remove", "content.library.pin", "content.library.ignore"}:
            instance_id, changed = result
            if self._matches_instance(instance_id):
                self.status_changed.emit(tr("status.content.updated_items", count=len(changed)))
                self.refresh()

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if not task_id.startswith("content.library."):
            return
        self._emit_error("Content Library", error)
        if task_id == "content.library.scan":
            self._run_pending_refresh()

    def _run_pending_refresh(self) -> None:
        if not self._refresh_pending:
            return
        self._refresh_pending = False
        self.refresh()

    def _matches_instance(self, instance_id: str) -> bool:
        return self._instance is not None and self._instance.instance_id == str(instance_id)
