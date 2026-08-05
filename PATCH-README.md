# MCW Launcher v1.1.0-beta.3 — Finalization patch

Apply this patch **after**:

1. `v1.1.0-beta.3-responsive-step1`
2. `v1.1.0-beta.3-step2-remove-create-instance`

This final step only:

- bumps launcher runtime metadata to `v1.1.0-beta.3`;
- adds the Beta 3 release notes and README entry;
- updates launcher metadata regression tests;
- keeps the MCW Core implementation and wheel unchanged (`1.1.0b2`).

No `mcw_core/` or `src/core/` implementation file is included.

## Validation

- 1292 passed
- 79 skipped
- 2 warnings
- compileall passed

Extract over the launcher repository root and replace existing files.
