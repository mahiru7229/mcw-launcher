# MCW Launcher v1.1.0-beta.6 — Launcher diff

## Baseline

Apply this patch on top of a complete **MCW Launcher v1.1.0-beta.5** source tree.

## Apply

Extract the ZIP into the repository root and allow files to be replaced.

This package contains launcher repository changes only. It does **not** contain a standalone `mcw_core` source archive, wheel, or any compiled executable.

Files under `src/core/` are the implementation bundled directly inside the launcher repository and are required for the Forge/NeoForge fixes.

## Main fixes

- Account credential re-protection now returns shared progress to a final success or failure state.
- Forge/NeoForge installers use the Java selected for the instance and retry once with another compatible Java on a recognized Java-runtime failure.
- Pre-1.7 Forge profiles using `net.minecraftforge:minecraftforge` are accepted as valid Forge runtimes instead of being blocked by the false `no runtime` error.

## Validation

- 1312 passed, 82 skipped, 2 warnings.
- `python -m compileall -q src test launcher.py` passed.
