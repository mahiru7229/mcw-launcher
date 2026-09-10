# MCW Launcher update packages

From `v1.5.1-beta.3`, automatic updates use **Updater Architecture v2**. Every GitHub Release ZIP contains both the launcher binary and a dedicated updater binary built from that same target release.

## Package contract — schema 2

Windows:

```text
MCW-Launcher-v1.5.1-beta.3-windows-x64/
├── MCW Launcher.exe
├── mcw-update.json
├── updater/
│   └── MCW Updater.exe
├── lang/
├── themes/
├── docs/
├── README.md
└── LICENSE
```

Linux:

```text
MCW-Launcher-v1.5.1-beta.3-linux-x64/
├── mcw-launcher
├── mcw-update.json
├── updater/
│   └── mcw-updater
└── ...
```

Example manifest:

```json
{
  "schema_version": 2,
  "version": "1.5.1-beta.3",
  "platform": "windows-x64",
  "executable": "MCW Launcher.exe",
  "updater": "updater/MCW Updater.exe",
  "files": [
    "MCW Launcher.exe",
    "mcw-update.json",
    "updater/MCW Updater.exe"
  ]
}
```

The managed-file list also contains the release documentation, languages, themes, and other packaged files.

## Security / fail-closed behavior

Before installation, the launcher validates:

- release SHA-256 digest or `.sha256` sidecar;
- archive paths and duplicate paths;
- manifest schema, version and platform;
- launcher executable name;
- bundled updater path;
- every managed file exists;
- no undeclared files are present;
- Linux launcher and updater have executable mode.

A schema-2 package missing its bundled updater is rejected. The launcher does not fall back to copying itself as an updater.

## Handoff model

The updater is taken from the **incoming** ZIP:

```text
current launcher
  ↓ download + validate new ZIP
incoming updater/MCW Updater.exe
  ↓ copy to %TEMP%/mcw-launcher-updater-...
launch incoming updater
  ↓
current launcher exits
  ↓
incoming updater applies target release
```

This ensures a fix to updater code becomes active during the transition *into* the release containing the fix.

## Build package manually

Windows example:

```powershell
python -m PyInstaller --clean --noconfirm mcw_launcher.spec
python -m PyInstaller --clean --noconfirm mcw_updater.spec
python -m tools.build_release_zip `
  --exe ".\dist\MCW Launcher.exe" `
  --updater ".\dist\MCW Updater.exe" `
  --version "1.5.1-beta.3" `
  --platform windows-x64
```

Linux example:

```bash
python -m PyInstaller --clean --noconfirm mcw_launcher.spec
python -m PyInstaller --clean --noconfirm mcw_updater.spec
python -m tools.build_release_zip \
  --exe ./dist/mcw-launcher \
  --updater ./dist/mcw-updater \
  --version 1.5.1-beta.3 \
  --platform linux-x64
```

## Windows v1.5.0 bridge

`v1.5.0` predates this architecture and contains the updater bootstrap bug. Existing affected Windows/Linux installs should use `MCW Update Bridge v1.2.0` once to migrate directly to Beta 3. The Bridge verifies the Beta 3 schema-2 package and installs it without depending on v1.5.0 updater code.

## Required live tests

1. `v1.5.0 → Bridge v1.2.0 → v1.5.1-beta.3`.
2. `v1.5.1-beta.3 → v1.5.1-beta.4` using automatic update.
3. Confirm updater log identifies the target release and completes rollback safely on a forced failure.
4. Confirm `config`, `instances`, accounts and saves remain unchanged.
