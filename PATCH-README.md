# MCW Launcher v1.1.0-beta.4 launcher diff

Apply this patch on top of the completed **v1.1.0-beta.3** launcher tree.

## Included

- Bounded automatic retry for temporary metadata/network failures.
- A manual **Retry / Cancel** dialog after all three automatic attempts fail.
- Exact task resubmission with the original parameters, task ID, blocking mode, and progress message.
- Duplicate-task protection, bounded remembered retry registrations, sensitive-data redaction, translations, tests, version metadata, README, and release notes.

## Not included

- No implementation files from `src/core/`.
- No implementation files from `mcw_core/`.
- No wheel or full source archive.
- No Forge legacy `--gameDir` fix.
- No account-protection progress fix.

## Apply

Extract this ZIP into the repository root and allow files to be replaced.

## Validation

- `PYTHONPATH=. pytest -q`: **1299 passed, 81 skipped, 2 warnings**.
- `python -m compileall -q src launcher.py test`: passed.
- GUI retry tests are included but skipped in this environment because PySide6 is unavailable; smoke-test Retry/Cancel on Windows.
