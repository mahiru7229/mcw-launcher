# MCW Launcher v0.9.0-beta.5

## Repair & Recovery Center

- Creates a full recovery point before repairing instance-scoped components.
- Automatically restores that recovery point when an instance repair step fails.
- Records the recovery-point path, rollback result, and rollback error in the repair report.
- Does not create large instance backups for repairs that only affect shared launcher caches.
- Skips non-repairable issues instead of running a component repair that cannot resolve them.
- Shows recovery and rollback status directly in Repair Center.

## Protected scope

Recovery points are used for mod-loader, managed-modpack, and instance-settings repairs. Minecraft client, library, asset, and Java repairs remain cache-only operations and continue to use checksum verification after repair.
