# MCW Launcher GUI API — Hướng dẫn phát triển giao diện

> Tài liệu này mô tả các API mà giao diện người dùng của MCW Launcher nên sử dụng.
>
> Mục tiêu là giữ GUI mỏng, dễ thay thế, và không phụ thuộc vào chi tiết triển khai bên trong core.

---

## 1. Mục đích

MCW Launcher được thiết kế theo hướng:

```text
GUI
↓
Public Core API
↓
Managers / Services
↓
Filesystem / Network / Java / Minecraft
```

GUI chỉ nên chịu trách nhiệm:

- Hiển thị dữ liệu.
- Nhận thao tác từ người dùng.
- Gọi API public của core.
- Hiển thị tiến trình.
- Hiển thị lỗi.
- Điều phối các thao tác nền để không làm treo giao diện.

GUI không nên:

- Đọc hoặc ghi JSON trực tiếp.
- Truy cập SQLite trực tiếp.
- Tự tải file Minecraft.
- Tự build classpath.
- Tự build command Java.
- Tự quét Java.
- Tự kiểm tra SHA1.
- Tự giải nén native.
- Gọi trực tiếp các hàm nội bộ bắt đầu bằng `_`.

---

## 2. Entry point

File root:

```python
from src.gui.main_window import ExperimentalLauncherGUI


def main() -> None:
    ExperimentalLauncherGUI().run()


if __name__ == "__main__":
    main()
```

GUI chính thức sau này có thể đổi class, nhưng `launcher.py` nên tiếp tục là entry point duy nhất.

---

## 3. Quy ước API

### API public

GUI được phép dùng:

- `VersionManifestManager`
- `VersionManager`
- `InstanceManager`
- `SettingsManager`
- `OfflineAuthentication`
- `MinecraftExecutor`
- `AccountManager` khi cần quản lý account
- Các model trong `src.models`

### API nội bộ

GUI không nên gọi trực tiếp:

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
- Các method bắt đầu bằng `_`

Các module này thuộc pipeline nội bộ của core và có thể được refactor mà không cần giữ tương thích với GUI.

---

# 4. Version API

## 4.1. Lấy danh sách version

```python
from src.core.minecraft.version_manifest_manager import (
    VersionManifestManager,
)

versions = VersionManifestManager.get()
```

### Trả về

```python
list[VersionManifest]
```

### Các field thường dùng

```python
version.id
version.type
version.url
version.release_time
```

### Mục đích trong GUI

- Hiển thị danh sách version.
- Lọc release.
- Lọc snapshot.
- Sắp xếp theo thời gian phát hành.
- Chọn version khi tạo instance.

### Ví dụ

```python
versions = VersionManifestManager.get()

release_ids = [
    version.id
    for version in versions
    if version.type == "release"
]
```

### Lưu ý thread

`VersionManifestManager.get()` có thể thực hiện network request.

Không gọi trực tiếp trên Tkinter main thread.

```python
threading.Thread(
    target=load_versions,
    daemon=True,
).start()
```

---

## 4.2. Lấy latest release hoặc snapshot

```python
latest_release = VersionManifestManager.latest_version()
latest_snapshot = VersionManifestManager.latest_version(
    is_snapshot=True
)
```

### Trả về

```python
str
```

Nếu không lấy được manifest, implementation hiện tại có thể trả chuỗi rỗng.

GUI nên kiểm tra:

```python
if not latest_release:
    show_error("Không thể lấy latest release.")
```

---

## 4.3. Load metadata của một version

```python
from src.core.minecraft.version_manager import VersionManager

version = VersionManager.load("1.20.1")
```

### Trả về

```python
Version
```

### Các field thường dùng

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

### GUI nên dùng khi nào?

- Tạo instance mới.
- Hiển thị thông tin version chi tiết.
- Kiểm tra Java major yêu cầu.
- Không cần gọi trước mỗi launch nếu executor đã xử lý.

