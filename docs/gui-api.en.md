# MCW Launcher GUI API — Developer Guide

> This document describes the APIs that an MCW Launcher user interface should use.
>
> The goal is to keep the GUI thin, replaceable, and independent from internal core implementation details.

---

## 1. Purpose

MCW Launcher follows this direction:

```text
GUI
↓
Public Core API
↓
Managers / Services
↓
Filesystem / Network / Java / Minecraft
```

The GUI should only:

- Display data.
- Collect user input.
- Call public core APIs.
- Render progress.
- Render errors.
- Move blocking work away from the UI thread.

The GUI should not:

- Read or write JSON directly.
- Access SQLite directly.
- Download Minecraft files itself.
- Build classpaths.
- Build Java commands.
- Scan Java installations.
- Verify SHA1 itself.
- Extract native libraries.
- Call private methods beginning with `_`.

---

## 2. Entry point

Root file:

```python
from src.gui.main_window import ExperimentalLauncherGUI


def main() -> None:
    ExperimentalLauncherGUI().run()


if __name__ == "__main__":
    main()
```

The official GUI class may change later, but `launcher.py` should remain the single application entry point.

---

## 3. API conventions

### Public APIs

The GUI may use:

- `VersionManifestManager`
- `VersionManager`
- `InstanceManager`
- `SettingsManager`
- `OfflineAuthentication`
- `MinecraftExecutor`
- `AccountManager` for persisted accounts
- Models from `src.models`

### Internal APIs

The GUI should not call directly:

- `HttpDownloader`
- `DownloadClientManager`
- `DownloadLibraryManager`
- `AssetIndexManager`
- `AssetManager`
- `ClasspathBuilder`
- `ContextBuilder`
- `ArgumentBuilder`
- `LauncherManager`
- `JavaManager`
- `JavaSelector`
- `JavaRuntime`
- Methods beginning with `_`

These modules are internal pipeline components and may be refactored without preserving GUI compatibility.

---

# 4. Version API

## 4.1. Load the version manifest

```python
from src.core.minecraft.version_manifest_manager import (
    VersionManifestManager,
)

versions = VersionManifestManager.get()
```

### Returns

```python
list[VersionManifest]
```

### Common fields

```python
version.id
version.type
version.url
version.release_time
```

### GUI use cases

- Populate a version selector.
- Filter releases.
- Filter snapshots.
- Sort versions by release time.
- Choose a version while creating an instance.

### Example

```python
versions = VersionManifestManager.get()

release_ids = [
    version.id
    for version in versions
    if version.type == "release"
]
```

### Threading note

`VersionManifestManager.get()` may perform a network request.

Do not call it on the Tkinter main thread.

```python
threading.Thread(
    target=load_versions,
    daemon=True,
).start()
```

---

## 4.2. Get the latest release or snapshot

```python
latest_release = VersionManifestManager.latest_version()
latest_snapshot = VersionManifestManager.latest_version(
    is_snapshot=True
)
```

### Returns

```python
str
```

The current implementation may return an empty string when the manifest is unavailable.

```python
if not latest_release:
    show_error("Unable to load the latest release.")
```

---

## 4.3. Load version metadata

```python
from src.core.minecraft.version_manager import VersionManager

version = VersionManager.load("1.20.1")
```

### Returns

```python
Version
```

### Common fields

```python
version.id
version.type
version.main_class
version.java_version
version.assets
version.asset_index
version.arguments
version.libraries
version.downloads
version.path
```

### When should the GUI call it?

- Creating a new instance.
- Showing detailed version information.
- Showing the required Java major version.
- It is not necessary before every launch because the executor handles it.

---

# 5. Instance API

## 5.1. List instances

```python
from src.core.instance.instance_manager import InstanceManager

instances = InstanceManager.list_instances()
```

### Returns

```python
list[Instance]
```

### Common fields

```python
instance.instance_id
instance.name
instance.version_id
instance.mod_loader
instance.instance_dir
```

### GUI use cases

- Instance list.
- Version labels.
- Current instance selection.
- Instance settings navigation.

---

## 5.2. Create an instance

```python
instance = InstanceManager.create(
    name="Minecraft 1.20.1",
    version=version,
    mod_loader=("vanilla", "-1"),
)
```

### Input

```python
name: str
version: Version
mod_loader: tuple[str, str]
```

### Returns

```python
Instance
```

### Full example

```python
version = VersionManager.load("1.20.1")

instance = InstanceManager.create(
    name="My 1.20.1 Instance",
    version=version,
)
```

### Common errors

- The instance name already exists.
- The name is invalid for the filesystem.
- The instance directory cannot be created.

Recommended validation:

