# MCW Update Bridge

`MCW Update Bridge 1.5.0` is a one-time cross-platform recovery updater for MCW Launcher `1.5.0` installations that need to migrate to the schema-2 updater architecture in `v1.5.1-beta.6`.

The bridge is a **separate executable**. It never copies or reuses the currently installed launcher executable as its updater process.

## Supported recovery targets

| Platform | Installed launcher | Release package | Bridge artifact |
| --- | --- | --- | --- |
| Windows x64 | `MCW Launcher.exe` | `MCW-Launcher-v1.5.1-beta.6-windows-x64.zip` | `MCW-Update-Bridge-v1.5.0-windows-x64.exe` |
| Linux x64 | `mcw-launcher` | `MCW-Launcher-v1.5.1-beta.6-linux-x64.zip` | `MCW-Update-Bridge-v1.5.0-linux-x64` |

Both paths require the matching `.sha256` release asset and a valid schema-2 `mcw-update.json`.

## Recovery flow

```text
MCW Launcher 1.5.0
      │
      ▼
MCW Update Bridge 1.5.0       (separate process)
      │
      ├─ identify the current platform
      ├─ close only launcher processes whose executable path matches this installation
      ├─ fetch v1.5.1-beta.6 metadata from GitHub
      ├─ download the matching platform ZIP + .sha256
      ├─ verify SHA-256
      ├─ validate mcw-update.json schema 2 and managed-file allow-list
      ├─ backup only files that will be changed
      ├─ replace the launcher executable first
      ├─ replace the remaining managed files
      ├─ restore +x on Linux mcw-launcher and updater/mcw-updater
      ├─ rollback only changed files if installation fails
      └─ start the updated launcher
```

User data (`instances`, accounts, saves and configuration outside package-managed files) is not deleted by the bridge.

## Build both recovery binaries

Use `.github/workflows/update-bridge.yml`:

1. Push the Bridge 1.5.0 files.
2. Open **Actions → Build MCW Update Bridge → Run workflow**.
3. Leave `release_tag` as `v1.5.1-beta.6`.
4. Enable `upload_to_release` if the release can still accept assets.

GitHub Actions builds:

```text
MCW-Update-Bridge-v1.5.0-windows-x64.exe
MCW-Update-Bridge-v1.5.0-windows-x64.exe.sha256
MCW-Update-Bridge-v1.5.0-linux-x64
MCW-Update-Bridge-v1.5.0-linux-x64.sha256
```

The Linux build is intentionally a small console recovery binary and excludes Tk.

## Linux usage

Make it executable, then run it:

```bash
chmod +x MCW-Update-Bridge-v1.5.0-linux-x64
./MCW-Update-Bridge-v1.5.0-linux-x64
```

The terminal flow asks for the launcher folder. Or use explicit CLI mode:

```bash
./MCW-Update-Bridge-v1.5.0-linux-x64 \
  --cli \
  --install-dir "$HOME/MCW-Launcher"
```

If the matching `mcw-launcher` process is still running:

```bash
./MCW-Update-Bridge-v1.5.0-linux-x64 \
  --cli \
  --install-dir "$HOME/MCW-Launcher" \
  --force-close
```

On Linux the bridge identifies the exact installation using `/proc/<pid>/exe`, sends `SIGTERM` first, waits, then uses `SIGKILL` only when `--force-close` permits it and the launcher did not exit.

## Windows usage

Run `MCW-Update-Bridge-v1.5.0-windows-x64.exe`, select the folder containing `MCW Launcher.exe`, and update to `v1.5.1-beta.6`.

## Recovery data

Backup:

```text
<launcher>/cache/update-bridge/backup-YYYYMMDD-HHMMSS/
```

Log:

```text
<launcher>/logs/update-bridge.log
```

## Relationship to Beta 4

The bridge remains a migration/recovery tool only. Normal updates from Beta 4 onward use the updater bundled inside the **new** release ZIP:

```text
Windows: updater/MCW Updater.exe
Linux:   updater/mcw-updater
```

The installed old launcher executable is never renamed and reused as the updater in the new architecture.
