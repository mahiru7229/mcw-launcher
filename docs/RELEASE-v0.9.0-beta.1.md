# MCW Launcher v0.9.0-beta.1

> Repair Center & Fast Verification

## Tiếng Việt

### Tính năng mới

- Thêm **Trung tâm sửa chữa** cho từng instance.
- Thêm hai chế độ kiểm tra:
  - **Kiểm tra nhanh:** kiểm tra sự tồn tại, kích thước và dùng lại cache xác minh khi file không thay đổi.
  - **Xác minh đầy đủ:** tính lại SHA-1/SHA-256/SHA-512 theo metadata nguồn.
- Hiển thị sức khỏe theo từng thành phần:
  - Minecraft client;
  - libraries và natives;
  - assets;
  - Java runtime;
  - mod loader;
  - file modpack được Modrinth/CurseForge quản lý;
  - MCW LAN Agent;
  - settings và metadata của instance.
- Tạo repair plan trước khi sửa, gồm số vấn đề và dung lượng tải dự kiến.
- Cho phép sửa mục đã chọn hoặc toàn bộ vấn đề có thể tự động sửa.
- Không thay thế world, save hoặc file không do launcher quản lý.
- Lưu cache xác minh và báo cáo lần kiểm tra/sửa gần nhất trong `.mcw` của instance.
- Progress mới cho các bước scan, verify, plan và apply repair.
- Có thể sao chép báo cáo sức khỏe instance vào clipboard.

### File mới trong instance

```text
.mcw/repair-verification-cache.json
.mcw/last-repair-scan.json
.mcw/last-repair-execution.json
```

### Ghi chú Beta

- Full Verification có thể mất thời gian với instance có nhiều assets.
- File CurseForge bị hạn chế phân phối vẫn cần luồng tải thủ công.
- Repair Center bị khóa khi Minecraft của instance đang chạy.

## English

### New features

- Added a per-instance **Repair Center**.
- Added **Quick Check** and **Full Verification** modes.
- Health checks cover the client, libraries, assets, Java, mod loader, managed modpack files, LAN Agent, and instance settings.
- Added repair planning with estimated download size.
- Added selective repair and repair-all actions.
- Added persistent verification cache and scan/execution reports.
- Added dedicated scan, verification, planning, and repair progress stages.
- Added a copyable health report.

### Version information

```text
Version: v0.9.0 Beta 1
Version ID: 0.9.0-beta.1
Release channel: beta
```
