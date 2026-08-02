from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal, Slot

from mcw_core import InstanceCreateRequest, InstanceDeletionError, LoaderService, get_default_core
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner
from src.config import VERSION_ID


class InstanceController(BaseController):
    instances_changed = Signal(list, str)
    running_instances_changed = Signal(list)
    health_reports_changed = Signal(list)
    selected_instance_changed = Signal(object)
    export_finished = Signal(object)
    repair_progress = Signal(object)
    loader_progress = Signal(object)
    package_progress = Signal(object)
    repair_finished = Signal(object)
    repair_scan_finished = Signal(object)
    repair_execution_finished = Signal(object)
    repair_center_failed = Signal(object)
    forge_diagnostics_finished = Signal(object)
    instance_created = Signal(object)
    import_preview_ready = Signal(object)

    CREATE_TASK_ID = "instance.create"
    IMPORT_INSPECT_TASK_ID = "instance.import.inspect"
    IMPORT_TASK_ID = "instance.import"
    REPAIR_TASK_ID = "instance.repair.full"
    REPAIR_SCAN_TASK_ID = "instance.repair.scan"
    REPAIR_EXECUTE_TASK_ID = "instance.repair.execute"
    LOADER_CHANGE_TASK_ID = "instance.loader"
    LOADER_REPAIR_TASK_ID = "instance.loader.repair"
    FORGE_RESTORE_TASK_ID = "instance.loader.restore"
    FORGE_DIAGNOSTICS_TASK_ID = "instance.forge.diagnostics"
    ICON_CHANGE_TASK_ID = "instance.icon.change"
    ICON_RESET_TASK_ID = "instance.icon.reset"
    INSTANCE_NAME_PATTERN = re.compile(r'^[^<>:"/\\|?*\x00-\x1F]{1,80}$')

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._core = get_default_core()
        self._selected_name = ""
        self._running_signature: tuple[tuple[object, ...], ...] | None = None
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def refresh(self, selected_name: str = "") -> None:
        try:
            instances = sorted(self._core.instances.list(), key=lambda item: item.name.casefold())
        except Exception as error:
            self._emit_error("Instances", error)
            return

        names = [instance.name for instance in instances]
        preferred = selected_name or self._selected_name
        if preferred not in names:
            preferred = names[0] if names else ""
        self._selected_name = preferred
        self.instances_changed.emit(instances, preferred)
        try:
            health_reports = self._core.instances.list_health()
        except Exception as error:
            health_reports = []
            self.log_created.emit(f"Instance health scan failed: {type(error).__name__}: {error}")
        self.health_reports_changed.emit(health_reports)
        self.select(preferred)
        self.log_created.emit(f"Instances refreshed: {len(instances)} found")

    def refresh_running(self, force: bool = False) -> None:
        running_instances = self._core.instances.list_running()
        signature = tuple((item.instance_id, item.name, item.state, item.launcher_pid, item.minecraft_pid) for item in running_instances)

        if not force and signature == self._running_signature:
            return

        self._running_signature = signature
        self.running_instances_changed.emit(running_instances)

    def select(self, name: str) -> None:
        self._selected_name = name.strip()
        if not self._selected_name:
            self.selected_instance_changed.emit(None)
            return
        try:
            instance = self._core.instances.load(self._selected_name)
        except Exception as error:
            self._emit_error("Load instance", error)
            return
        self.selected_instance_changed.emit(instance)

    def create(self, name: str, version_id: str, loader_name: str = "vanilla", loader_version: str = LoaderService.AUTO) -> bool:
        name = self._validated_name(name)
        version_id = version_id.strip()
        loader_name, loader_version = self._core.loaders.normalize((loader_name, loader_version))
        if name is None or not version_id:
            if not version_id:
                self._emit_error("Create instance", "Select a Minecraft version first.")
            return False

        def task() -> Any:
            return self._core.instances.create(
                InstanceCreateRequest(
                    name=name,
                    version_id=version_id,
                    loader_name=loader_name,
                    loader_version=loader_version,
                    on_progress=self._on_loader_progress,
                )
            )

        return self._task_runner.run(self.CREATE_TASK_ID, task, f"Creating instance '{name}'...")

    def change_loader(self, name: str, loader_name: str, loader_version: str) -> None:
        name = name.strip()
        loader_name, loader_version = self._core.loaders.normalize((loader_name, loader_version))
        if not name:
            return
        if loader_name in LoaderService.MODDED_LOADERS and not loader_version:
            self._emit_error("Change mod loader", "Select a mod-loader version first.")
            return

        def task() -> Any:
            return self._core.instances.change_loader(name, loader_name, loader_version, self._on_loader_progress)

        self._task_runner.run(self.LOADER_CHANGE_TASK_ID, task, f"Applying {loader_name.title()} to '{name}'...")

    def repair_loader(self, name: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.repair_loader(name, self._on_loader_progress)

        self._task_runner.run(self.LOADER_REPAIR_TASK_ID, task, f"Repairing mod loader for '{name}'...")

    def restore_previous_forge(self, name: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.restore_previous_loader(name, self._on_loader_progress)

        self._task_runner.run(self.FORGE_RESTORE_TASK_ID, task, f"Restoring previous mod-loader installation for '{name}'...")

    def export_forge_diagnostics(self, name: str, output_path: Path) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Path:
            return self._core.instances.export_loader_diagnostics(name, output_path)

        self._task_runner.run(self.FORGE_DIAGNOSTICS_TASK_ID, task, f"Exporting mod-loader diagnostics for '{name}'...", blocking=False)


    def repair_instance(self, name: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.repair(name, self._on_repair_progress)

        self._task_runner.run(self.REPAIR_TASK_ID, task, f"Repairing '{name}'...")

    def scan_repair_center(self, name: str, mode: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.scan_repair(name, mode, self._on_repair_progress)

        self._task_runner.run(self.REPAIR_SCAN_TASK_ID, task, f"Checking instance '{name}'...")

    def execute_repair_plan(self, name: str, plan: object) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.execute_repair(name, plan, self._on_repair_progress)

        self._task_runner.run(self.REPAIR_EXECUTE_TASK_ID, task, f"Repairing selected components for '{name}'...")

    def _on_repair_progress(self, event: object) -> None:
        self.repair_progress.emit(event)
        stage = getattr(getattr(event, "stage", None), "value", "repair")
        message = str(getattr(event, "message", "Repairing instance..."))
        self.log_created.emit(f"[{stage}] {message}")

    def _on_loader_progress(self, event: object) -> None:
        self.loader_progress.emit(event)
        stage = getattr(getattr(event, "stage", None), "value", "mod_loader")
        message = str(getattr(event, "message", "Preparing mod loader..."))
        self.log_created.emit(f"[{stage}] {message}")

    def rename(self, source_name: str, target_name: str) -> None:
        source_name = source_name.strip()
        target_name = self._validated_name(target_name)
        if not source_name or target_name is None:
            return

        def task() -> dict[str, str]:
            self._core.instances.rename(source_name, target_name)
            return {"source": source_name, "target": target_name}

        self._task_runner.run("instance.rename", task, f"Renaming '{source_name}'...")

    def clone(self, source_name: str, target_name: str, include_saves: bool) -> None:
        source_name = source_name.strip()
        target_name = self._validated_name(target_name)
        if not source_name or target_name is None:
            return

        def task() -> Any:
            return self._core.instances.clone(source_name, target_name, include_saves)

        self._task_runner.run("instance.clone", task, f"Cloning '{source_name}'...")

    def delete(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run("instance.delete", lambda: {"name": name, "deleted": self._core.instances.delete(name)}, f"Deleting '{name}'...")

    def inspect_package(self, package_path: Path) -> None:
        package_path = Path(package_path)
        self._task_runner.run(
            self.IMPORT_INSPECT_TASK_ID,
            lambda: self._core.instances.inspect_package(package_path),
            f"Reading '{package_path.name}'...",
        )

    def import_package(self, package_path: Path, settings_override: dict | None = None) -> None:
        package_path = Path(package_path)
        normalized_override = copy.deepcopy(settings_override)
        self._task_runner.run(
            self.IMPORT_TASK_ID,
            lambda: self._core.instances.import_package(
                package_path,
                self._on_package_progress,
                settings_override=normalized_override,
            ),
            f"Importing '{package_path.name}'...",
        )

    def change_icon(self, name: str, source_path: Path) -> None:
        name = name.strip()
        if not name:
            return
        path = Path(source_path)
        self._task_runner.run(self.ICON_CHANGE_TASK_ID, lambda: self._core.instances.set_icon(name, path), f"Changing icon for '{name}'...")

    def reset_icon(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run(self.ICON_RESET_TASK_ID, lambda: self._core.instances.reset_icon(name), f"Resetting icon for '{name}'...")

    def export_package(self, name: str, output_path: Path, include_saves: bool) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run("instance.export", lambda: self._core.instances.export_package(name, output_path, include_saves, self._on_package_progress), f"Exporting '{name}'...")

    def _on_package_progress(self, event: object) -> None:
        self.package_progress.emit(event)
        stage = getattr(getattr(event, "stage", None), "value", "package")
        message = str(getattr(event, "message", "Processing package..."))
        self.log_created.emit(f"[{stage}] {message}")

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == self.IMPORT_INSPECT_TASK_ID:
            self.import_preview_ready.emit(result)
            self.status_changed.emit(f"Ready to import '{result.name}'")
            self.log_created.emit(f"Instance package inspected: {result.package_path}")
            return

        selected_name = self._selected_name
        if task_id == self.CREATE_TASK_ID:
            selected_name = result.name
            self.instance_created.emit(result)
            self.status_changed.emit(f"Created '{selected_name}'")
        elif task_id == "instance.rename":
            selected_name = result["target"]
            self.status_changed.emit(f"Renamed '{result['source']}' to '{selected_name}'")
        elif task_id == "instance.clone":
            selected_name = result.name
            self.status_changed.emit(f"Cloned instance as '{selected_name}'")
        elif task_id == "instance.delete":
            if not result["deleted"]:
                self._emit_error("Delete instance", "Instance was not found.")
                return
            selected_name = ""
            self.status_changed.emit(f"Deleted '{result['name']}'")
        elif task_id == self.IMPORT_TASK_ID:
            selected_name = result.name
            self.status_changed.emit(f"Imported '{selected_name}'")
        elif task_id == self.LOADER_CHANGE_TASK_ID:
            selected_name = result.name
            loader_name, loader_version = self._core.loaders.normalize(result.mod_loader)
            loader_text = loader_name if loader_name == "vanilla" else f"{loader_name} {loader_version}"
            self.status_changed.emit(f"Applied {loader_text} to '{selected_name}'")
        elif task_id == self.LOADER_REPAIR_TASK_ID:
            selected_name = result.name
            loader_name, _ = self._core.loaders.normalize(result.mod_loader)
            self.status_changed.emit(f"Repaired {loader_name.title()} for '{selected_name}'")
        elif task_id == self.FORGE_RESTORE_TASK_ID:
            selected_name = result.name
            loader_name, loader_version = self._core.loaders.normalize(result.mod_loader)
            loader_text = loader_name.title() if loader_name == LoaderService.VANILLA else f"{loader_name.title()} {loader_version}"
            self.status_changed.emit(f"Restored {loader_text} for '{selected_name}'")
        elif task_id == self.FORGE_DIAGNOSTICS_TASK_ID:
            self.forge_diagnostics_finished.emit(result)
            self.status_changed.emit("Mod-loader diagnostics export completed")
            self.log_created.emit(f"Mod-loader diagnostics exported to: {result}")
            return
        elif task_id == self.ICON_CHANGE_TASK_ID:
            selected_name = result.name
            self.status_changed.emit(f"Changed icon for '{selected_name}'")
        elif task_id == self.ICON_RESET_TASK_ID:
            selected_name = result.name
            self.status_changed.emit(f"Reset icon for '{selected_name}'")
        elif task_id == self.REPAIR_TASK_ID:
            selected_name = result.instance_name
            self.repair_finished.emit(result)
            self.status_changed.emit(f"Repaired instance '{selected_name}'")
        elif task_id == self.REPAIR_SCAN_TASK_ID:
            selected_name = result.instance_name
            self.repair_scan_finished.emit(result)
            self.status_changed.emit(f"Checked instance '{selected_name}'")
        elif task_id == self.REPAIR_EXECUTE_TASK_ID:
            selected_name = result.instance_name
            self.repair_execution_finished.emit(result)
            self.status_changed.emit(f"Repair completed for '{selected_name}'")
        elif task_id == "instance.export":
            self.export_finished.emit(result)
            self.status_changed.emit("Instance export completed")
            self.log_created.emit(f"Instance exported to: {result}")
            return
        else:
            return

        self.log_created.emit(self.status_changed_message(task_id, result))
        self.refresh(selected_name)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == "instance.delete" and isinstance(error, InstanceDeletionError):
            if error.scheduled:
                self.status_changed.emit(f"Deletion queued for '{error.instance_name}'")
            self._emit_error("Delete instance", error)
            return
        if task_id in {self.REPAIR_SCAN_TASK_ID, self.REPAIR_EXECUTE_TASK_ID}:
            self.repair_center_failed.emit(error)
            self.status_changed.emit("Repair Center task failed")
            self.log_created.emit(f"Repair Center failed: {error}")
            return
        if task_id.startswith("instance."):
            self._emit_error("Instance task", error)

    def _validated_name(self, name: str) -> str | None:
        name = name.strip()
        if not name:
            self._emit_error("Instance name", "Enter an instance name.")
            return None
        if name in {".", ".."} or not self.INSTANCE_NAME_PATTERN.fullmatch(name) or name.endswith((" ", ".")):
            self._emit_error("Instance name", "The instance name is not valid on Windows.")
            return None
        return name

    @staticmethod
    def status_changed_message(task_id: str, result: object) -> str:
        if task_id == "instance.rename":
            return f"Instance renamed: {result['source']} -> {result['target']}"
        if task_id == "instance.delete":
            return f"Instance deleted: {result['name']}"
        if hasattr(result, "name"):
            return f"Instance task completed: {result.name}"
        return f"Instance task completed: {task_id}"
