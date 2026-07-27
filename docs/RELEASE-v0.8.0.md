# MCW Launcher v0.8.0

## Tiếng Việt

`v0.8.0` là bản Stable hoàn thiện nhánh LAN hosting mới, giao diện settings được nhóm lại và vòng đời progress nhất quán hơn.

### LAN hosting

- Thêm **MCW LAN Agent** cho chế độ Private LAN Offline Mode mà không thay thế Mojang Authlib.
- Tách riêng chính sách xác thực khỏi phương thức kết nối: LAN/VPN/direct port/custom relay hoặc e4mc.
- Resolve target runtime theo Fabric intermediary mappings và Forge SRG mappings.
- Giữ nguyên chế độ Microsoft-only; agent chỉ được gắn khi người dùng chủ động chọn Microsoft + Offline.
- Bổ sung log riêng, kiểm tra SHA-256 và fail-safe khi target không thể resolve hoặc patch.

### Giao diện và bản dịch

- Nhóm Launcher Settings và Instance Settings thành các section chức năng rõ ràng.
- Tự reflow từ hai cột sang một cột trên profile compact cho màn hình 1366×768.
- Sửa bố cục **Cửa sổ game** để nhãn Chiều rộng/Chiều cao nằm trực tiếp phía trên ô nhập tương ứng.
- Hoàn thiện parity giữa language pack `en-US` và `vi-VN`.
- Giữ Qt dialog dùng palette tối để tránh lỗi chữ trắng trên nền trắng.

### Progress và độ ổn định

- Chuẩn hóa trạng thái tác vụ thành `RUNNING`, `SUCCEEDED`, `FAILED` và `CANCELLED`.
- Lỗi giữa chừng không còn để progress treo ở phần trăm cũ.
- Thêm progress cho Java discovery, kiểm tra cập nhật mod/modpack, repair, import/export, LAN hosting và launcher update.
- Sửa lỗi chọn instance có thể gọi refresh trước khi `LaunchControlWidget._launch_active` được khởi tạo.
- Khôi phục nút Launch/Cancel đúng trạng thái sau hoàn tất, thất bại, hủy hoặc game thoát.

### Version metadata

```python
VERSION = "v0.8.0"
VERSION_ID = "0.8.0"
UPDATE_CHANNEL = "stable"
```

### Kiểm thử trước release

```text
833 passed, 48 skipped
Release preflight passed for v0.8.0 (stable).
Language parity: 919 keys in en-US and vi-VN.
Unresolved merge markers: 0
```

Các test GUI phụ thuộc PySide6 bị skip trong môi trường Linux tối giản; cần chạy lại toàn bộ suite và kiểm tra trực quan trên Windows trước khi đóng gói EXE chính thức.

---

## English

`v0.8.0` is the Stable release completing the new LAN-hosting flow, grouped settings interface, and consistent task-progress lifecycle.

### LAN hosting

- Add the **MCW LAN Agent** for Private LAN Offline Mode without replacing Mojang Authlib.
- Keep authentication policy independent from the connection transport: LAN/VPN/direct port/custom relay or e4mc.
- Resolve runtime targets through Fabric intermediary mappings and Forge SRG mappings.
- Preserve Microsoft-only mode; the agent is attached only when Microsoft + Offline is explicitly selected.
- Add a dedicated log, SHA-256 verification, and fail-safe behavior when a target cannot be resolved or patched.

### Interface and localization

- Group Launcher Settings and Instance Settings into clear functional sections.
- Reflow from two columns to one column on the compact 1366×768 display profile.
- Fix the **Game window** layout so Width and Height labels stay directly above their matching inputs.
- Complete `en-US` and `vi-VN` language-pack parity.
- Keep Qt dialogs on the launcher dark palette to avoid white text on white backgrounds.

### Progress and stability

- Standardize task states around `RUNNING`, `SUCCEEDED`, `FAILED`, and `CANCELLED`.
- Mid-operation failures no longer leave progress running at an outdated percentage.
- Add progress for Java discovery, mod/modpack update checks, repair, import/export, LAN hosting, and launcher updates.
- Fix instance selection refreshing the launch button before `LaunchControlWidget._launch_active` was initialized.
- Restore the Launch/Cancel control correctly after completion, failure, cancellation, or game exit.

### Version metadata

```python
VERSION = "v0.8.0"
VERSION_ID = "0.8.0"
UPDATE_CHANNEL = "stable"
```

### Release validation

```text
833 passed, 48 skipped
Release preflight passed for v0.8.0 (stable).
Language parity: 919 keys in en-US and vi-VN.
Unresolved merge markers: 0
```

GUI tests requiring PySide6 are skipped in the minimal Linux validation environment; rerun the full suite and perform a visual check on Windows before packaging the official EXE.
