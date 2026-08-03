# MCW Launcher v0.12.0-beta.5

## Tiếng Việt

### Instance-Centered GUI Workflow

`v0.12.0-beta.5` sắp xếp lại launcher theo workflow tập trung vào instance, lấy sự rõ ràng của MultiMC làm tham khảo nhưng vẫn giữ nhận diện pixel-art và Launch Control của MCW Launcher.

### Thay đổi chính

- Màn hình mặc định là **thư viện instance** thay vì trang tổng quan trung gian.
- Hiển thị instance dạng icon, có tìm kiếm theo tên, phiên bản Minecraft và mod loader.
- Thêm toolbar chung cho **Add Instance**, Import, Modrinth Packs, CurseForge Packs và Refresh.
- Thêm panel thao tác nhanh cho instance đang chọn: Launch, Edit Instance, Manage Mods, Instance Settings, Open Folder, Repair, Clone, Export và Delete.
- Double-click instance để launch; menu chuột phải cung cấp các thao tác tương tự.
- Thêm dialog **Add Instance** với hai luồng Minecraft và Modpack.
- Thêm dialog **Edit Instance** với navigation Overview, Mods, Settings, Maintenance và Diagnostics.
- Giữ toàn bộ chức năng cũ trong **Advanced Instance Management** để không làm mất loader switching, backup và modpack lifecycle.
- Rút gọn sidebar về Instances, Accounts, Launcher Settings, Logs và About.
- Giữ Launch Control cố định ở cuối cửa sổ và tiếp tục sử dụng public API của `mcw_core`.

### Kiến trúc

GUI mới không thêm dependency ngược vào core. Mọi workflow vẫn đi qua `mcw_core` / `mcw_core.api`, tiếp tục giữ boundary đã chốt ở Beta 4.

---

## English

### Instance-Centered GUI Workflow

`v0.12.0-beta.5` reorganizes the launcher around instances, using MultiMC's clarity as a workflow reference while retaining MCW Launcher's pixel-art identity and permanent Launch Control.

### Main changes

- Make the **instance library** the default screen instead of an intermediate dashboard.
- Show instances in an icon library with search by name, Minecraft version, and mod loader.
- Add a shared toolbar for Add Instance, Import, Modrinth Packs, CurseForge Packs, and Refresh.
- Add a selected-instance action panel with Launch, Edit Instance, Manage Mods, Instance Settings, Open Folder, Repair, Clone, Export, and Delete.
- Double-click an instance to launch it; the context menu exposes the same common actions.
- Add an **Add Instance** dialog with Minecraft and Modpack workflows.
- Add an **Edit Instance** dialog with Overview, Mods, Settings, Maintenance, and Diagnostics navigation.
- Preserve every previous control under **Advanced Instance Management**, including loader switching, backups, and modpack lifecycle actions.
- Reduce the main sidebar to Instances, Accounts, Launcher Settings, Logs, and About.
- Keep Launch Control permanently visible and continue routing workflows through the public `mcw_core` API.

### Architecture

The reorganized GUI does not add any reverse dependency into the core. All workflows remain behind the `mcw_core` / `mcw_core.api` boundary established in Beta 4.