---

# 5. Instance API

## 5.1. Danh sách instance

```python
from src.core.instance.instance_manager import InstanceManager

instances = InstanceManager.list_instances()
```

### Trả về

```python
list[Instance]
```

### Field thường dùng

```python
instance.instance_id
instance.name
instance.version_id
instance.mod_loader
instance.instance_dir
```

### GUI usage

- Danh sách instance.
- Hiển thị version.
- Chọn instance hiện tại.
- Điều hướng tới màn hình settings.

---

## 5.2. Tạo instance

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

### Trả về

```python
Instance
```

### Ví dụ đầy đủ

```python
version = VersionManager.load("1.20.1")

instance = InstanceManager.create(
    name="My 1.20.1 Instance",
    version=version,
)
```

### Lỗi thường gặp

- Tên instance đã tồn tại.
- Tên không hợp lệ với filesystem.
- Không tạo được thư mục.

GUI nên validate tên trước khi gọi:

- Không rỗng.
- Không chứa `<>:"/\|?*`.
- Không kết thúc bằng dấu cách hoặc dấu chấm.
- Không dùng `.` hoặc `..`.

---

## 5.3. Load instance

```python
instance = InstanceManager.load(
    "My Instance"
)
```

### Trả về

```python
Instance
```

### Mục đích

- Lấy object instance trước khi launch.
- Lấy settings.
- Hiển thị metadata.
- Export package.

---

## 5.4. Kiểm tra instance tồn tại

```python
exists = InstanceManager.is_instance_exist(
    "My Instance"
)
```

### Trả về

```python
bool
```

Không nên chỉ kiểm tra thư mục bằng `Path.exists()`, vì core còn hỗ trợ metadata legacy.

---

## 5.5. Rename instance

```python
new_path = InstanceManager.rename(
    instance_name="Old Name",
    new_name="New Name",
)
```

### Trả về

```python
Path
```

Sau khi rename, GUI nên refresh danh sách instance.

---

## 5.6. Clone instance

```python
cloned = InstanceManager.clone(
    source_name="Original",
    new_name="Clone",
    include_saves=False,
)
```

### Trả về

```python
Instance
```

### `include_saves`

- `False`: bỏ `saves`, `logs`, `crash-reports`.
- `True`: sao chép cả world.

Clone có thể tốn nhiều thời gian nếu world lớn. Luôn chạy background thread.

---

## 5.7. Xóa instance

```python
deleted = InstanceManager.delete_instance(
    "My Instance"
)
```

### Trả về

```python
bool
```

GUI phải hỏi xác nhận trước vì thao tác xóa toàn bộ thư mục instance.

---

## 5.8. Export package

```python
package_path = InstanceManager.export(
    instance_name="My Instance",
    output_path=Path("My Instance.mcwpack"),
    include_saves=False,
)
```

### Trả về

```python
Path
```

### GUI usage

Dùng file dialog:

```python
filedialog.asksaveasfilename(
    defaultextension=".mcwpack",
    filetypes=[
        ("MCW Package", "*.mcwpack")
    ],
)
```

---

## 5.9. Import package

```python
instance = InstanceManager.import_instance(
    Path("My Instance.mcwpack")
)
```

### Trả về

```python
Instance
```

### Lỗi thường gặp

- Package không có `instance.json`.
- Package có nhiều `instance.json`.
- Instance cùng tên đã tồn tại.
- File không phải package hợp lệ.

---

# 6. Instance Settings API

## 6.1. Load settings

```python
from src.core.instance.settings_manager import SettingsManager

settings = SettingsManager.load(instance)
```

### Trả về

```python
InstanceSettings
```

### Các field thường dùng

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

### Ví dụ cập nhật RAM

```python
settings = SettingsManager.load(instance)

settings.min_memory = 1024
settings.max_memory = 4096

SettingsManager.save(
    instance,
    settings,
)
```

