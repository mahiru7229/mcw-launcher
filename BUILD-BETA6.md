# MCW Launcher v1.5.1-beta.6 build/test notes

Target GitHub pre-release: `v1.5.1-beta.6`.

Beta 6 keeps updater schema 2 and the bundled updater layout. Windows validation must exercise the native executable transition and rename-away fallback tests before packaging.

Release packages must not include `docs/`; `cleanup_paths` remains `docs` for migration from older installations.

Build MCW Update Bridge v1.5.0 from `.github/workflows/update-bridge.yml` with target `v1.5.1-beta.6`. Leave `activate_release_override=false` unless the release is explicitly declared an emergency recovery release.
