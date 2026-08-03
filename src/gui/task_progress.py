from __future__ import annotations

from dataclasses import dataclass

from src.models.progress.progress_stage import ProgressStage


@dataclass(frozen=True, slots=True)
class TaskProgressProfile:
    stage: ProgressStage
    success_message: str
    success_detail: str
    failure_message: str


def task_progress_profile(task_id: str) -> TaskProgressProfile | None:
    task = str(task_id or "")

    exact = {
        "java.scan": TaskProgressProfile(ProgressStage.SELECTING_JAVA, "java.scan.completed", "java.scan.completed_detail", "java.scan.failed"),
        "mods.update.check": TaskProgressProfile(ProgressStage.CHECKING_MODS, "mods.update_check.completed", "mods.update_check.completed_detail", "mods.update_check.failed"),
        "mods.update.apply": TaskProgressProfile(ProgressStage.DOWNLOADING_MODS, "mods.update.completed", "mods.update.completed_detail", "mods.update.failed"),
        "modpack.scan": TaskProgressProfile(ProgressStage.CHECKING_MODPACK, "modpack.scan.completed", "modpack.scan.completed_detail", "modpack.scan.failed"),
        "modpack.update.check": TaskProgressProfile(ProgressStage.CHECKING_MODPACK, "modpack.update_check.completed", "modpack.update_check.completed_detail", "modpack.update_check.failed"),
        "modpack.update.preview": TaskProgressProfile(ProgressStage.CHECKING_MODPACK, "modpack.preview.completed", "modpack.preview.completed_detail", "modpack.preview.failed"),
        "modpack.update.apply": TaskProgressProfile(ProgressStage.DOWNLOADING_MODPACK, "modpack.update.completed", "modpack.update.completed_detail", "modpack.update.failed"),
        "modpack.repair": TaskProgressProfile(ProgressStage.CHECKING_MODPACK, "modpack.repair.completed", "modpack.repair.completed_detail", "modpack.repair.failed"),
        "backup.create": TaskProgressProfile(ProgressStage.EXPORTING_INSTANCE, "backup.create.completed", "backup.create.completed_detail", "backup.create.failed"),
        "backup.restore": TaskProgressProfile(ProgressStage.REPAIRING_INSTANCE, "backup.restore.completed", "backup.restore.completed_detail", "backup.restore.failed"),
        "instance.import": TaskProgressProfile(ProgressStage.IMPORTING_INSTANCE, "instance.import.completed", "instance.import.completed_detail", "instance.import.failed"),
        "modpack.import": TaskProgressProfile(ProgressStage.IMPORTING_INSTANCE, "modpack_package.import.completed", "modpack_package.import.completed_detail", "modpack_package.import.failed"),
        "instance.export": TaskProgressProfile(ProgressStage.EXPORTING_INSTANCE, "instance.export.completed", "instance.export.completed_detail", "instance.export.failed"),
        "instance.repair.full": TaskProgressProfile(ProgressStage.REPAIRING_INSTANCE, "instance.repair.completed", "instance.repair.completed_detail", "instance.repair.failed"),
        "instance.repair.scan": TaskProgressProfile(ProgressStage.SCANNING_REPAIR, "repair.center.scan_task_completed", "repair.center.scan_task_detail", "repair.center.scan_task_failed"),
        "instance.repair.execute": TaskProgressProfile(ProgressStage.APPLYING_REPAIR, "repair.center.repair_task_completed", "repair.center.repair_task_detail", "repair.center.repair_task_failed"),
        "lan.hosting.prepare": TaskProgressProfile(ProgressStage.PREPARING, "lan.prepare.completed", "lan.prepare.completed_detail", "lan.prepare.failed"),
        "update.prepare": TaskProgressProfile(ProgressStage.DOWNLOADING_UPDATE, "update.prepare.completed", "update.prepare.completed_detail", "update.prepare.failed"),
    }
    if task in exact:
        return exact[task]

    if task.startswith("java.install."):
        return TaskProgressProfile(ProgressStage.INSTALLING_JAVA, "java.install.completed", "java.install.completed_detail", "java.install.failed")
    if task.startswith("update.check."):
        return TaskProgressProfile(ProgressStage.PREPARING, "update.check.completed", "update.check.completed_detail", "update.check.failed")
    if task in {"instance.create", "instance.loader", "instance.loader.repair", "instance.loader.restore"}:
        return TaskProgressProfile(ProgressStage.INSTALLING_MOD_LOADER, "loader.progress.ready", "loader.progress.ready_detail", "loader.progress.failed")
    if task.startswith("modrinth.install.modpack") or task.startswith("curseforge.install.modpack") or task.startswith("ftb.install.modpack"):
        return TaskProgressProfile(ProgressStage.DOWNLOADING_MODPACK, "modpack.install.completed", "modpack.install.completed_detail", "modpack.install.failed")
    if task.startswith("modrinth.install.mod") or task.startswith("curseforge.install.mod"):
        return TaskProgressProfile(ProgressStage.DOWNLOADING_MODS, "mods.install.completed", "mods.install.completed_detail", "mods.install.failed")
    if task.startswith("content.install."):
        return TaskProgressProfile(ProgressStage.DOWNLOADING_CONTENT, "content.task.install.completed", "content.task.install.completed_detail", "content.task.install.failed")

    return None
