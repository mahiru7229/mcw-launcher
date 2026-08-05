from src.gui.task_progress import task_progress_profile
from src.models.progress.progress_stage import ProgressStage


def test_account_reprotect_has_terminal_progress_profile():
    profile = task_progress_profile("account.security.reprotect")

    assert profile is not None
    assert profile.stage is ProgressStage.PREPARING
    assert profile.success_message == "account.security.reprotect_completed"
    assert profile.success_detail == "account.security.reprotect_completed_detail"
    assert profile.failure_message == "account.security.reprotect_failed"
