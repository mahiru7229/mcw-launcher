# MCW Update Bridge 1.7.1

`MCW Update Bridge` is the universal recovery and upgrade tool for MCW Launcher installations. It rescues legacy or broken installations (including 1.5.0 and 1.5.1) and updates them directly to the **latest stable release** (or any maintainer-specified release tag).

## Platform contract

| Platform | Installed launcher | Stable package | Bridge binary |
| --- | --- | --- | --- |
| Windows x64 | `MCW Launcher.exe` | `MCW-Launcher-v{version}-windows-x64.zip` | `MCW-Update-Bridge-v1.7.1-windows-x64.exe` |
| Linux x64 | `mcw-launcher` | `MCW-Launcher-v{version}-linux-x64.zip` | `MCW-Update-Bridge-v1.7.1-linux-x64` |

The Bridge queries the GitHub API to dynamically discover the latest stable release (with graceful fallback if assets are in the middle of being built), downloads the matching package plus its `.sha256` sidecar, validates SHA-256 and schema-2 `mcw-update.json`, closes only launcher processes that match the exact selected installation path, keeps a rollback backup, installs the launcher first, and then installs the remaining managed files.

On Windows, launcher replacement uses `ReplaceFileW` / `MoveFileExW` and a rename-away fallback for access, sharing, or lock errors. On Linux it restores executable bits for both the launcher and bundled updater.

## Stable release workflow

Run **Build MCW Update Bridge** via GitHub Actions:

- `release_tag`: `latest` (default, or specify e.g. `v1.7.1`)
- `upload_to_release`: `true`
- `activate_release_override`: `false`

The workflow attaches:

```text
MCW-Update-Bridge-v1.7.1-windows-x64.exe
MCW-Update-Bridge-v1.7.1-windows-x64.exe.sha256
MCW-Update-Bridge-v1.7.1-linux-x64
MCW-Update-Bridge-v1.7.1-linux-x64.sha256
```

Do **not** enable `MCW-USE-BRIDGE` for normal stable releases unless an emergency hotfix requires all launchers to bypass their local updater and route through the standalone bridge.

## Manual recovery

Windows: run `MCW-Update-Bridge-v1.7.1-windows-x64.exe`, select the folder containing `MCW Launcher.exe`, and click **Update to Latest Release** (or the detected release tag).

Linux:

```bash
chmod +x MCW-Update-Bridge-v1.7.1-linux-x64
./MCW-Update-Bridge-v1.7.1-linux-x64
```

A persistent recovery log is written to `logs/update-bridge.log` and rollback backups are kept under `cache/update-bridge/`.
