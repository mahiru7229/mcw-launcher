# MCW Launcher v0.12.0-beta.6

## Instance identity and runtime states

Beta 6 expands the instance-centered workflow introduced in Beta 5.

### Instance metadata schema v3

Each `Instance` now exposes:

- `icon`;
- `last_played`;
- `last_exit_code`;
- `last_launch_crashed`.

`instance.json` now uses `metadata_version: 3` and records the last completed launch state separately from live process state.

### Runtime-state model

The public core API exposes `InstanceState` and `InstanceStatus`:

```text
ready
loading
running
finished
crashed
```

`loading` and `running` are resolved from the live instance run lock. They are not persisted as permanent metadata, so an interrupted launcher session cannot leave an instance permanently marked as running.

`finished` and `crashed` describe the most recent completed Minecraft session.

### Instance icons

The instance workspace can now:

- choose a PNG, JPEG, WebP, BMP, or ICO file;
- copy the selected icon into `.mcw/instance-icon.<ext>`;
- replace a previous managed icon safely;
- reset to the built-in default icon;
- display a runtime-state badge over the instance icon.

### MCW package icons

`.mcwpack` exports now include managed instance icons. `package.json` also includes:

```json
{
  "instance_name": "Example",
  "instance_icon": ".mcw/instance-icon.png"
}
```

Legacy metadata that references an external icon is internalized during export without modifying the original instance.

### Public API

```python
from mcw_core import InstanceState, InstanceStatus

status = core.instances.status("Example")
statuses = core.instances.list_statuses()
core.instances.set_icon("Example", icon_path)
core.instances.reset_icon("Example")
```

### Compatibility

- Existing metadata v1/v2 remains loadable.
- Existing `.mcwpack` format version 1 remains supported.
- Extra package metadata fields are optional and ignored by older compatible readers.
- Core remains independent from GUI and PySide6.
