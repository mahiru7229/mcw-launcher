# Build / publish v1.5.1-beta.3

## Apply patch

Extract this archive over the repository root.

```bash
git add .
git commit -m "fix(updater): switch releases to bundled updater v2"
git push
```

## Publish Beta 3

Create/publish GitHub **pre-release** tag:

```text
v1.5.1-beta.3
```

The release workflow now builds two binaries per platform:

Windows:
```text
dist/MCW Launcher.exe
dist/MCW Updater.exe
```

Linux:
```text
dist/mcw-launcher
dist/mcw-updater
```

Then it creates:

```text
MCW-Launcher-v1.5.1-beta.3-windows-x64.zip
MCW-Launcher-v1.5.1-beta.3-windows-x64.zip.sha256
MCW-Launcher-v1.5.1-beta.3-linux-x64.zip
MCW-Launcher-v1.5.1-beta.3-linux-x64.zip.sha256
```

The Windows ZIP must contain `updater/MCW Updater.exe`; the Linux ZIP must contain `updater/mcw-updater`.

## Attach recovery bridge

After the Beta 3 ZIP assets have been uploaded, run:

```text
Actions -> Build MCW Update Bridge -> Run workflow
release_tag: v1.5.1-beta.3
upload_to_release: true
```

This produces and attaches:

```text
MCW-Update-Bridge-v1.1.0-windows-x64.exe
MCW-Update-Bridge-v1.1.0-windows-x64.exe.sha256
```

## Mandatory smoke tests

1. Installed v1.5.0 -> Bridge v1.1.0 -> Beta 3.
2. Confirm Beta 3 starts and user data is unchanged.
3. Publish a test/newer Beta using schema 2.
4. Beta 3 -> newer Beta via automatic updater.
5. Confirm the temporary updater is the binary copied from the incoming ZIP, not `MCW Launcher.exe`.
