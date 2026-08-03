from src.gui.task_progress import task_progress_profile
from src.models.progress.progress_stage import ProgressStage


def test_profiles_cover_requested_long_running_tasks() -> None:
    expected = {
        "java.scan": ProgressStage.SELECTING_JAVA,
        "mods.update.check": ProgressStage.CHECKING_MODS,
        "modpack.update.check": ProgressStage.CHECKING_MODPACK,
        "backup.create": ProgressStage.EXPORTING_INSTANCE,
        "instance.import": ProgressStage.IMPORTING_INSTANCE,
        "lan.hosting.prepare": ProgressStage.PREPARING,
        "update.prepare": ProgressStage.DOWNLOADING_UPDATE,
        "modrinth.install.modpack": ProgressStage.DOWNLOADING_MODPACK,
        "curseforge.install.mod": ProgressStage.DOWNLOADING_MODS,
        "content.install.modrinth": ProgressStage.DOWNLOADING_CONTENT,
    }

    assert {task_id: task_progress_profile(task_id).stage for task_id in expected} == expected


def test_profile_lookup_ignores_unrelated_background_searches() -> None:
    assert task_progress_profile("mod_catalog.search.fabric") is None
