# MCW Launcher v1.1.0-beta.3 — Step 1: Responsive mod-loader UI

Incremental launcher-only patch for **v1.1.0-beta.2**.

## Apply

Extract this ZIP over the launcher repository root and replace existing files.

## Scope

This step only fixes the responsive layout of **Advanced Instance Management**:

- The advanced dialog is freely resizable instead of being locked to its initial size.
- Minimum supported dialog size is `520 × 420`.
- Mod-loader and loader-version fields are side by side on wide layouts and stacked on narrower layouts.
- Loader action buttons reflow between 3, 2, and 1 columns.
- The remaining instance action buttons use the same reflow behavior so the management card does not overflow.
- Long loader-version values no longer force unnecessary horizontal expansion.
- Compact margins and spacing are enabled automatically on narrow layouts.

The duplicated **Create instance** section is intentionally still present. Its removal is the next Beta 3 step.

This patch does not change MCW Core, package metadata, version metadata, language files, or release documentation.

## Changed files

- `src/gui/dialogs/instance_management_dialog.py`
- `src/gui/pages/instances_page.py`
- `test/gui/dialogs/test_instance_management_dialog.py`
- `test/gui/pages/test_instances_page.py`

## Validation performed

- Modified Python files compile successfully.
- Existing version/public-API smoke tests: `5 passed`.
- Responsive GUI tests were added, but could not be executed in the packaging environment because PySide6 is unavailable there; run them on the normal launcher development environment.
