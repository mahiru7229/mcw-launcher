# MCW Launcher v0.10.0 Beta 2

> Opt-in test build for global instance defaults and settings-aware `.mcwpack` imports. `v0.9.0` remains the default Stable release.

---

## Tiếng Việt

### Setting tổng cho instance mới

- Launcher Settings có bảng **Cài đặt mặc định cho instance** dùng chung một schema với `settings.json` của từng instance.
- Có thể đặt Java, RAM tối thiểu/tối đa, cửa sổ/toàn màn hình, LAN authentication/connection, chính sách Modrinth/CurseForge, Forge preflight, JVM arguments và game arguments.
- Mọi instance Vanilla, Fabric hoặc Forge được tạo mới đều sao chép bộ mặc định tại thời điểm tạo.
- Instance do modpack Modrinth hoặc CurseForge tạo cũng đi qua cùng luồng nên không có cấu hình riêng bị lệch.
- Các instance đã tồn tại không bị thay đổi; `settings.json` của từng instance vẫn có độ ưu tiên cao nhất.

### Import `.mcwpack`

- Launcher kiểm tra metadata và setting của gói trước khi giải nén.
- Hộp thoại import cho chọn một trong ba chế độ:
  1. dùng setting tổng của launcher và ghi đè setting trong gói;
  2. giữ nguyên setting trong `.mcwpack`;
  3. mở đầy đủ setting của gói để xem và chỉnh trước khi import.
- Nếu gói không có `settings.json`, tùy chọn giữ setting trong gói sẽ bị tắt và launcher dùng setting tổng.
- Setting được chuẩn hóa theo giới hạn RAM vật lý và các policy hợp lệ trước khi ghi atomically.
- Override của modpack không được ghi đè `instance.json`, `settings.json` hoặc thư mục `.mcw` do launcher quản lý.

### Phiên bản

```text
VERSION = v0.10.0 Beta 2
VERSION_ID = 0.10.0-beta.2
UPDATE_CHANNEL = beta
```

### Checklist cho tester

1. Đổi Java/RAM/cửa sổ trong Launcher Settings rồi tạo một instance Vanilla.
2. Cài một modpack Modrinth và một modpack CurseForge; kiểm tra `settings.json` mới.
3. Export một instance thành `.mcwpack`, sau đó thử cả ba chế độ import bằng các tên instance khác nhau.
4. Xác nhận instance cũ không đổi sau khi sửa setting tổng.
5. Thử đổi ngôn ngữ Việt/Anh và mở lại hai hộp thoại setting.
6. Backup world quan trọng trước khi thử bản Beta.

Chạy regression:

```powershell
python -m pytest test -q
python -m tools.release_preflight
```

Kết quả source Beta 2: `1055 passed`, `0 failed`, `0 errors`.

---

## English

### Defaults for new instances

- Launcher Settings now contains **Default instance settings** backed by the same schema as each instance's `settings.json`.
- Configure Java, minimum/maximum memory, window/fullscreen, LAN authentication/connection, Modrinth/CurseForge policies, Forge preflight, JVM arguments, and game arguments.
- Every newly created Vanilla, Fabric, or Forge instance copies the defaults at creation time.
- Modrinth and CurseForge modpack installers use the same creation path, preventing provider-specific settings drift.
- Existing instances are never rewritten; each instance's own `settings.json` remains authoritative.

### `.mcwpack` import

- The launcher inspects package metadata and settings before extraction.
- The import dialog offers three modes:
  1. apply launcher defaults and overwrite package settings;
  2. preserve settings stored in the `.mcwpack`;
  3. open the complete package settings for review and editing before import.
- When a package has no `settings.json`, preserve mode is disabled and launcher defaults are applied.
- Settings are normalized against physical-memory limits and valid policy values before atomic persistence.
- Modpack override layers cannot replace launcher-owned `instance.json`, `settings.json`, or `.mcw` paths.

### Version

```text
VERSION = v0.10.0 Beta 2
VERSION_ID = 0.10.0-beta.2
UPDATE_CHANNEL = beta
```

### Tester checklist

1. Change Java/memory/window defaults in Launcher Settings, then create a Vanilla instance.
2. Install one Modrinth and one CurseForge modpack and inspect each new `settings.json`.
3. Export an instance as `.mcwpack`, then test all three import modes with different instance names.
4. Confirm existing instances do not change after editing global defaults.
5. Switch between Vietnamese and English and reopen both settings dialogs.
6. Back up important worlds before testing the Beta.

Regression commands:

```powershell
python -m pytest test -q
python -m tools.release_preflight
```

Beta 2 source result: `1055 passed`, `0 failed`, `0 errors`.
