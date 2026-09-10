# MCW Launcher 1.5.0 recovery bridge

## Incident

The updater shipped in MCW Launcher `1.5.0` can enter a bootstrap deadlock on affected installations because the old updater path reuses updater code from the currently installed launcher. Fixes that exist only in a newer release are therefore not guaranteed to run before the old updater has already succeeded.

## Temporary recovery

`MCW Update Bridge 1.4.0` is a standalone recovery executable for **Windows x64 and Linux x64**. Its default target is `v1.5.1-beta.5`.

It performs a one-time migration without executing updater code from the installed 1.5.0 launcher:

1. Detect the current platform and validate the selected launcher installation.
2. Close only launcher processes whose executable path exactly matches that installation.
3. Read the official GitHub release metadata for `v1.5.1-beta.5`.
4. Download the exact matching platform ZIP and its `.sha256` sidecar.
5. Verify SHA-256 before extraction.
6. Reject unsafe ZIP paths and validate `mcw-update.json` schema 2, platform, executable, bundled updater and managed-file allow-list.
7. Create a persistent rollback backup only for files that will actually change.
8. Replace the launcher executable before all other package files.
9. Replace the remaining managed files and restore executable permission on Linux `mcw-launcher` and `updater/mcw-updater`.
10. Roll back only files that were already changed if installation fails.
11. Restart the updated launcher.

Windows process matching uses the exact executable path. Linux process matching uses `/proc/<pid>/exe`; graceful close sends `SIGTERM` first, and force-close uses `SIGKILL` only when explicitly allowed.

The bridge does not delete unrelated installation files or user data.

## Recovery artifacts

```text
MCW-Update-Bridge-v1.4.0-windows-x64.exe
MCW-Update-Bridge-v1.4.0-windows-x64.exe.sha256
MCW-Update-Bridge-v1.4.0-linux-x64
MCW-Update-Bridge-v1.4.0-linux-x64.sha256
```

## Beta 4 architecture boundary

The bridge is not the long-term updater. Starting with `1.5.1-beta.3`, each release package carries its own dedicated updater built from the **new release**:

```text
Windows: updater/MCW Updater.exe
Linux:   updater/mcw-updater
```

The installed launcher downloads/extracts the new package and executes the bundled updater from that package. It must never copy the currently running launcher executable and rename that copy as the updater.
