# Beta 6 Windows CI test fix

This patch updates `test/core/update/test_update_applier.py` so the generic atomic-replace test uses a normal managed file instead of `MCW Launcher.exe`.

Why: on Windows, Beta 6 intentionally routes the launcher executable through the native Windows replacement path, so patching `os.replace` no longer observes launcher replacement calls.

Validated:
- `python -m pytest test/core/update/test_update_applier.py -q` -> 18 passed
- `python -m pytest test/core/update -q` -> 65 passed
