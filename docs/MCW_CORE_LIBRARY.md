# MCW Core Library

MCW Core is the GUI-independent runtime used by MCW Launcher. It can be imported from a Python program without installing PySide6.

```python
from mcw_core import CorePaths, LaunchRequest, MCWCore

core = MCWCore(CorePaths.from_root(r"D:\\Games\\MCW"))
core.operations.begin()
try:
    result = core.launch(
        LaunchRequest(
            instance="My Quilt Instance",
            offline_username="Player",
            on_progress=print,
        )
    )
finally:
    core.operations.finish()

print(result.minecraft_version, result.java_path)
```

The same operation can be run without the GUI:

```powershell
python tools\core_smoke_launch.py --root D:\Games\MCW --instance "My Quilt Instance" --username Player
```

## Public API

The supported import surface is exposed from `mcw_core`:

- `MCWCore` and `CorePaths`
- `LaunchRequest` and `LaunchResult`
- `InstanceCreateRequest`
- `OperationHandle`
- progress event models

Consumers should not import implementation modules from `src.core`.

## Process-wide paths

The current implementation keeps one active path configuration per Python process. Create one `MCWCore` for an application root, or explicitly call `configure_default_core()` before using the default facade.
