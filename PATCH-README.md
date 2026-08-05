# MCW Launcher v1.1.0 — pytest freeze hotfix

Apply this patch to the root of the MCW Launcher v1.1.0 repository.

## Fixed

`test_workspace_create_dialog_emits_public_create_contract` still used the old three-argument create signal and attempted to create a Quilt instance without supplying the newly-required loader version.

That path opens `QMessageBox.information(...)`. Under pytest with `QT_QPA_PLATFORM=offscreen`, the modal message box is invisible and waits forever, making the suite appear frozen.

The test now:

- provides a compatible Quilt loader version;
- validates the selected loader version;
- listens to the stable four-argument create contract;
- completes without opening a modal dialog.

## Changed file

- `test/gui/pages/test_instance_workspace_page.py`

This is a test-only patch. Runtime launcher and MCW Core code are unchanged.
