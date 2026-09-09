# MCW Update Bridge

`MCW Update Bridge` is a one-time Windows recovery updater for MCW Launcher installations stuck on the updater shipped in `1.5.0`.

The bridge is intentionally a **separate executable**. It never copies or reuses the currently installed `MCW Launcher.exe` as its updater process.

## Recovery flow

```text
MCW Launcher 1.5.0
      │
      │ old self-updater cannot replace MCW Launcher.exe
      ▼
MCW-Update-Bridge.exe          (separate process)
      │
      ├─ close only the matching installed launcher process
      ├─ fetch v1.5.1-beta.3 release metadata from GitHub
      ├─ download windows-x64 ZIP + .sha256
      ├─ verify SHA-256
      ├─ validate mcw-update.json
      ├─ backup files that will actually be changed
      ├─ replace MCW Launcher.exe first
      ├─ replace the remaining managed package files
      ├─ rollback only changed files if installation fails
      └─ start the updated launcher
```

User data (`instances`, `accounts`, configuration, saves, caches unrelated to the update package) is not copied from the release ZIP and is not deleted by the bridge.

## Build the Windows executable

The repository includes `.github/workflows/update-bridge.yml`.

1. Push the bridge files to the repository.
2. Open **Actions → Build MCW Update Bridge → Run workflow**.
3. Leave the target release as `v1.5.1-beta.3`.
4. Enable **Upload bridge to target release** if that release is mutable.
5. GitHub Actions builds:

```text
MCW-Update-Bridge-v1.1.0-windows-x64.exe
MCW-Update-Bridge-v1.1.0-windows-x64.exe.sha256
```

If the GitHub release is immutable, disable release upload and publish the Action artifact or attach it to a new recovery release instead.

## End-user instructions

1. Download `MCW-Update-Bridge-v1.1.0-windows-x64.exe` from the official MCW Launcher GitHub release.
2. Run it.
3. Select the folder containing `MCW Launcher.exe` if it is not detected automatically.
4. Click **Update to v1.5.1-beta.3**.
5. If the launcher is still open, allow the bridge to close it.

The bridge keeps a recovery backup under:

```text
<launcher>/cache/update-bridge/backup-YYYYMMDD-HHMMSS/
```

The persistent recovery log is:

```text
<launcher>/logs/update-bridge.log
```

## CLI mode

```powershell
.\MCW-Update-Bridge-v1.1.0-windows-x64.exe --cli --install-dir "D:\MINECRAFT\MCW-Launcher-v0.5.1-windows-x64"
```

To allow the bridge to close a matching launcher process automatically:

```powershell
.\MCW-Update-Bridge-v1.1.0-windows-x64.exe --cli --install-dir "D:\MINECRAFT\MCW-Launcher-v0.5.1-windows-x64" --force-close
```

## Relationship to Beta 3

This tool is only a migration bridge. `1.5.1-beta.3` should replace the 1.5.0-era bootstrap design:

```text
OLD:
installed MCW Launcher.exe
   └─ copied to temp and executed as updater

BETA 3:
new release ZIP
   └─ updater/MCW Updater.exe
          └─ copied/executed from the NEW package
```

After Beta 3 adopts that contract, the bridge should no longer be part of normal update flows.
