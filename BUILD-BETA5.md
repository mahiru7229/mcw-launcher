# MCW Launcher v1.5.1-beta.5 build/test notes

## Release tag

`v1.5.1-beta.5` (GitHub pre-release)

## Native release contract

Windows ZIP must contain:
- `MCW Launcher.exe`
- `updater/MCW Updater.exe`
- `mcw-update.json`
- `lang/`
- `themes/`

Linux ZIP must contain:
- `mcw-launcher`
- `updater/mcw-updater`
- `mcw-update.json`
- `lang/`
- `themes/`

`docs/` must not be packaged. The manifest keeps `cleanup_paths: ["docs"]`.

## Critical Windows smoke test

1. Install/run `v1.5.1-beta.4` in an isolated directory.
2. Publish Beta 5 with Windows/Linux ZIP + SHA-256 assets.
3. Accept the Beta 5 update from Beta 4.
4. Confirm `MCW Updater.exe` opens with the MCW logo before the old launcher closes.
5. Confirm `logs/updater.log` includes `Primary launcher process exited` and `Launcher installation is fully stopped and executable lock is released`.
6. Confirm no `WinError 5` occurs, Beta 5 starts, and `docs/` is absent.

## Bridge

Build Bridge v1.4.0 from `.github/workflows/update-bridge.yml` with target `v1.5.1-beta.5`. Keep `activate_release_override=false` unless the release is explicitly declared an emergency recovery release.
