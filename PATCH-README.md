# MCW Launcher v1.1.1-beta.5 dependency-resolution patch

Apply this patch to a complete **v1.1.1-beta.4** source tree.

## Apply

1. Close MCW Launcher and Minecraft.
2. Back up local changes.
3. Extract this ZIP into the repository root and allow changed files to be replaced.
4. Run `python -m pytest -q`.

## Scope

- Recursive required-dependency completion for Modrinth and CurseForge managed modpacks.
- Pack-pinned files remain authoritative and are never silently replaced.
- Missing, disabled, or version-invalid required dependencies cannot be bypassed by the compatibility override.
- Dependency provenance records `selectionReason` and `requiredBy`.
- Modpack Repair reruns dependency resolution and downloads newly added files.
- Runtime/package version updated to v1.1.1-beta.5 / 1.1.1b5.

## Validation

- 1375 passed, 88 skipped, 2 expected ZIP-fixture warnings.
- `compileall` passed for `src`, `mcw_core`, and `test`.

This beta patch does not contain a separately published Core source archive or wheel. Those remain scheduled for v1.1.1 stable.
