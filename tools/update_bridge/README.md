# MCW Update Bridge 1.6.0

`MCW Update Bridge 1.6.0` is the one-time recovery updater for MCW Launcher `1.5.0` installations whose legacy updater can fail while replacing the launcher executable. The default and workflow-pinned target is stable `v1.5.1`.

## Platform contract

| Platform | Installed launcher | Stable package | Bridge binary |
| --- | --- | --- | --- |
| Windows x64 | `MCW Launcher.exe` | `MCW-Launcher-v1.5.1-windows-x64.zip` | `MCW-Update-Bridge-v1.6.0-windows-x64.exe` |
| Linux x64 | `mcw-launcher` | `MCW-Launcher-v1.5.1-linux-x64.zip` | `MCW-Update-Bridge-v1.6.0-linux-x64` |

The Bridge downloads the matching stable package plus its `.sha256` sidecar, validates SHA-256 and schema-2 `mcw-update.json`, closes only launcher processes that match the exact selected installation path, keeps a rollback backup, installs the launcher first, then installs the remaining managed files.

On Windows, launcher replacement uses `ReplaceFileW` / `MoveFileExW` and a rename-away fallback for access, sharing, or lock errors. On Linux it restores executable bits for both the launcher and bundled updater.

## Stable release workflow

Run **Build MCW Update Bridge** after the `v1.5.1` GitHub Release exists:

- `release_tag`: `v1.5.1`
- `upload_to_release`: `true`
- `activate_release_override`: `false`

The workflow attaches:

```text
MCW-Update-Bridge-v1.6.0-windows-x64.exe
MCW-Update-Bridge-v1.6.0-windows-x64.exe.sha256
MCW-Update-Bridge-v1.6.0-linux-x64
MCW-Update-Bridge-v1.6.0-linux-x64.sha256
```

Do **not** enable `MCW-USE-BRIDGE` for the normal stable release. Launcher 1.5.0 predates automatic Bridge routing, so affected 1.5.0 users must run the Bridge manually once. Beta 3 and newer installations should use the normal bundled updater.

## Manual recovery

Windows: run `MCW-Update-Bridge-v1.6.0-windows-x64.exe`, select the folder containing `MCW Launcher.exe`, and allow the Bridge to close the launcher if needed.

Linux:

```bash
chmod +x MCW-Update-Bridge-v1.6.0-linux-x64
./MCW-Update-Bridge-v1.6.0-linux-x64
```

A persistent recovery log is written to `logs/update-bridge.log` and rollback backups are kept under `cache/update-bridge/`.
