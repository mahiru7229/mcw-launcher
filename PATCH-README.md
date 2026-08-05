# MCW Launcher v1.1.0-beta.1 — Launcher patch

Extract this archive over the repository root.
Only files added or changed for v1.1.0-beta.1 are included.

Scope: missing translations only. This patch localizes the advanced instance page and remaining dynamic progress messages.

Validation:
- Launcher suite: 1281 passed, 79 skipped.
- Core suite: 18 passed.
- Wheel import smoke test: passed.

Added files:
+ docs/RELEASE-v1.1.0-beta.1.md

Changed files:
* README.md
* lang/en-US.json
* lang/vi-VN.json
* pyproject.toml
* src/config.py
* src/gui/dialogs/instance_management_dialog.py
* src/gui/pages/instance_workspace_page.py
* src/gui/pages/instances_page.py
* test/core/config/test_version_metadata.py
* test/gui/pages/test_instance_workspace_page.py
* test/gui/pages/test_instances_page.py
* test/test_language_runtime.py
* test/test_public_api.py

Removed files:
(none)
