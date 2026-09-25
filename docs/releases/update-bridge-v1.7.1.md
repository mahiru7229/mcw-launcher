# MCW Update Bridge v1.7.1

MCW Update Bridge v1.7.1 is the universal recovery and upgrade companion for MCW Launcher installations.

- **Dynamic Release Resolution**: Automatically queries the GitHub API (`/releases/latest`) to discover and target the newest stable release.
- **Smart Fallback**: If a new release tag was recently published and GitHub Actions has not finished uploading platform binaries, the bridge automatically falls back to the most recent stable release with verified assets.
- **Tag Override**: Still accepts explicit release tags (e.g. `--tag v1.5.1` or `--tag v1.7.0`) via CLI or parameters.
- **GUI Polish**: The Tkinter recovery window features background release discovery, dynamic button updates (`Update to v1.7.1`), and clear status feedback.
- **Transactional Recovery**: Downloads the platform release ZIP plus SHA-256 sidecar, validates schema-2 `mcw-update.json`, closes matching launcher processes, installs the launcher first with Windows rename-away fallback, and maintains a full rollback backup under `cache/update-bridge/`.
- **Workflow Flexibility**: GitHub Actions workflow `.github/workflows/update-bridge.yml` now defaults to `latest` and can build and attach bridge artifacts to any target release.
