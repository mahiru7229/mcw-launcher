# MCW Launcher v0.6.0 Beta 5

> The first public beta release of the `0.6.x` line, focused on managed Modrinth modpack maintenance, safer memory configuration, responsive layouts, and release-candidate preparation.

## Tiếng Việt

### Modpack update và repair

- Thêm **Repair modpack** trong trang Instances.
- Tải lại manifest `.mrpack` của phiên bản hiện tại và force-verify toàn bộ file được quản lý.
- Khôi phục file bị thiếu hoặc sai checksum, bao gồm downloads, `overrides` và `client-overrides`.
- Kiểm tra và cài phiên bản modpack mới hơn.
- Bỏ qua download/copy khi file đích đã đúng với manifest mới.
- Giữ nguyên file người dùng đã chỉnh sửa khi update, nhưng vẫn theo dõi chúng để scan/repair nhận biết về sau.
- Tạo full backup trước khi thay đổi file đầu tiên.
- Tự rollback file instance, runtime profile và registry metadata nếu update/repair thất bại.
- Không xóa world hoặc file không do modpack quản lý.

### Tối ưu hiệu năng

- Nâng schema `modrinth-pack.json` lên **4**.
- Cache kết quả xác minh theo path, size, `mtime_ns` và checksum mong đợi.
- Không hash lại file managed không đổi ở mỗi lần scan hoặc launch.
- Phát hiện sai kích thước trước khi đọc toàn bộ file.
- Seed cache ngay sau install, update hoặc repair thành công.

### Cấu hình RAM an toàn

- Thay nhập RAM đơn thuần bằng **slider + ô nhập số MB chính xác** cho cả Min và Max.
- Slider và ô số đồng bộ hai chiều.
- Không ép giá trị nhập chính xác như `5000 MB` sang mốc slider gần nhất.
- Ràng buộc động: `Minimum RAM ≤ Maximum RAM ≤ RAM vật lý được phát hiện`.
- Khi hạ Max thấp hơn Min, Min tự hạ theo.
- Cấu hình cũ vượt giới hạn được clamp an toàn ở GUI, controller và settings manager.
- Ô nhập RAM được căn trái để dễ đọc và cân đối với nút tăng/giảm.

### Responsive GUI

- Màn hình `1920×1080` trở lên dùng cửa sổ launcher `1600×900`.
- Màn hình `1366×768` dùng profile gọn `1280×720`.
- Màn hình nhỏ hơn dùng kích thước an toàn theo available screen geometry.
- Compact profile thu gọn sidebar, Session panel, launch bar, card spacing và một số metadata phụ.
- Geometry cũ không còn kéo cửa sổ vượt khỏi màn hình hiện tại.
- Mod Manager, Modrinth, CurseForge và Update dialogs tự co theo vùng màn hình khả dụng.

### Dialog và thông báo lỗi

- `QMessageBox` sử dụng Fusion + palette/stylesheet tương phản cao để tránh lỗi nền trắng và chữ trắng trên một số máy Windows.
- Khi launch hoặc repair thất bại, progress chỉ hiển thị thông báo ngắn yêu cầu mở Logs.
- Toàn bộ lỗi kỹ thuật, dependency mismatch và cảnh báo vẫn được lưu đầy đủ trong Logs.
- Text lỗi nhiều dòng không còn làm vùng progress bị kéo cao bất thường.

### An toàn và tương thích

- Update/repair bị chặn khi instance đang chạy.
- Download tiếp tục dùng checksum, HTTPS host policy, retry, pause/resume, bandwidth limit và progress chung.
- Không thay đổi schema `settings.json` cho `min_memory`/`max_memory`.
- Kênh cập nhật vẫn là `beta`; người dùng stable không tự động bị chuyển sang beta.

### Kiểm thử

```text
744 passed
33 skipped
0 failed
0 errors
```

Các test bị skip là nhóm GUI phụ thuộc PySide6 không có trong môi trường regression đã dùng để chuẩn bị source. GitHub Actions trên Windows sẽ cài đầy đủ dependencies và chạy lại test suite.

---

## English

### Modpack update and repair

- Added **Repair modpack** to the Instances page.
- Downloads the current `.mrpack` manifest and force-verifies every managed file.
- Restores missing or checksum-mismatched downloads, `overrides`, and `client-overrides` files.
- Checks for and installs newer managed modpack versions.
- Skips downloads and disk copies when target files already match the new manifest.
- Preserves user-modified files during updates while keeping them tracked for later scan/repair actions.
- Creates a full safety backup before changing the first file.
- Automatically rolls back instance data, runtime profile, and registry metadata when update/repair fails.
- Does not remove worlds or unmanaged files.

### Performance

- Upgraded `modrinth-pack.json` to schema **4**.
- Stores verification cache entries using path, size, `mtime_ns`, and expected checksums.
- Avoids hashing unchanged managed files on repeated scans and launches.
- Rejects size mismatches before reading full file contents.
- Seeds the cache immediately after successful install, update, or repair operations.

### Safe memory configuration

- Replaced plain RAM entry with a **slider and exact MB input** for both Minimum and Maximum memory.
- Slider and numeric input synchronize in both directions.
- Exact values such as `5000 MB` remain exact instead of being rounded to a slider step.
- Enforces `Minimum RAM ≤ Maximum RAM ≤ detected physical RAM`.
- Lowering Max below Min automatically lowers Min.
- Legacy out-of-range settings are clamped safely in the GUI, controller, and settings manager.
- RAM inputs are left-aligned for clearer spacing beside the step controls.

### Responsive GUI

- `1920×1080` or larger displays use a `1600×900` launcher window.
- `1366×768` displays use the compact `1280×720` profile.
- Smaller displays use a safe size based on available screen geometry.
- Compact mode reduces sidebar, Session panel, launch bar, card spacing, and secondary metadata.
- Saved geometry can no longer restore the window outside the current display.
- Mod Manager, Modrinth, CurseForge, and Update dialogs fit within the available screen area.

### Dialogs and failure presentation

- `QMessageBox` now uses Fusion plus a high-contrast palette and stylesheet to prevent white-background/white-text rendering failures on some Windows systems.
- Launch and repair failures show a short progress message directing the user to Logs.
- Complete technical errors, dependency mismatches, and warnings remain available in Logs.
- Multi-line failure text can no longer expand the progress area abnormally.

### Safety and compatibility

- Update and repair remain blocked while the target instance is running.
- Downloads retain checksum verification, HTTPS host restrictions, retry, pause/resume, bandwidth limiting, and unified progress.
- Existing `settings.json` fields `min_memory` and `max_memory` remain compatible.
- The update channel remains `beta`; stable users are not moved into the beta channel automatically.

### Tests

```text
744 passed
33 skipped
0 failed
0 errors
```

The skipped tests are GUI tests requiring PySide6, which was unavailable in the regression environment used to prepare the source. GitHub Actions installs the full Windows dependency set and reruns the suite.

---

## Release metadata

```python
VERSION = "v0.6.0 Beta 5"
VERSION_ID = "0.6.0-beta.5"
UPDATE_CHANNEL = "beta"
```

```text
Branch: beta/0.6
Tag: v0.6.0-beta.5
Title: MCW Launcher v0.6.0 Beta 5
Asset: MCW-Launcher-v0.6.0-beta.5-windows-x64.zip
Prerelease: yes
```
