# MCW Launcher v0.10.0

> Stable release for CurseForge Fabric support, global instance defaults, and settings-aware `.mcwpack` imports. This release promotes the features verified throughout the v0.10.0 Beta cycle without adding last-minute features.

---

## Tiếng Việt

### Điểm nổi bật

- Cài mod **Fabric hoặc Forge trực tiếp từ CurseForge** trong catalog Mods.
- Cài modpack **Fabric hoặc Forge từ CurseForge** dựa trên loader và phiên bản được khai báo trong `manifest.json`.
- Dùng nhãn Minecraft/loader của nhà cung cấp để ưu tiên kết quả thay vì chặn cứng; metadata thật trong file JAR vẫn được kiểm tra trước khi thay đổi instance.
- Tự động chuẩn bị toàn bộ file và dependency bắt buộc trước khi cài; rollback mod cùng registry nếu bước áp dụng thất bại.
- Giữ luồng tải thủ công có xác minh dung lượng/SHA-1 khi tác giả tắt phân phối bên thứ ba.

### Cài đặt mặc định cho instance mới

- Launcher Settings có bảng **Cài đặt mặc định cho instance** dùng chung schema với `settings.json` của từng instance.
- Có thể đặt Java, RAM tối thiểu/tối đa, cửa sổ/toàn màn hình, LAN authentication/connection, chính sách Modrinth/CurseForge, Forge preflight, JVM arguments và game arguments.
- Mọi instance Vanilla, Fabric hoặc Forge mới đều sao chép bộ mặc định tại thời điểm tạo.
- Instance do modpack Modrinth hoặc CurseForge tạo cũng dùng cùng luồng mặc định.
- Instance đã tồn tại không bị thay đổi; `settings.json` riêng vẫn có độ ưu tiên cao nhất.

### Import `.mcwpack`

Trước khi giải nén, launcher kiểm tra metadata và hiển thị thông tin của gói. Người dùng có thể:

1. dùng cài đặt mặc định của launcher và ghi đè setting trong gói;
2. giữ nguyên setting được lưu trong `.mcwpack`;
3. mở toàn bộ setting của gói để xem và chỉnh trước khi import.

Nếu gói không có `settings.json`, chế độ giữ setting trong gói sẽ bị tắt và launcher dùng setting tổng. Setting được chuẩn hóa theo giới hạn RAM vật lý và các policy hợp lệ trước khi ghi atomically.

### An toàn và tương thích

- Override của modpack không được ghi đè `instance.json`, `settings.json` hoặc thư mục `.mcw` do launcher quản lý.
- Không thay đổi account database, Microsoft token storage, world, save hoặc file cá nhân trong instance hiện có.
- Kênh `stable` tiếp tục là mặc định cho người dùng thông thường.
- Lựa chọn tham gia tester program vẫn là opt-in và không bị tự động bật.
- NeoForge và Quilt chưa được hỗ trợ trong `v0.10.0`.

### Metadata phát hành

```text
VERSION = v0.10.0
VERSION_ID = 0.10.0
TAG = v0.10.0
UPDATE_CHANNEL = stable
```

GitHub Release phải là bản phát hành thông thường, không đánh dấu **Pre-release**.

### Tài sản phát hành

```text
MCW-Launcher-v0.10.0-windows-x64.zip
MCW-Launcher-v0.10.0-windows-x64.zip.sha256
```

### Xác minh trước khi tải lên

Baseline của source Beta 2:

- Toàn bộ test: `1055 passed`, `0 failed`, `0 errors`.
- Language parity: `1102` key trong cả `en-US` và `vi-VN`.
- Merge marker chưa xử lý: `0`.

Sau khi đổi metadata sang Stable, phải chạy lại:

```powershell
python -m tools.release_preflight
python -m pytest test -q
```

Chỉ build và phát hành khi cả hai lệnh đều thành công.

---

## English

### Highlights

- Install **Fabric or Forge mods directly from CurseForge** through the Mods catalog.
- Install **Fabric or Forge CurseForge modpacks** from the loader and Minecraft version declared by `manifest.json`.
- Treat provider Minecraft/loader labels as ranking hints instead of hard blockers; validate real JAR metadata before changing an instance.
- Prepare every automatic file and required dependency before installation, then roll back mods and registry data if apply fails.
- Preserve the size/SHA-1-verified manual download flow when an author disables third-party distribution.

### Defaults for new instances

- Launcher Settings includes **Default instance settings**, backed by the same schema as each instance's `settings.json`.
- Configure Java, minimum/maximum memory, window/fullscreen, LAN authentication/connection, Modrinth/CurseForge policies, Forge preflight, JVM arguments, and game arguments.
- Every new Vanilla, Fabric, or Forge instance copies these defaults at creation time.
- Modrinth and CurseForge modpack instances use the same defaults path.
- Existing instances are not rewritten; their own `settings.json` remains authoritative.

### `.mcwpack` import

Before extraction, the launcher inspects package metadata and displays package details. Users can:

1. apply launcher defaults and overwrite package settings;
2. preserve settings stored in the `.mcwpack`;
3. open the complete package settings for review and editing before import.

When a package has no `settings.json`, preserve mode is disabled and launcher defaults are used. Settings are normalized against physical-memory limits and valid policies before atomic persistence.

### Safety and compatibility

- Modpack override layers cannot replace launcher-owned `instance.json`, `settings.json`, or `.mcw` paths.
- The release does not rewrite account databases, Microsoft token storage, worlds, saves, or personal files in existing instances.
- `stable` remains the default channel for regular users.
- The tester program remains opt-in and is never enabled automatically.
- NeoForge and Quilt are not supported in `v0.10.0`.

### Release metadata

```text
VERSION = v0.10.0
VERSION_ID = 0.10.0
TAG = v0.10.0
UPDATE_CHANNEL = stable
```

The GitHub Release must be a normal release and must not be marked as a **Pre-release**.

### Release assets

```text
MCW-Launcher-v0.10.0-windows-x64.zip
MCW-Launcher-v0.10.0-windows-x64.zip.sha256
```

### Pre-upload verification

Beta 2 source baseline:

- Full suite: `1055 passed`, `0 failed`, `0 errors`.
- Language parity: `1102` keys in both `en-US` and `vi-VN`.
- Unresolved merge markers: `0`.

After changing metadata to Stable, rerun:

```powershell
python -m tools.release_preflight
python -m pytest test -q
```

Build and publish only when both commands succeed.
