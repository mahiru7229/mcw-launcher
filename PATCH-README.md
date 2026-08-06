# MCW Launcher v1.1.1-beta.3 — OptiFine optional component

Apply this launcher diff over a complete **v1.1.1-beta.2** source tree.

It adds OptiFine metadata discovery, manual official-JAR selection, Vanilla standalone and Forge-mod installation modes, compatibility states, transactional journal/rollback, create-instance integration, existing-instance management, repair/uninstall, launch integration, export policy, translations, and regression tests.

This beta does **not** include a separate MCW Core source archive or wheel. The small `mcw_core/` changes inside this launcher patch only expose the new feature through the existing public GUI/Core boundary.

See `docs/RELEASE-v1.1.1-beta.3.md` for details.
