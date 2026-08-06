# MCW Launcher v1.1.1-beta.5 pack dependency compatibility hotfix

Apply this hotfix to a complete **v1.1.1-beta.5** source tree.

## Apply

1. Close MCW Launcher and Minecraft.
2. Back up local changes.
3. Extract this ZIP into the repository root and allow changed files to be replaced.
4. Run `python -m pytest -q`.

## Scope

- Keeps missing and disabled required dependencies as blocking errors.
- Accepts a dependency version selected by the modpack manifest when both the requiring mod and installed dependency are managed by that modpack.
- Converts launcher-only version-parser disagreements for pack-pinned dependencies into non-blocking warnings.
- Keeps strict version validation for manually added or unmanaged dependency files.
- Adds regression coverage for the reported Caelus, Curios, AutoRegLib, LibX, and Skyblock Builder version formats.

## Validation

- 1382 passed, 88 skipped, 2 expected ZIP-fixture warnings.
- `compileall` passed for `src` and `test`.

This is a launcher-only Beta 5 hotfix. It does not publish a new MCW Core source archive or wheel.
