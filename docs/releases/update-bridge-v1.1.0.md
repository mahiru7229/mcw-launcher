# MCW Update Bridge v1.1.0

> Windows recovery tool for MCW Launcher 1.5.0 installations that cannot complete self-update.

Some Windows installations running MCW Launcher `1.5.0` can fail while replacing `MCW Launcher.exe` and then fail the rollback for the same locked executable. Because the 1.5.0 updater launches a temporary copy of the **old installed launcher executable**, updater fixes contained only in a newer launcher release cannot participate until the old updater has already completed.

`MCW Update Bridge v1.1.0` breaks that bootstrap loop with a separate recovery executable.

## Who needs it?

Use the bridge only if MCW Launcher 1.5.0 cannot update normally and `logs/updater.log` contains a Windows `Access is denied` / `WinError 5` error while replacing `MCW Launcher.exe`.

## What it does

- Targets `v1.5.1-beta.3`.
- Downloads the official `windows-x64` release ZIP and `.sha256` sidecar.
- Verifies SHA-256 before installation.
- Validates `mcw-update.json` and rejects unsafe/unlisted archive content.
- Closes only launcher processes whose full executable path belongs to the selected installation.
- Creates a persistent rollback backup.
- Replaces `MCW Launcher.exe` first, outside the old 1.5.0 updater process.
- Replaces the remaining managed release files only after the executable succeeds.
- Rolls back only files that were actually changed if installation fails.
- Restarts the updated launcher.

The bridge does not delete unrelated files and does not replace Minecraft instances, saves, accounts, or launcher configuration with release content.

## User steps

1. Close MCW Launcher if possible.
2. Download `MCW-Update-Bridge-v1.1.0-windows-x64.exe` from the official repository/release.
3. Run the bridge.
4. Select the folder containing `MCW Launcher.exe` if it is not detected.
5. Click **Update to v1.5.1-beta.3**.
6. Allow the bridge to close the launcher if prompted.

A recovery log is written to `logs/update-bridge.log`.

## Temporary migration only

This bridge is not the future normal updater. The planned `1.5.1-beta.3` package should ship a dedicated `updater/MCW Updater.exe`, and the installed launcher should execute the updater from the **newly downloaded package**, not a renamed copy of the currently installed launcher.
