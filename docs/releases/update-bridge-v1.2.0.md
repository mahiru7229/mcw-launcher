# MCW Update Bridge v1.2.0

## Purpose

Bridge v1.2.0 expands the one-time 1.5.0 recovery path to **Windows x64 and Linux x64** while remaining pinned to `v1.5.1-beta.3`.

## Added in v1.2.0

- Linux x64 release-package selection and SHA-256 verification.
- Linux schema-2 package validation for `mcw-launcher` and `updater/mcw-updater`.
- Exact Linux process matching through `/proc/<pid>/exe`.
- Graceful `SIGTERM` followed by optional `SIGKILL` when force-close is allowed.
- Restoration of executable permission for the Linux launcher and bundled updater after ZIP extraction/install.
- GitHub Actions matrix build that publishes both Windows and Linux bridge binaries plus checksum sidecars.
- Cross-platform bridge regression tests.

## Linux usage

```bash
chmod +x MCW-Update-Bridge-v1.2.0-linux-x64
./MCW-Update-Bridge-v1.2.0-linux-x64
```

Or:

```bash
./MCW-Update-Bridge-v1.2.0-linux-x64 --cli --install-dir "$HOME/MCW-Launcher" --force-close
```
