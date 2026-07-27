# MCW Launcher v0.8.0 Beta 3

## Tiếng Việt

`v0.8.0-beta.3` là đợt hoàn thiện giao diện, bản dịch và tiến trình tác vụ trước khi cân nhắc phát hành `v0.8.0` Stable.

### Giao diện được nhóm lại

- **Launcher Settings** được chia thành các nhóm: Chung, Tải xuống và nguồn nội dung, Môi trường chạy và cập nhật, Giao diện.
- **Instance Settings** được chia thành: Instance đang chọn, Môi trường chạy và hiển thị, Chơi mạng và tải xuống, Nâng cao.
- Các card tự chuyển từ bố cục hai cột sang một cột trên màn hình compact để giữ khả năng sử dụng ở 1366×768.
- Thêm component `SettingsSection` dùng chung để spacing, tiêu đề và cách reflow nhất quán giữa các trang settings.

### Progress nhất quán hơn

- Thêm trạng thái terminal rõ ràng: `SUCCEEDED`, `FAILED`, `CANCELLED`.
- Tác vụ thất bại không còn để progress ở trạng thái đang chạy hoặc phần trăm cũ.
- Check for Update của modpack báo từng bước đọc registry, project, phiên bản hiện tại, danh sách phiên bản và so sánh kết quả.
- Kiểm tra cập nhật mod báo tiến độ theo số project Modrinth được theo dõi.
- Quét Java hiển thị lần lượt JAVA_HOME, PATH, Program Files, Windows Registry, managed runtimes và bước kiểm tra từng bản Java tìm thấy.
- Các tác vụ mod/modpack, backup, import/export, repair, LAN hosting và launcher update có thông báo hoàn tất hoặc thất bại thống nhất trên launch progress panel.

### Bản dịch

- Bổ sung toàn bộ chuỗi mới cho `en-US` và `vi-VN`.
- Mở rộng kiểm thử static GUI text để bao gồm section component mới.
- Giữ parity key và placeholder giữa hai language pack.

### LAN Agent

- Giữ nguyên các sửa lỗi đã xác nhận trong Beta 2 cho Fabric intermediary mappings và Forge SRG mappings.
- MCW LAN Agent vẫn chỉ được gắn khi instance chọn Private LAN Offline Mode.

## English

`v0.8.0-beta.3` is the GUI, localization, and task-progress polish pass before considering `v0.8.0` Stable.

### Grouped settings interface

- **Launcher Settings** is grouped into General, Downloads and content sources, Runtime and updates, and Appearance.
- **Instance Settings** is grouped into Selected instance, Runtime and display, Multiplayer and downloads, and Advanced.
- Cards automatically reflow from two columns to one column in compact layouts.
- Added a reusable `SettingsSection` component for consistent spacing, headings, and responsive behavior.

### Consistent progress lifecycle

- Added explicit terminal states: `SUCCEEDED`, `FAILED`, and `CANCELLED`.
- Failed operations no longer leave the progress panel running at an outdated percentage.
- Modpack update checks now report metadata-loading and comparison steps.
- Mod update checks report progress across tracked Modrinth projects.
- Java scans report each discovery source and each detected runtime inspection.
- Mod/modpack, backup, import/export, repair, LAN hosting, and launcher-update tasks now present consistent completion or failure states.

### Localization

- Added all new messages to `en-US` and `vi-VN`.
- Extended static GUI text coverage to the new section component.
- Preserved translation-key and placeholder parity.

### LAN Agent

- Preserves the verified Beta 2 Fabric intermediary and Forge SRG mapping fixes.
- The MCW LAN Agent is attached only when Private LAN Offline Mode is selected.