- Not empty.
- Must not contain `<>:"/\|?*`.
- Must not end with a space or period.
- Must not be `.` or `..`.

---

## 5.3. Load an instance

```python
instance = InstanceManager.load(
    "My Instance"
)
```

### Returns

```python
Instance
```

### Use cases

- Load the instance before launching.
- Load settings.
- Display metadata.
- Export a package.

---

## 5.4. Check whether an instance exists

```python
exists = InstanceManager.is_instance_exist(
    "My Instance"
)
```

### Returns

```python
bool
```

Do not replace this with a direct `Path.exists()` check because core may also handle legacy metadata.

---

## 5.5. Rename an instance

```python
new_path = InstanceManager.rename(
    instance_name="Old Name",
    new_name="New Name",
)
```

### Returns

```python
Path
```

Refresh the GUI instance list after renaming.

---

## 5.6. Clone an instance

```python
cloned = InstanceManager.clone(
    source_name="Original",
    new_name="Clone",
    include_saves=False,
)
```

### Returns

```python
Instance
```

### `include_saves`

- `False`: excludes `saves`, `logs`, and `crash-reports`.
- `True`: copies worlds too.

Cloning may take a long time for large worlds. Always run it on a worker thread.

---

## 5.7. Delete an instance

```python
deleted = InstanceManager.delete_instance(
    "My Instance"
)
```

### Returns

```python
bool
```

The GUI must ask for confirmation because the entire instance directory is removed.

---

## 5.8. Export a package

```python
package_path = InstanceManager.export(
    instance_name="My Instance",
    output_path=Path("My Instance.mcwpack"),
    include_saves=False,
)
```

### Returns

```python
Path
```

### Suggested file dialog

```python
filedialog.asksaveasfilename(
    defaultextension=".mcwpack",
    filetypes=[
        ("MCW Package", "*.mcwpack")
    ],
)
```

---

## 5.9. Import a package

```python
instance = InstanceManager.import_instance(
    Path("My Instance.mcwpack")
)
```

### Returns

```python
Instance
```

### Common errors

- Missing `instance.json`.
- More than one `instance.json`.
- An instance with the same name already exists.
- Invalid or corrupted package.

---

# 6. Instance Settings API

## 6.1. Load settings

```python
from src.core.instance.settings_manager import SettingsManager

settings = SettingsManager.load(instance)
```

### Returns

```python
InstanceSettings
```

### Common fields

```python
settings.java_path
settings.min_memory
settings.max_memory
settings.width
settings.height
settings.fullscreen
settings.jvm_arguments
settings.game_arguments
settings.offline_multiplayer_enabled
```

---

## 6.2. Save settings

```python
SettingsManager.save(
    instance,
    settings,
)
```

### RAM example

```python
settings = SettingsManager.load(instance)

settings.min_memory = 1024
settings.max_memory = 4096

SettingsManager.save(
    instance,
    settings,
)
```

### Recommended validation

- `min_memory > 0`
- `max_memory >= min_memory`
- Avoid allocating an unreasonable amount of system RAM
- Width and height must be positive
- A custom Java path should exist before saving

---

# 7. Offline Authentication API

## 7.1. Generate an offline UUID

```python
from src.core.auth.offline_auth import OfflineAuthentication

player_uuid = OfflineAuthentication.uuid_generator(
    "Steve"
)
```

### Returns

```python
str
```

Offline UUIDs are:

- Stable for the same username.
- Case-sensitive.
- Compatible with Minecraft's offline UUID algorithm.

---

## 7.2. Authenticate an offline account

```python
authentication = OfflineAuthentication.authenticate(
    account
)
```

### Input

```python
Account
```

### Returns

```python
Authentication
```

### Full example

```python
import uuid

from src.models.account.account import Account
from src.models.account.account_source import AccountSource

account = Account(
    account_id=str(uuid.uuid4()),
    account_type=AccountSource.OFFLINE,
    username="Steve",
    uuid=OfflineAuthentication.uuid_generator(
        "Steve"
    ),
)

authentication = OfflineAuthentication.authenticate(
    account
)
```

### Username validation

Typical Minecraft username rules:

```text
3-16 characters
A-Z
a-z
0-9
_
```

Suggested regex:

```python
r"^[A-Za-z0-9_]{3,16}$"
```

---

# 8. Account API

`AccountManager` should be used for persisted accounts.

The experimental GUI may create temporary accounts in memory, while the official GUI should use `AccountManager`.

Main account use cases:

- Create an offline account.
- Read the selected account.
- Change the selected account.
- Remove an account.
- List accounts.

Conceptual example:

```python
account = AccountManager.create_offline_account(
    username
)

AccountManager.set_selected_account(
    account.account_id
)

selected = AccountManager.get_selected()
```

