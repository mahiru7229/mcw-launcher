# MCW Launcher v1.1.0-beta.5 launcher diff

Apply this patch on top of the completed **v1.1.0-beta.4** launcher tree.

## Included

- Normalizes reserved single-value game options before the final Java launch command is created.
- Fixes legacy Forge/LaunchWrapper profiles that contain duplicate `--gameDir` values, including Forge 1.12.2-style inherited `minecraftArguments`.
- Handles both `--option value` and `--option=value` forms.
- Uses canonical launch-context values for launcher-controlled paths and version fields.
- Preserves repeatable Forge options such as `--tweakClass`.
- Rejects malformed single-value options before Java is spawned.
- Includes version metadata, README/release notes, and regression tests.

## Delivery boundary

- This is a launcher-repository changed-files patch only.
- No `mcw_core/` implementation files, wheel, or separate MCW Core source archive are included.
- `src/core/minecraft/` is the implementation bundled inside the launcher repository; it is included because the launch-command fix lives there.
- The standalone MCW Core distribution remains `1.1.0b2` until the final v1.1.0 release.

## Apply

Extract this ZIP into the repository root and allow files to be replaced.

## Validation

- `PYTHONPATH=. pytest -q`: **1304 passed, 81 skipped, 2 warnings**.
- `python -m compileall -q src mcw_core test launcher.py`: passed.
- Perform a Windows smoke test with a real Forge 1.12.2 instance to confirm LaunchWrapper no longer reports multiple values for `gameDir`.