### GUI validation đề xuất

- `min_memory > 0`
- `max_memory >= min_memory`
- Không cấp quá nhiều RAM so với máy
- Width và height phải lớn hơn 0
- Java path phải tồn tại nếu người dùng chọn custom path

---

# 7. Offline Authentication API

## 7.1. Tạo offline UUID

```python
from src.core.auth.offline_auth import OfflineAuthentication

player_uuid = OfflineAuthentication.uuid_generator(
    "Steve"
)
```

### Trả về

```python
str
```

UUID offline:

- Ổn định với cùng username.
- Phân biệt chữ hoa chữ thường.
- Dùng thuật toán offline UUID của Minecraft.

---

## 7.2. Authenticate offline account

```python
authentication = OfflineAuthentication.authenticate(
    account
)
```

### Input

```python
Account
```

### Trả về

```python
Authentication
```

### Ví dụ đầy đủ

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

Minecraft username thông thường:

```text
3-16 ký tự
A-Z
a-z
0-9
_
```

Regex đề xuất:

```python
r"^[A-Za-z0-9_]{3,16}$"
```

---

# 8. Account API

AccountManager dùng để lưu account lâu dài.

GUI test có thể tạo account tạm trong memory, nhưng GUI chính thức nên dùng AccountManager.

Các use case chính:

- Tạo offline account.
- Lấy account đang được chọn.
- Chọn account.
- Xóa account.
- Danh sách account.

Ví dụ khái niệm:

```python
account = AccountManager.create_offline_account(
    username
)

AccountManager.set_selected_account(
    account.account_id
)

selected = AccountManager.get_selected()
```

> Tên method có thể thay đổi trong quá trình hoàn thiện account subsystem. Trước khi build GUI account chính thức, kiểm tra trực tiếp `AccountManager` hiện tại.

GUI không nên truy cập `accounts.db` trực tiếp.

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

### Trả về

Implementation hiện tại trả dictionary:

```python
{
    "javaPath": Path,
    "minecraftJavaMajorVersion": int,
    "minecraftVersion": str,
}
```

### Ví dụ

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

### Pipeline bên trong

GUI không cần gọi từng bước sau:

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

`MinecraftExecutor` thực hiện toàn bộ.

---

# 10. Progress API

## 10.1. Callback

```python
def on_progress(
    event: ProgressEvent
) -> None:
    ...
```

### Field

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

### Ý nghĩa

| Stage | Mục đích |
|---|---|
| `PREPARING` | Khởi tạo pipeline |
| `LOADING_VERSION` | Tải và parse version metadata |
| `DOWNLOADING_CLIENT` | Kiểm tra hoặc tải client JAR |
| `DOWNLOADING_LIBRARIES` | Kiểm tra hoặc tải libraries |
| `DOWNLOADING_ASSET_INDEX` | Tải asset index |
| `DOWNLOADING_ASSETS` | Tải asset objects |
| `BUILDING_CONTEXT` | Tạo placeholder context |
| `BUILDING_COMMAND` | Build Java/Minecraft command |
| `SELECTING_JAVA` | Chọn Java runtime |
| `LAUNCHING` | Gọi Java process |
| `FINISHED` | Minecraft process đã được khởi chạy |

`FINISHED` nghĩa là process được tạo thành công, không phải người chơi đã thoát game.

---

## 10.3. Tkinter thread safety

Progress callback có thể chạy từ worker thread.

Không cập nhật widget trực tiếp.

Sai:

```python
def on_progress(event):
    status_label.config(
        text=event.message
    )
```

Đúng:

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

Mọi thao tác có network, disk hoặc subprocess nên chạy background:

- Load manifest.
- Load version.
- Create/clone/import/export instance.
- Launch Minecraft.
- Scan Java.
- Microsoft login.

Mẫu đề xuất:

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

Hiện một số core API vẫn dùng `RuntimeError`.

