# MCW Launcher v0.5.0 Beta 7

> Runtime & Repair Update

---

## Tiếng Việt

### Theo dõi vòng đời Minecraft

- Theo dõi Minecraft từ lúc process được tạo cho tới khi game đóng.
- Ghi nhận PID, exit code, thời gian bắt đầu, thời gian kết thúc và tổng thời gian chơi.
- Phân biệt game đóng bình thường với crash.
- Phát hiện crash report mới kể cả khi Java trả exit code `0`.
- Cập nhật `last_played` và tổng playtime trong metadata instance.
- Lưu tối đa 50 phiên chạy gần nhất tại `.mcw/runtime-history.json`.

### Crash và log

Trang Logs có thêm:

- **Open latest game log**;
- **Open latest crash report**.

Launch Control tự chuyển sang trạng thái **FINISHED** hoặc **CRASHED** sau khi game đóng.

### Repair Instance

Thêm nút **Repair instance** trong trang Instances.

Repair sẽ kiểm tra:

- version metadata;
- client JAR;
- libraries;
- assets;
- natives;
- Fabric Loader/profile;
- Java runtime.

Repair không xóa world, mod, resource pack, shader, screenshot hoặc settings của instance.

### Metadata an toàn hơn

- Metadata được ghi atomic.
- Nâng `metadata_version` lên `2`.
- Giữ lại notes, icon, playtime, dữ liệu Modrinth và các field mở rộng khi đổi tên hoặc đổi loader.

---

## English

### Minecraft lifecycle monitoring

- Monitor Minecraft from process creation until exit.
- Record PID, exit code, start time, end time, and session duration.
- Distinguish normal exits from crashes.
- Detect newly generated crash reports even when Java returns exit code `0`.
- Update `last_played` and accumulated play time in instance metadata.
- Keep the latest 50 sessions in `.mcw/runtime-history.json`.

### Crash and log tools

The Logs page now includes:

- **Open latest game log**;
- **Open latest crash report**.

Launch Control changes to **FINISHED** or **CRASHED** after the game exits.

### Repair Instance

Added **Repair instance** to the Instances page.

Repair verifies:

- version metadata;
- client JAR;
- libraries;
- assets;
- natives;
- Fabric Loader/profile;
- Java runtime.

Worlds, mods, resource packs, shaders, screenshots, and instance settings are preserved.

### Safer metadata

- Atomic metadata writes.
- `metadata_version` upgraded to `2`.
- Notes, icons, play time, Modrinth data, and custom extension fields survive rename and loader changes.

---

## Release information

```text
Version: v0.5.0-beta.7
Channel: Beta / Pre-release
Platform: Windows x64
License: MIT
```

Suggested asset:

```text
MCW-Launcher-v0.5.0-beta.7-windows-x64.zip
```
