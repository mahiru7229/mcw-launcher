from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from src.core.fs.paths import Paths
from src.core.instance.instance_deletion_manager import InstanceDeletionManager
from src.core.instance.instance_manager import InstanceManager
from src.core.instance.instance_operation_journal import InstanceOperationJournal, InstanceRecoveryRecord
from src.core.instance.instance_run_lock import InstanceRunLock


@dataclass(frozen=True, slots=True)
class StartupRecoveryReport:
    deleted_instances: tuple[str, ...]
    stale_locks: tuple[str, ...]
    operations: tuple[InstanceRecoveryRecord, ...]
    orphan_staging_paths: tuple[str, ...]

    @property
    def recovered_item_count(self) -> int:
        return len(self.deleted_instances) + len(self.stale_locks) + len(self.operations) + len(self.orphan_staging_paths)


class StartupRecoveryManager:
    @staticmethod
    def reconcile() -> StartupRecoveryReport:
        deleted_instances = tuple(InstanceDeletionManager.process_pending())
        stale_locks = InstanceRunLock.reconcile()
        operations = InstanceOperationJournal.recover_all()
        orphan_staging_paths = StartupRecoveryManager._remove_orphan_staging()
        InstanceManager.reconcile_registry()
        return StartupRecoveryReport(
            deleted_instances=deleted_instances,
            stale_locks=stale_locks,
            operations=operations,
            orphan_staging_paths=orphan_staging_paths,
        )

    @staticmethod
    def _remove_orphan_staging() -> tuple[str, ...]:
        root = Paths.instance_staging_root()
        removed: list[str] = []
        for path in list(root.iterdir()):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink(missing_ok=True)
                removed.append(path.name)
            except OSError:
                continue
        return tuple(sorted(removed, key=str.casefold))


startup_recovery_manager = StartupRecoveryManager()
