# Windows 1.5.0 updater recovery bridge

## Incident

The updater shipped in MCW Launcher `1.5.0` can remain unable to replace `MCW Launcher.exe` on Windows (`WinError 5`). Because that updater bootstraps by copying the **currently installed launcher executable** into a temporary updater executable, fixes included only in a newer release do not run until the old updater has already succeeded.

This creates a bootstrap deadlock for affected `1.5.0` installations.

## Temporary recovery

`MCW Update Bridge 1.1.0` is a standalone Windows executable whose default target is `v1.5.1-beta.3`.

It performs a one-time migration without executing updater code from the installed 1.5.0 launcher:

1. Validate the selected installation and `MCW Launcher.exe`.
2. Close only the process whose full executable path matches that installation.
3. Read the official GitHub release metadata for `v1.5.1-beta.3`.
4. Download the exact `windows-x64.zip` and its `.sha256` sidecar.
5. Verify SHA-256 before extraction.
6. Reject unsafe ZIP paths and validate `mcw-update.json` (`schema_version=2`, target version, platform, executable, managed files).
7. Create a persistent rollback backup for files that will actually be changed.
8. Replace `MCW Launcher.exe` before any other package file, retrying an atomic replacement for up to 60 seconds.
9. Replace the remaining package-managed files.
10. Roll back only files that were already changed if any installation step fails.
11. Restart the updated launcher.

The bridge does not delete unrelated installation files and does not update user data from the release package.

## Beta 3 architecture boundary

The bridge is not the long-term updater.

Starting with `1.5.1-beta.3`, the release package should carry a dedicated updater executable built from the **new release**:

```text
MCW-Launcher-v1.5.1-beta.3-windows-x64/
├── MCW Launcher.exe
├── mcw-update.json
├── updater/
│   └── MCW Updater.exe
├── lang/
├── themes/
└── docs/
```

The installed launcher should prepare/download/extract the package, then copy or execute `updater/MCW Updater.exe` from that extracted **new package**. It must not copy the currently running `MCW Launcher.exe` and rename that copy as the updater.

This guarantees that updater fixes in release N are already active while installing release N, removing the bootstrap deadlock exposed by 1.5.0.
