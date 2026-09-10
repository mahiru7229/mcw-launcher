# Apply MCW Launcher v1.5.1-beta.6

1. Extract `MCW-Launcher-v1.5.1-beta.6-changed-files.zip` over the repository root.
2. Review the changed updater / bridge files.
3. Run:

```bash
python -m tools.release_preflight
python -m pytest test/core/update test/tools/test_update_bridge.py -q
```

4. Commit and push the source.
5. Create/publish GitHub pre-release `v1.5.1-beta.6` so `.github/workflows/release.yml` builds the native Windows/Linux launcher and bundled updater.
6. Build Bridge v1.5.0 separately only if you want recovery assets attached to the release; keep `activate_release_override=false` unless emergency bridge mode is explicitly required.

The critical live test is Windows `v1.5.1-beta.5 -> v1.5.1-beta.6`. Inspect `logs/updater.log`. A successful transition should report either a native direct replacement or the Windows rename-away fallback, then start the new launcher without `WinError 5`.
