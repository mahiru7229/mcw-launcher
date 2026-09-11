# MCW Update Bridge v1.6.0

MCW Update Bridge v1.6.0 is the stable recovery companion for MCW Launcher `v1.5.1`.

- Windows x64 and Linux x64 builds are produced from the same bridge source.
- Default and workflow-pinned target: `v1.5.1`.
- Downloads the platform release ZIP plus SHA-256 sidecar and validates schema 2 before installation.
- Closes only launcher processes matching the exact installation executable path.
- Windows launcher replacement uses native ReplaceFileW/MoveFileExW with rename-away fallback for access/sharing/lock errors.
- Maintains transactional backup/rollback and Linux executable permissions.
- `MCW-USE-BRIDGE` remains an explicit emergency option and should be false for normal v1.5.1 publication.
