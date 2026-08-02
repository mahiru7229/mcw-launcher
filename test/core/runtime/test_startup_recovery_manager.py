from types import SimpleNamespace

from src.core.runtime.startup_recovery_manager import StartupRecoveryManager


def test_startup_recovery_runs_all_reconcilers(monkeypatch) -> None:
    monkeypatch.setattr("src.core.runtime.startup_recovery_manager.InstanceDeletionManager.process_pending", lambda: ["Old"])
    monkeypatch.setattr("src.core.runtime.startup_recovery_manager.InstanceRunLock.reconcile", lambda: ("Stale",))
    monkeypatch.setattr("src.core.runtime.startup_recovery_manager.InstanceOperationJournal.recover_all", lambda: (SimpleNamespace(result="rolled-back"),))
    monkeypatch.setattr(StartupRecoveryManager, "_remove_orphan_staging", staticmethod(lambda: ("orphan",)))
    called = []
    monkeypatch.setattr("src.core.runtime.startup_recovery_manager.InstanceManager.reconcile_registry", lambda: called.append("registry"))

    report = StartupRecoveryManager.reconcile()

    assert report.deleted_instances == ("Old",)
    assert report.stale_locks == ("Stale",)
    assert report.orphan_staging_paths == ("orphan",)
    assert report.recovered_item_count == 4
    assert called == ["registry"]
