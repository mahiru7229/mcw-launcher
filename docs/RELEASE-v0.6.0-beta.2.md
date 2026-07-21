# MCW Launcher v0.6.0 Beta 2

> Beta 2 focuses on Forge recovery and local mod management while CurseForge remains available only when an API key is configured.

---

## Tiếng Việt

### Forge Repair

- Reinstall Forge bằng staging riêng và chỉ thay profile cache sau khi cài thành công.
- Tải và kiểm tra lại toàn bộ Forge libraries trong cùng tác vụ Repair.
- Kiểm tra Minecraft version, Forge version, main class, Forge library, kích thước và SHA-1.
- Nếu installer, download hoặc verification lỗi, profile Forge cũ được khôi phục tự động.
- Ghi log riêng tại `cache/modloaders/forge/logs/forge-repair-<minecraft>-<forge>.log`.
- Không thay đổi `mods/`, `config/`, `saves/`, resource packs hoặc settings của instance.
- Hỗ trợ cả installer Forge hiện đại và installer legacy như Minecraft 1.8.9.

### Manual Mod Manager

- Thêm mod `.jar` bằng file picker hoặc kéo-thả vào cửa sổ Mod Manager.
- Bật, tắt và xóa mod thủ công.
- Đọc metadata từ:
  - `fabric.mod.json`
  - `META-INF/mods.toml`
  - `META-INF/neoforge.mods.toml`
  - `mcmod.info`
- Hiển thị loader và định dạng metadata trong bảng/details.
- Phát hiện mod Fabric trong Forge instance và ngược lại.
- Phát hiện NeoForge mod trong Forge instance.
- Phát hiện mod ID trùng trước khi ghi file.
- Đọc dependency bắt buộc và dependency tùy chọn của Forge.
- Hỗ trợ version range kiểu Forge/Maven như `[47,)` và `[1.20.1,1.21)`.
- Hỗ trợ metadata mod Forge legacy từ các phiên bản cũ.
- Copy file qua `.part` và chỉ thay file đích sau khi JAR đã được xác nhận hợp lệ.

### CurseForge trong Beta 2

- Nút CurseForge được ẩn khi chưa có API key.
- Launcher không gọi CurseForge API khi integration chưa được cấu hình.
- Phần CurseForge hiện có vẫn được giữ lại để tiếp tục sau khi API key được duyệt.

### Version

```python
VERSION = "v0.6.0 Beta 2"
VERSION_ID = "0.6.0-beta.2"
UPDATE_CHANNEL = "beta"
```

### Kiểm thử

```text
702 passed
32 skipped
0 failed
0 errors
```

---

## English

### Forge Repair

- Reinstalls Forge in a separate staging directory and only replaces the cached profile after installation succeeds.
- Downloads and verifies Forge libraries during the same Repair task.
- Validates the Minecraft version, Forge version, main class, Forge library, file size, and SHA-1.
- Restores the previous Forge profile automatically if installation, download, or verification fails.
- Writes a dedicated repair log to `cache/modloaders/forge/logs/forge-repair-<minecraft>-<forge>.log`.
- Does not modify instance mods, configs, saves, resource packs, or settings.
- Supports both modern Forge installers and legacy installers such as Minecraft 1.8.9.

### Manual Mod Manager

- Adds local `.jar` files through the file picker or drag and drop.
- Enables, disables, and removes local mods.
- Reads metadata from Fabric, modern Forge, NeoForge, and legacy Forge formats.
- Displays the detected loader and metadata format.
- Detects loader mismatches and duplicate mod IDs.
- Reads required and optional Forge dependencies.
- Supports Forge/Maven version ranges such as `[47,)` and `[1.20.1,1.21)`.
- Uses a temporary `.part` copy before replacing an installed mod.

### CurseForge in Beta 2

- CurseForge actions are hidden when no API key is configured.
- The launcher does not call the CurseForge API until the integration is configured.
- Existing CurseForge groundwork remains available for later development.

### Testing

```text
702 passed
32 skipped
0 failed
0 errors
```

---

## GitHub Release

**Tag:**

```text
v0.6.0-beta.2
```

**Title:**

```text
MCW Launcher v0.6.0 Beta 2
```

Mark the release as a pre-release and upload only the Windows ZIP plus its SHA-256 file.
