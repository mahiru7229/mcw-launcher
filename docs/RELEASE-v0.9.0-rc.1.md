# MCW Launcher v0.9.0-rc.1

## Release candidate

This build freezes the v0.9.0 feature set for final Windows validation.
Only release-blocking fixes should be accepted before the stable release.

## Included hardening

- Recovers interrupted downloads through verified partial files and a durable download journal.
- Previews managed modpack changes before applying an update.
- Creates recovery points for instance-scoped repairs and rolls back failed repairs automatically.
- Exports bounded, privacy-filtered diagnostic ZIP bundles.
- Releases the blocking task state before completion callbacks so preview-to-update task chains are accepted.
- Falls back to a transactional copy when Windows blocks renaming a staged backup folder such as `.fabric`.

## Final EXE validation

- Start the packaged launcher without a console window or startup error.
- Sign in with both Offline and Microsoft accounts.
- Launch representative Vanilla, Fabric, and Forge instances.
- Pause, resume, and cancel an active download.
- Install and update a managed modpack, reviewing the update preview first.
- Run Repair Center and confirm recovery-point rollback behavior.
- Restore the latest full modpack backup, including a backup containing `.fabric`.
- Export a diagnostic bundle and confirm that it contains no account database, world, or mod JAR contents.
- Download an update and confirm that its progress is visible in the launch progress area.

## Release metadata

- Version: `v0.9.0 RC 1`
- Version ID: `0.9.0-rc.1`
- Tag: `v0.9.0-rc.1`
- Update channel: `beta`
