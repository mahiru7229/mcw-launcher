from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr

from mcw_core import InstanceCreateRequest, InstanceDeletionError, LoaderService, get_default_core
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskConflictPolicy, TaskRunner
from src.config import VERSION_ID


class InstanceController(BaseController):
    instances_changed = Signal(list, str)
    running_instances_changed = Signal(list)
    health_reports_changed = Signal(list)
    selected_instance_changed = Signal(object)
    runtime_profile_changed = Signal(object)
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
    modpack_import_preview_ready = Signal(object)
    modpack_export_finished = Signal(object)
    portable_manual_files_installed = Signal(object)
    instance_killed = Signal(str)

    CREATE_TASK_ID = "instance.create"
    IMPORT_INSPECT_TASK_ID = "instance.import.inspect"
    IMPORT_TASK_ID = "instance.import"
    MODPACK_IMPORT_INSPECT_TASK_ID = "modpack.import.inspect"
    MODPACK_IMPORT_TASK_ID = "modpack.import"
    MODPACK_EXPORT_TASK_ID = "modpack.export"
    PORTABLE_MANUAL_TASK_ID = "modpack.manual.install"
    REPAIR_TASK_ID = "instance.repair.full"
    REPAIR_SCAN_TASK_ID = "instance.repair.scan"
    REPAIR_EXECUTE_TASK_ID = "instance.repair.execute"
    LOADER_CHANGE_TASK_ID = "instance.loader"
    LOADER_REPAIR_TASK_ID = "instance.loader.repair"
    FORGE_RESTORE_TASK_ID = "instance.loader.restore"
    FORGE_DIAGNOSTICS_TASK_ID = "instance.forge.diagnostics"
    ICON_CHANGE_TASK_ID = "instance.icon.change"
    ICON_RESET_TASK_ID = "instance.icon.reset"
    RUNTIME_PROFILE_TASK_PREFIX = "instance.runtime.profile."
    JAVA_RUNTIME_TASK_ID = "instance.java.runtime"
    KILL_TASK_PREFIX = "instance.kill."
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
            self.runtime_profile_changed.emit(None)
            return
        try:
            instance = self._core.instances.load(self._selected_name)
        except Exception as error:
            self._emit_error("Load instance", error)
            return
        self.selected_instance_changed.emit(instance)
        task_id = f"{self.RUNTIME_PROFILE_TASK_PREFIX}{instance.name}"
        self._task_runner.run(
            task_id,
            lambda name=instance.name: self._core.instances.runtime_profile(name),
            tr("workspace.editor.runtime.loading", name=instance.name),
            blocking=False,
        )

    def set_favorite(self, name: str, favorite: bool) -> None:
        self._update_library_metadata(name, favorite=bool(favorite))

    def set_group(self, name: str, group: str) -> None:
        self._update_library_metadata(name, group=str(group or "").strip())

    def set_tags(self, name: str, tags: object) -> None:
        self._update_library_metadata(name, tags=tags)

    def set_java_runtime(self, name: str, java_path: str) -> None:
        normalized = str(name or "").strip()
        if not normalized:
            return
        self._task_runner.run(
            self.JAVA_RUNTIME_TASK_ID,
            lambda: self._core.instances.set_java_runtime(normalized, java_path),
            tr("task.instance.java_runtime", name=normalized),
        )

    def _update_library_metadata(self, name: str, **changes: object) -> None:
        normalized = str(name or "").strip()
        if not normalized:
            return
        try:
            instance = self._core.instances.set_library_metadata(normalized, **changes)
        except Exception as error:
            self._emit_error("Update instance library", error)
            return
        self.refresh(selected_name=instance.name)

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

        return self._task_runner.run(self.CREATE_TASK_ID, task, tr("task.instance.create", name=name))

    def create_with_optifine(self, name: str, version_id: str, loader_name: str, loader_version: str, source_path: object) -> bool:
        name = self._validated_name(name)
        version_id = str(version_id or "").strip()
        loader_name, loader_version = self._core.loaders.normalize((loader_name, loader_version))
        if name is None or not version_id:
            if not version_id:
                self._emit_error("Create instance", "Select a Minecraft version first.")
            return False

        def task() -> Any:
            return self._core.instances.create_with_optifine(
                InstanceCreateRequest(
                    name=name,
                    version_id=version_id,
                    loader_name=loader_name,
                    loader_version=loader_version,
                    on_progress=self._on_loader_progress,
                ),
                Path(source_path),
                "auto",
                self._on_loader_progress,
            )

        return self._task_runner.run(self.CREATE_TASK_ID, task, tr("task.instance.create_optifine", name=name))

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

        self._task_runner.run(self.LOADER_CHANGE_TASK_ID, task, tr("task.instance.apply_loader", loader=loader_name.title(), name=name))

    def repair_loader(self, name: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.repair_loader(name, self._on_loader_progress)

        self._task_runner.run(self.LOADER_REPAIR_TASK_ID, task, tr("task.instance.repair_loader", name=name))

    def restore_previous_forge(self, name: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.restore_previous_loader(name, self._on_loader_progress)

        self._task_runner.run(self.FORGE_RESTORE_TASK_ID, task, tr("task.instance.restore_loader", name=name))

    def export_forge_diagnostics(self, name: str, output_path: Path) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Path:
            return self._core.instances.export_loader_diagnostics(name, output_path)

        self._task_runner.run(self.FORGE_DIAGNOSTICS_TASK_ID, task, tr("task.instance.export_loader_diagnostics", name=name), blocking=False)


    def repair_instance(self, name: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.repair(name, self._on_repair_progress)

        self._task_runner.run(self.REPAIR_TASK_ID, task, tr("task.instance.repair", name=name))

    def scan_repair_center(self, name: str, mode: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.scan_repair(name, mode, self._on_repair_progress)

        self._task_runner.run(self.REPAIR_SCAN_TASK_ID, task, tr("task.instance.check", name=name))

    def execute_repair_plan(self, name: str, plan: object) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            return self._core.instances.execute_repair(name, plan, self._on_repair_progress)

        self._task_runner.run(self.REPAIR_EXECUTE_TASK_ID, task, tr("task.instance.repair_components", name=name))

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

        self._task_runner.run("instance.rename", task, tr("task.instance.rename", name=source_name))

    def clone(self, source_name: str, target_name: str, include_saves: bool) -> None:
        source_name = source_name.strip()
        target_name = self._validated_name(target_name)
        if not source_name or target_name is None:
            return

        def task() -> Any:
            return self._core.instances.clone(source_name, target_name, include_saves)

        self._task_runner.run("instance.clone", task, tr("task.instance.clone", name=source_name))

    def delete(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run("instance.delete", lambda: {"name": name, "deleted": self._core.instances.delete(name)}, tr("task.instance.delete", name=name))

    def inspect_package(self, package_path: Path) -> None:
        package_path = Path(package_path)

        def task() -> tuple[str, object]:
            modpack_error: Exception | None = None
            try:
                return "modpack", self._core.instances.inspect_modpack_package(package_path)
            except Exception as error:
                modpack_error = error
            try:
                return "instance", self._core.instances.inspect_package(package_path)
            except Exception as instance_error:
                modpack_message = str(modpack_error or "").strip()
                instance_message = str(instance_error).strip()
                if "missing package.json" in instance_message.casefold() and modpack_message:
                    raise RuntimeError(modpack_message) from instance_error
                raise

        self._task_runner.run(
            self.IMPORT_INSPECT_TASK_ID,
            task,
            tr("task.instance.read_package", file=package_path.name),
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
            tr("task.instance.import_package", file=package_path.name),
        )

    def inspect_modpack_package(self, package_path: Path) -> None:
        path = Path(package_path)
        self._task_runner.run(
            self.MODPACK_IMPORT_INSPECT_TASK_ID,
            lambda: self._core.instances.inspect_modpack_package(path),
            tr("task.instance.read_modpack_package", file=path.name),
        )

    def import_modpack_package(self, package_path: Path, settings_override: dict | None = None, install_optional_files: bool = True, instance_name: str = "") -> None:
        path = Path(package_path)
        normalized_override = copy.deepcopy(settings_override)
        self._task_runner.run(
            self.MODPACK_IMPORT_TASK_ID,
            lambda: self._core.instances.import_modpack_package(
                path,
                self._on_package_progress,
                settings_override=normalized_override,
                install_optional_files=install_optional_files,
                instance_name=instance_name,
            ),
            tr("task.instance.import_modpack_package", file=path.name),
        )

    def export_modpack(self, name: str, output_path: Path, mode: str, portable_mode: str = "smart", include_saves: bool = False) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run(
            self.MODPACK_EXPORT_TASK_ID,
            lambda: self._core.instances.export_modpack(name, output_path, mode, portable_mode, include_saves, self._on_package_progress),
            tr("task.instance.export_modpack_profile", name=name),
        )

    def install_portable_manual_files(self, name: str, requirements: object, sources: object) -> None:
        normalized_name = str(name or "").strip()
        if not normalized_name:
            return
        requirement_values = tuple(requirements or ())
        source_values = tuple(Path(source) for source in (sources or ()))
        self._task_runner.run(
            self.PORTABLE_MANUAL_TASK_ID,
            lambda: self._core.instances.install_portable_manual_files(normalized_name, requirement_values, source_values),
            tr("task.instance.import_manual_modpack_files", name=normalized_name),
        )

    def change_icon(self, name: str, source_path: Path) -> None:
        name = name.strip()
        if not name:
            return
        path = Path(source_path)
        self._task_runner.run(self.ICON_CHANGE_TASK_ID, lambda: self._core.instances.set_icon(name, path), tr("task.instance.change_icon", name=name))

    def reset_icon(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run(self.ICON_RESET_TASK_ID, lambda: self._core.instances.reset_icon(name), tr("task.instance.reset_icon", name=name))

    def export_package(self, name: str, output_path: Path, include_saves: bool) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run("instance.export", lambda: self._core.instances.export_package(name, output_path, include_saves, self._on_package_progress), tr("task.instance.export", name=name))

    def kill_instance(self, name: str) -> None:
        instance_name = str(name or "").strip()
        if not instance_name:
            return
        task_id = f"{self.KILL_TASK_PREFIX}{instance_name}"
        self._task_runner.run(
            task_id,
            lambda: (instance_name, self._core.instances.kill(instance_name)),
            tr("status.instance.killing", name=instance_name),
            blocking=False,
            group=task_id,
            conflict_policy=TaskConflictPolicy.REPLACE,
        )

    def _on_package_progress(self, event: object) -> None:
        self.package_progress.emit(event)
        stage = getattr(getattr(event, "stage", None), "value", "package")
        message = str(getattr(event, "message", "Processing package..."))
        self.log_created.emit(f"[{stage}] {message}")

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == self.IMPORT_INSPECT_TASK_ID:
            package_kind, preview = result
            if package_kind == "modpack":
                self.modpack_import_preview_ready.emit(preview)
                self.status_changed.emit(tr("status.instance.ready_import_modpack", name=preview.name))
                self.log_created.emit(f"Provider modpack package inspected: {preview.package_path}")
            else:
                self.import_preview_ready.emit(preview)
                self.status_changed.emit(tr("status.instance.ready_import_package", name=preview.name))
                self.log_created.emit(f"Instance package inspected: {preview.package_path}")
            return

        if task_id == self.MODPACK_IMPORT_INSPECT_TASK_ID:
            self.modpack_import_preview_ready.emit(result)
            self.status_changed.emit(tr("status.instance.ready_import_modpack", name=result.name))
            self.log_created.emit(f"Provider modpack package inspected: {result.package_path}")
            return

        if task_id.startswith(self.KILL_TASK_PREFIX):
            instance_name, killed = result
            if not killed:
                self._emit_error(tr("workspace.kill.title"), tr("workspace.kill.not_running", name=instance_name))
                return
            self.instance_killed.emit(instance_name)
            self.status_changed.emit(tr("status.instance.killed", name=instance_name))
            self.log_created.emit(f"Instance killed by user: {instance_name}")
            self.refresh_running(force=True)
            return

        if task_id.startswith(self.RUNTIME_PROFILE_TASK_PREFIX):
            if str(getattr(result, "instance_name", "")) == self._selected_name:
                self.runtime_profile_changed.emit(result)
            return

        selected_name = self._selected_name
        if task_id == self.JAVA_RUNTIME_TASK_ID:
            selected_name = str(getattr(result, "instance_name", "") or selected_name)
            self.runtime_profile_changed.emit(result)
            self.status_changed.emit(tr("status.instance.java_runtime_applied", name=selected_name))
        elif task_id == self.CREATE_TASK_ID:
            selected_name = result.name
            self.instance_created.emit(result)
            self.status_changed.emit(tr("status.instance.created", name=selected_name))
        elif task_id == "instance.rename":
            selected_name = result["target"]
            self.status_changed.emit(tr("status.instance.renamed", source=result["source"], name=selected_name))
        elif task_id == "instance.clone":
            selected_name = result.name
            self.status_changed.emit(tr("status.instance.cloned", name=selected_name))
        elif task_id == "instance.delete":
            if not result["deleted"]:
                self._emit_error("Delete instance", "Instance was not found.")
                return
            selected_name = ""
            self.status_changed.emit(tr("status.instance.deleted", name=result["name"]))
        elif task_id == self.IMPORT_TASK_ID:
            selected_name = result.name
            self.status_changed.emit(tr("status.instance.imported", name=selected_name))
        elif task_id == self.MODPACK_IMPORT_TASK_ID:
            selected_name = result.name
            self.status_changed.emit(tr("status.instance.modpack_imported", name=selected_name))
        elif task_id == self.MODPACK_EXPORT_TASK_ID:
            self.modpack_export_finished.emit(result)
            self.status_changed.emit(tr("status.instance.modpack_exported", path=result.output_path))
            return
        elif task_id == self.PORTABLE_MANUAL_TASK_ID:
            self.portable_manual_files_installed.emit(result)
            self.status_changed.emit(tr("status.instance.manual_files_imported", count=len(result.get("installed", ())) or 0))
            return
        elif task_id == self.LOADER_CHANGE_TASK_ID:
            selected_name = result.name
            loader_name, loader_version = self._core.loaders.normalize(result.mod_loader)
            loader_text = loader_name if loader_name == "vanilla" else f"{loader_name} {loader_version}"
            self.status_changed.emit(tr("status.instance.loader_applied", loader=loader_text, name=selected_name))
        elif task_id == self.LOADER_REPAIR_TASK_ID:
            selected_name = result.name
            loader_name, _ = self._core.loaders.normalize(result.mod_loader)
            self.status_changed.emit(tr("status.instance.loader_repaired", loader=loader_name.title(), name=selected_name))
        elif task_id == self.FORGE_RESTORE_TASK_ID:
            selected_name = result.name
            loader_name, loader_version = self._core.loaders.normalize(result.mod_loader)
            loader_text = loader_name.title() if loader_name == LoaderService.VANILLA else f"{loader_name.title()} {loader_version}"
            self.status_changed.emit(tr("status.instance.loader_restored", loader=loader_text, name=selected_name))
        elif task_id == self.FORGE_DIAGNOSTICS_TASK_ID:
            self.forge_diagnostics_finished.emit(result)
            self.status_changed.emit(tr("status.instance.loader_diagnostics_completed"))
            self.log_created.emit(f"Mod-loader diagnostics exported to: {result}")
            return
        elif task_id == self.ICON_CHANGE_TASK_ID:
            selected_name = result.name
            self.status_changed.emit(tr("status.instance.icon_changed", name=selected_name))
        elif task_id == self.ICON_RESET_TASK_ID:
            selected_name = result.name
            self.status_changed.emit(tr("status.instance.icon_reset", name=selected_name))
        elif task_id == self.REPAIR_TASK_ID:
            selected_name = result.instance_name
            self.repair_finished.emit(result)
            self.status_changed.emit(tr("status.instance.repaired", name=selected_name))
        elif task_id == self.REPAIR_SCAN_TASK_ID:
            selected_name = result.instance_name
            self.repair_scan_finished.emit(result)
            self.status_changed.emit(tr("status.instance.checked", name=selected_name))
        elif task_id == self.REPAIR_EXECUTE_TASK_ID:
            selected_name = result.instance_name
            self.repair_execution_finished.emit(result)
            self.status_changed.emit(tr("status.instance.repair_completed", name=selected_name))
        elif task_id == "instance.export":
            self.export_finished.emit(result)
            self.status_changed.emit(tr("instance.export.completed"))
            self.log_created.emit(f"Instance exported to: {result}")
            return
        else:
            return

        self.log_created.emit(self.status_changed_message(task_id, result))
        self.refresh(selected_name)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id.startswith(self.KILL_TASK_PREFIX):
            instance_name, killed = result
            if not killed:
                self._emit_error(tr("workspace.kill.title"), tr("workspace.kill.not_running", name=instance_name))
                return
            self.instance_killed.emit(instance_name)
            self.status_changed.emit(tr("status.instance.killed", name=instance_name))
            self.log_created.emit(f"Instance killed by user: {instance_name}")
            self.refresh_running(force=True)
            return

        if task_id.startswith(self.RUNTIME_PROFILE_TASK_PREFIX):
            self.log_created.emit(f"Instance runtime profile unavailable: {type(error).__name__}: {error}")
            if task_id == f"{self.RUNTIME_PROFILE_TASK_PREFIX}{self._selected_name}":
                self.runtime_profile_changed.emit(None)
            return
        if task_id == "instance.delete" and isinstance(error, InstanceDeletionError):
            if error.scheduled:
                self.status_changed.emit(tr("status.instance.deletion_queued", name=error.instance_name))
            self._emit_error("Delete instance", error)
            return
        if task_id in {self.REPAIR_SCAN_TASK_ID, self.REPAIR_EXECUTE_TASK_ID}:
            self.repair_center_failed.emit(error)
            self.status_changed.emit(tr("status.instance.repair_center_failed"))
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
