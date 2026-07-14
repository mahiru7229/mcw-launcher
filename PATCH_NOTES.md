# MCW Launcher — Running Instances UI

## Added

- `InstanceRunLock.list_active()` returns active instance sessions from runtime lock files.
- Stale runtime locks are removed while the list is refreshed.
- The right panel now shows:
  - Number of running instances.
  - Instance name.
  - `Preparing` or `Running` state.
- The running instance list refreshes every second.
- The Launch button always keeps the text `Launch`.

## Changed files

- `src/core/instance/instance_run_lock.py`
- `src/gui/controllers/instance_controller.py`
- `src/gui/main_window_2.py`
- `src/gui/widget/launch_control_widget.py`
- `src/gui/widget/right_panel_widget.py`
- `test/core/instance/test_instance_run_lock.py`
- `test/gui/widget/test_launch_control_widget.py`
- `test/gui/widget/test_right_panel_widget.py`

## Validation

```text
431 passed, 2 skipped, 3 xfailed
```

The two skipped tests are Qt widget tests because PySide6 is not installed in the validation sandbox. They run normally in an environment with PySide6 installed.