GUI nên bắt lỗi tại boundary:

```python
try:
    MinecraftExecutor.run(...)
except Exception as error:
    messagebox.showerror(
        "Launch failed",
        f"{type(error).__name__}: {error}",
    )
```

Không nên nuốt exception:

```python
except Exception:
    pass
```

Không nên hiển thị traceback đầy đủ cho người dùng bình thường. Có thể ghi traceback vào debug log.

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
Load cached/remote manifest in worker thread
↓
Populate version selector
```

---

## 13.2. Create instance

```text
User enters name
↓
Validate name
↓
User selects version
↓
VersionManager.load(version_id)
↓
InstanceManager.create(name, version)
↓
Refresh instance list
```

---

## 13.3. Launch instance

```text
User selects instance
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

| API | GUI dùng trực tiếp? | Độ ổn định mong đợi |
|---|---:|---|
| `MinecraftExecutor.run` | Có | Public |
| `InstanceManager.*` | Có | Public |
| `SettingsManager.load/save` | Có | Public |
| `VersionManifestManager.get` | Có | Public |
| `VersionManager.load` | Có | Public |
| `OfflineAuthentication.*` | Có | Public |
| `AccountManager.*` | Có | Public, đang phát triển |
| `ProgressEvent` | Có | Public |
| `HttpDownloader` | Không | Internal |
| `JavaManager` | Không | Internal |
| `JavaSelector` | Không | Internal |
| `JavaRuntime` | Không | Internal |
| `ArgumentBuilder` | Không | Internal |
| `ContextBuilder` | Không | Internal |
| `ClasspathBuilder` | Không | Internal |
| `LauncherManager` | Không | Internal |
| `AssetManager` | Không | Internal |
| `DownloadLibraryManager` | Không | Internal |

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

- Luôn chạy network/disk/subprocess ngoài UI thread.
- Không truy cập file data trực tiếp.
- Không gọi method `_private`.
- Dùng `ProgressEvent` thay cho parse text log.
- Refresh model sau create/rename/delete/import.
- Validate user input trước khi gọi core.
- Disable button khi task đang chạy.
- Không cho launch hai lần cùng một instance ngoài ý muốn.
- Log lỗi kỹ thuật vào file, hiển thị thông báo ngắn cho người dùng.
- Giữ GUI độc lập với Tkinter nếu có kế hoạch chuyển sang PySide hoặc framework khác.

---

# 17. Future public facade

Trong tương lai, core có thể thêm facade:

```python
from mcw_launcher import MCWLauncher

launcher = MCWLauncher()

launcher.list_versions()
launcher.list_instances()
launcher.create_instance(...)
launcher.launch(...)
```

Khi facade này tồn tại, GUI nên ưu tiên facade thay vì import nhiều manager riêng.

---

# 18. Checklist trước khi merge GUI

- [ ] GUI không block khi tải manifest.
- [ ] GUI không block khi launch.
- [ ] Progress callback thread-safe.
- [ ] Instance create/load/rename/clone/delete hoạt động.
- [ ] Import/export `.mcwpack` hoạt động.
- [ ] Offline account hoạt động.
- [ ] Java được core tự chọn.
- [ ] Không có cửa sổ console Java ngoài ý muốn.
- [ ] Lỗi được hiển thị rõ.
- [ ] Không đọc JSON/SQLite trực tiếp.
- [ ] Test suite và GitHub Actions vẫn pass.

---

## Kết luận

GUI của MCW Launcher nên là một client mỏng của core.

Tư tưởng chính:

```text
GUI quyết định cách hiển thị.
Core quyết định cách Minecraft hoạt động.
```

Giữ ranh giới này sẽ giúp:

- Dễ thay GUI.
- Dễ viết CLI.
- Dễ tái sử dụng core.
- Dễ refactor.
- Dễ cho launcher khác dùng MCW Launcher Core.