# MCW Launcher v1.1.1-beta.1 — ATLauncher patch

This archive contains only launcher repository files changed from MCW Launcher v1.1.0.
It does not include a standalone MCW Core source archive or wheel.

## Apply

1. Close MCW Launcher and any running test process.
2. Back up the repository or commit the current working tree.
3. Extract this ZIP into the repository root and allow files to be replaced.
4. Keep the v1.1.0 pytest-freeze hotfix if it is already present; this patch does not replace that test file.
5. Run `python -m pytest -q`.

## ATLauncher Beta 1 scope

- Public pack search/browser through the ATLauncher V2 GraphQL API.
- V1/CDN fallback for pack details, versions, and `Configs.json` installation manifests.
- Explicit pack-version and release-channel selection.
- Vanilla, Forge, NeoForge, Fabric, and Quilt runtime resolution.
- Deferred first-launch file downloads with SHA-1/MD5 verification and bounded retries.
- Safe staged extraction of `Configs.zip`.
- ATLauncher registry, provenance, Content Library integration, cache status, and cache clearing.

Packs requiring browser-only files, custom libraries/main classes, jar mods, extract/decomp actions,
or other legacy install behavior are deliberately blocked in this beta instead of being partially installed.

## Suggested Windows smoke test

1. Open Add Instance and choose **Browse ATLauncher packs**.
2. Search for a public pack and open its details.
3. Select a supported version and create an instance.
4. Launch it once and verify aggregate download progress.
5. Confirm files pass checksum verification and `Configs.zip` content appears in the instance.
6. Confirm the ATLauncher pack appears in Content Library.

Changed repository files: 40
