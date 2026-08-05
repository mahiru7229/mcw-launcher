# MCW Launcher v1.1.0-beta.2 — Launcher Patch

Incremental patch for **MCW Launcher v1.1.0-beta.1** after the corrected translation-audit hotfix.

## Apply

1. Close MCW Launcher.
2. Back up the repository/worktree.
3. Extract this ZIP over the launcher repository root.
4. Replace files when prompted.
5. Install the accompanying `mcw_core-1.1.0b2-py3-none-any.whl` into the build/test environment before packaging the EXE.

## Scope

This beta only adds explicit Automatic/Custom Java selection and bounded one-time Java recovery. It does not include the later responsive mod-loader, network Retry, Forge legacy `--gameDir`, or account-security progress fixes.

## Changed files (22)

- `README.md`
- `docs/RELEASE-v1.1.0-beta.2.md`
- `lang/en-US.json`
- `lang/vi-VN.json`
- `pyproject.toml`
- `src/config.py`
- `src/core/java/java_manager.py`
- `src/core/java/java_resolver.py`
- `src/core/java/java_runtime.py`
- `src/core/java/java_selector.py`
- `src/core/minecraft/minecraft_executor.py`
- `src/gui/controllers/settings_controller.py`
- `src/gui/dialogs/instance_settings_editor_dialog.py`
- `src/gui/pages/instance_settings_page.py`
- `test/core/config/test_version_metadata.py`
- `test/core/java/test_java_manager.py`
- `test/core/java/test_java_resolver.py`
- `test/core/java/test_java_runtime.py`
- `test/core/java/test_java_selector.py`
- `test/core/minecraft/test_minecraft_executor.py`
- `test/gui/pages/test_instance_settings_page.py`
- `test/test_public_api.py`
