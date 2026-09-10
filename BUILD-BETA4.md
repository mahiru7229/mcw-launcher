# MCW Launcher v1.5.1-beta.4 build/test notes

## What Beta 4 changes

- Dedicated updater from the incoming release remains mandatory (`updater/MCW Updater.exe` / `updater/mcw-updater`).
- Windows updater has its own lightweight Tk GUI.
- Launcher waits for the incoming updater READY handshake before closing.
- If the incoming updater cannot initialize, the installed updater is copied to temp and used as a fallback.
- Release ZIPs no longer ship `docs/`.
- `mcw-update.json` includes `cleanup_paths: ["docs"]`; updater and Bridge remove an old installed `docs/` tree if it exists and silently skip it if absent.
- MCW Update Bridge is v1.3.0 and targets Beta 4.
- A release uses the Bridge automatically only when the maintainer also attaches the exact marker asset `MCW-USE-BRIDGE`.
- Launcher-managed Modrinth `required_dependency` files are re-downloaded when stale instead of being preserved as user-modified files.

## Local checks

```bash
python -m tools.release_preflight
python -m pytest test/core/update test/core/modrinth test/core/mod test/core/package test/tools/test_build_release_zip.py test/tools/test_pyinstaller_spec.py test/tools/test_release_preflight.py test/tools/test_release_workflow.py test/tools/test_update_bridge.py -q
```

Expected baseline for this patch: `331 passed`, with two intentional duplicate-ZIP warnings from package security tests.

## Release

Commit the patch, create/publish pre-release tag `v1.5.1-beta.4`, and let `.github/workflows/release.yml` build both launcher and updater binaries before packaging.

Normal Beta 4 release assets should include the Windows/Linux launcher ZIPs plus SHA-256 sidecars. Bridge assets may also be attached as recovery tools without changing normal update behavior.

To explicitly force an emergency Bridge update, run the `Build MCW Update Bridge` workflow with:

- `release_tag`: `v1.5.1-beta.4`
- `upload_to_release`: `true`
- `activate_release_override`: `true`

That last option uploads `MCW-USE-BRIDGE`. Do not enable it for a healthy release.