> Method names may still change while the account subsystem is being completed. Verify the current `AccountManager` before implementing the final account screen.

The GUI should never access `accounts.db` directly.

---

# 9. Launch API

## 9.1. Launch Minecraft

```python
from src.core.minecraft.minecraft_executor import (
    MinecraftExecutor,
)

launch_info = MinecraftExecutor.run(
    instance=instance,
    authentication=authentication,
    account=account,
    on_progress=progress_callback,
    debug_mode=False,
)
```

### Input

```python
instance: Instance
authentication: Authentication
account: Account
on_progress: ProgressCallback | None
debug_mode: bool
```

### Returns

The current implementation returns a dictionary:

```python
{
    "javaPath": Path,
    "minecraftJavaMajorVersion": int,
    "minecraftVersion": str,
}
```

### Example

```python
result = MinecraftExecutor.run(
    instance=instance,
    authentication=authentication,
    account=account,
    on_progress=on_progress,
)

print(result["javaPath"])
print(result["minecraftVersion"])
```

### Internal pipeline

The GUI does not need to call these steps:

```text
Load manifest
Load version metadata
Download client
Download libraries
Download asset index
Download assets
Load settings
Build context
Build command
Select Java
Launch Java
```

`MinecraftExecutor` owns the full pipeline.

---

# 10. Progress API

## 10.1. Callback

```python
def on_progress(
    event: ProgressEvent
) -> None:
    ...
```

### Fields

```python
event.stage
event.message
event.current
event.total
event.unit
event.fraction
event.percentage
event.is_determinate
```

### Determinate progress

```python
if event.is_determinate:
    progress_bar["value"] = (
        event.percentage or 0
    )
```

### Indeterminate progress

```python
if not event.is_determinate:
    progress_bar.configure(
        mode="indeterminate"
    )
    progress_bar.start()
```

---

## 10.2. Progress stages

```python
ProgressStage.PREPARING
ProgressStage.LOADING_VERSION
ProgressStage.DOWNLOADING_CLIENT
ProgressStage.DOWNLOADING_LIBRARIES
ProgressStage.DOWNLOADING_ASSET_INDEX
ProgressStage.DOWNLOADING_ASSETS
ProgressStage.BUILDING_CONTEXT
ProgressStage.BUILDING_COMMAND
ProgressStage.SELECTING_JAVA
ProgressStage.LAUNCHING
ProgressStage.FINISHED
```

| Stage | Purpose |
|---|---|
| `PREPARING` | Initialize the pipeline |
| `LOADING_VERSION` | Load and parse version metadata |
| `DOWNLOADING_CLIENT` | Verify or download the client JAR |
| `DOWNLOADING_LIBRARIES` | Verify or download libraries |
| `DOWNLOADING_ASSET_INDEX` | Download the asset index |
| `DOWNLOADING_ASSETS` | Download asset objects |
| `BUILDING_CONTEXT` | Build placeholder context |
| `BUILDING_COMMAND` | Build the Java/Minecraft command |
| `SELECTING_JAVA` | Select a Java runtime |
| `LAUNCHING` | Create the Java process |
| `FINISHED` | The Minecraft process was started |

`FINISHED` means the process was successfully created, not that the player has exited the game.

---

## 10.3. Tkinter thread safety

Progress callbacks may run on a worker thread.

Do not update widgets directly.

Incorrect:

```python
def on_progress(event):
    status_label.config(
        text=event.message
    )
```

Correct:

```python
def on_progress(event):
    root.after(
        0,
        apply_progress,
        event,
    )
```

---

# 11. Background task pattern

Operations involving network, disk, or subprocesses should run in the background:

- Loading the manifest.
- Loading version metadata.
- Creating, cloning, importing, or exporting instances.
- Launching Minecraft.
- Scanning Java.
- Microsoft login.

Suggested helper:

```python
def run_task(
    worker,
    on_success,
    on_error,
):
    def runner():
        try:
            result = worker()
        except Exception as error:
            root.after(
                0,
                on_error,
                error,
            )
        else:
            root.after(
                0,
                on_success,
                result,
            )

    threading.Thread(
        target=runner,
        daemon=True,
    ).start()
```

---

# 12. Error handling

Some current core APIs still raise `RuntimeError`.

Catch errors at the GUI boundary:

```python
try:
    MinecraftExecutor.run(...)
except Exception as error:
    messagebox.showerror(
        "Launch failed",
        f"{type(error).__name__}: {error}",
    )
```

Do not silently swallow errors:

```python
except Exception:
    pass
```

Do not show full tracebacks to normal users. Write technical details to a debug log instead.

---

# 13. Recommended GUI flows

## 13.1. Launcher startup

