from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from mcw_core.api.language.language_manager import tr

from mcw_core.api.modloader.fabric.fabric_meta_client import FabricMetaClient
from mcw_core.api.modloader.forge.forge_metadata_client import ForgeMetadataClient
from mcw_core.api.modloader.neoforge.neoforge_metadata_client import NeoForgeMetadataClient
from mcw_core.api.modloader.quilt.quilt_meta_client import QuiltMetaClient
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class ModLoaderController(BaseController):
    fabric_versions_changed = Signal(str, list)
    forge_versions_changed = Signal(str, list)
    neoforge_versions_changed = Signal(str, list)
    quilt_versions_changed = Signal(str, list)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def load_fabric_versions(self, game_version: str) -> None:
        self._load_versions("fabric", game_version, FabricMetaClient.list_loader_versions, "Fabric")

    def load_quilt_versions(self, game_version: str) -> None:
        self._load_versions("quilt", game_version, QuiltMetaClient.list_loader_versions, "Quilt")

    def load_forge_versions(self, game_version: str) -> None:
        self._load_versions("forge", game_version, ForgeMetadataClient.list_versions, "Forge")

    def load_neoforge_versions(self, game_version: str) -> None:
        self._load_versions("neoforge", game_version, NeoForgeMetadataClient.list_versions, "NeoForge")

    def _load_versions(self, loader: str, game_version: str, resolver, title: str) -> None:
        game_version = game_version.strip()
        if not game_version:
            return
        task_id = f"{loader}.versions:{game_version}"
        if self._task_runner.is_task_active(task_id):
            return
        self._task_runner.run(task_id, lambda: (game_version, resolver(game_version)), tr("task.mod_loader.load_versions", loader=title, version=game_version), blocking=False)

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        game_version, versions = result if isinstance(result, tuple) and len(result) == 2 else ("", ())
        if task_id.startswith("fabric.versions:"):
            self.fabric_versions_changed.emit(game_version, list(versions))
            title = "Fabric"
        elif task_id.startswith("quilt.versions:"):
            self.quilt_versions_changed.emit(game_version, list(versions))
            title = "Quilt"
        elif task_id.startswith("forge.versions:"):
            self.forge_versions_changed.emit(game_version, list(versions))
            title = "Forge"
        elif task_id.startswith("neoforge.versions:"):
            self.neoforge_versions_changed.emit(game_version, list(versions))
            title = "NeoForge"
        else:
            return
        self.log_created.emit(f"{title} versions loaded for Minecraft {game_version}: {len(versions)}")

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        game_version = task_id.partition(":")[2]
        if task_id.startswith("fabric.versions:"):
            self.fabric_versions_changed.emit(game_version, [])
            title = "Fabric Loader"
        elif task_id.startswith("quilt.versions:"):
            self.quilt_versions_changed.emit(game_version, [])
            title = "Quilt Loader"
        elif task_id.startswith("forge.versions:"):
            self.forge_versions_changed.emit(game_version, [])
            title = "Minecraft Forge"
        elif task_id.startswith("neoforge.versions:"):
            self.neoforge_versions_changed.emit(game_version, [])
            title = "NeoForge"
        else:
            return
        self._emit_error(title, error)
