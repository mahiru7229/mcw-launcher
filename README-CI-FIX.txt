MCW Launcher v1.5.1-beta.3 CI fix

Fixes Windows CI failure in:
  test/core/update/test_update_manager.py::test_rejects_undeclared_update_package_file

Cause:
  Linux executable-bit validation ran before the package allow-list validation.
  On Windows, chmod(0o755) does not provide POSIX executable bits, so the test
  raised "The Linux updater in the update package is not executable" before it
  could detect unexpected.sh as an undeclared file.

Fix:
  Validate actual package files against the manifest allow-list first, then
  perform Linux executable-bit checks.

Verification:
  test/core/update/test_update_manager.py: 19 passed
  test/core/update + test/core/package: 89 passed, 2 benign duplicate-ZIP warnings