```text
Start GUI
↓
Load instance list
↓
Load selected account
↓
Load cached/remote manifest on a worker thread
↓
Populate version selector
```

---

## 13.2. Create an instance

```text
User enters a name
↓
Validate the name
↓
User selects a version
↓
VersionManager.load(version_id)
↓
InstanceManager.create(name, version)
↓
Refresh instance list
```

---

## 13.3. Launch an instance

```text
User selects an instance
↓
Load Instance
↓
Load/Create Account
↓
Authenticate
↓
Disable launch controls
↓
MinecraftExecutor.run(..., on_progress)
↓
Render ProgressEvent
↓
Show Java/version result
↓
Enable controls
```

---

## 13.4. Export/import

```text
Export:
Select instance
↓
Choose output path
↓
InstanceManager.export()

Import:
Choose .mcwpack
↓
InstanceManager.import_instance()
↓
Refresh instance list
```

---

# 14. API stability table

| API | Direct GUI use? | Expected stability |
|---|---:|---|
| `MinecraftExecutor.run` | Yes | Public |
| `InstanceManager.*` | Yes | Public |
| `SettingsManager.load/save` | Yes | Public |
| `VersionManifestManager.get` | Yes | Public |
| `VersionManager.load` | Yes | Public |
| `OfflineAuthentication.*` | Yes | Public |
| `AccountManager.*` | Yes | Public, evolving |
| `ProgressEvent` | Yes | Public |
| `HttpDownloader` | No | Internal |
| `JavaManager` | No | Internal |
| `JavaSelector` | No | Internal |
| `JavaRuntime` | No | Internal |
| `ArgumentBuilder` | No | Internal |
| `ContextBuilder` | No | Internal |
| `ClasspathBuilder` | No | Internal |
| `LauncherManager` | No | Internal |
| `AssetManager` | No | Internal |
| `DownloadLibraryManager` | No | Internal |

---

# 15. Minimal GUI launch example

```python
import threading
import uuid

from src.core.auth.offline_auth import (
    OfflineAuthentication,
)
from src.core.instance.instance_manager import (
    InstanceManager,
)
from src.core.minecraft.minecraft_executor import (
    MinecraftExecutor,
)
from src.models.account.account import Account
from src.models.account.account_source import (
    AccountSource,
)


def launch(
    instance_name: str,
    username: str,
    on_progress,
):
    instance = InstanceManager.load(
        instance_name
    )

    account = Account(
        account_id=str(uuid.uuid4()),
        account_type=AccountSource.OFFLINE,
        username=username,
        uuid=(
            OfflineAuthentication.uuid_generator(
                username
            )
        ),
    )

    authentication = (
        OfflineAuthentication.authenticate(
            account
        )
    )

    return MinecraftExecutor.run(
        instance=instance,
        authentication=authentication,
        account=account,
        on_progress=on_progress,
    )


threading.Thread(
    target=lambda: launch(
        "My Instance",
        "Steve",
        print,
    ),
    daemon=True,
).start()
```

---

# 16. Best practices

- Run network, disk, and subprocess operations outside the UI thread.
- Never access launcher data files directly.
- Never call `_private` methods from the GUI.
- Use `ProgressEvent` instead of parsing log text.
- Refresh models after create, rename, delete, or import operations.
- Validate user input before calling core.
- Disable controls while a task is running.
- Prevent accidental duplicate launches.
- Log technical errors to files and show concise messages to users.
- Keep the GUI independent enough to migrate from Tkinter to PySide or another framework.

---

# 17. Future public facade

A future core facade may look like:

```python
from mcw_launcher import MCWLauncher

launcher = MCWLauncher()

launcher.list_versions()
launcher.list_instances()
launcher.create_instance(...)
launcher.launch(...)
```

When this facade exists, GUIs should prefer it over importing many manager classes directly.

---

# 18. Pre-merge GUI checklist

- [ ] The GUI does not freeze while loading the manifest.
- [ ] The GUI does not freeze while launching.
- [ ] Progress callbacks are thread-safe.
- [ ] Create/load/rename/clone/delete instance operations work.
- [ ] `.mcwpack` import/export works.
- [ ] Offline accounts work.
- [ ] Java is selected by core.
- [ ] No unwanted Java console window appears.
- [ ] Errors are displayed clearly.
- [ ] The GUI never reads JSON or SQLite directly.
- [ ] Tests and GitHub Actions still pass.

---

## Conclusion

The MCW Launcher GUI should remain a thin client of the core.

Main principle:

```text
The GUI decides how information is displayed.
The core decides how Minecraft works.
```

Maintaining this boundary makes it easier to:

- Replace the GUI.
- Build a CLI.
- Reuse the core.
- Refactor internal modules.
- Allow other launchers to use MCW Launcher Core.