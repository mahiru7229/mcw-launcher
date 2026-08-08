# MCW Launcher v1.2.0

## Tiếng Việt

MCW Launcher **v1.2.0** là bản stable của nhánh Instance Manager 2.0. Bản phát hành này tổng hợp toàn bộ thay đổi đã được kiểm thử qua Beta 1–3 và RC.1–RC.2, đồng thời đóng dấu stable bằng logo **M xanh** mới cho executable và cửa sổ launcher.

### Instance Manager 2.0

- Thêm **Favorite**, **Group** và **Tags** cho instance, tương thích ngược với metadata v1.1.2.
- Instance Library hỗ trợ lọc group, favorites, search theo metadata và sort theo tên, lần chơi gần nhất hoặc Minecraft version.
- Instance Overview và Instance Editor hiển thị metadata tổ chức rõ ràng hơn.

### Unified Content Management

- Installed Content Library hỗ trợ import/kéo-thả local mods, resource packs và shader packs.
- Thêm filter User-added / Modpack-managed, Pinned only, bộ đếm kết quả và ATLauncher provider filter.
- Giữ bảo vệ managed modpack files và dùng chung Core validation/run-lock hiện có.

### Components & Java Runtime

- Instance Editor có trang **Version & Loader** với Minecraft, mod loader/version và Java requirement.
- Hỗ trợ quản lý/repair loader bằng flow hiện có.
- Thêm trang **Java Runtime** với Auto/custom runtime, scan và cài managed Java tương thích.
- Public Core API bổ sung `InstanceRuntimeProfile`; GUI không đọc trực tiếp internal version/settings files.

### Release hardening

- Sửa Instance Overview từng hiển thị literal `\\n` thay vì line break thật.
- Lỗi hết dung lượng hoặc local file-access trong lúc cài không còn bị hiểu nhầm thành manual-download recovery; task kết thúc và release preparing lock để người dùng có thể dọn/xóa instance ngay.
- Giữ toàn bộ dependency/modpack hardening của v1.1.2, bao gồm loader-scoped dependencies, embedded capabilities, manual dependency pause/import/resume và bounded download concurrency.

### Launcher icon

- Thêm logo **M xanh** chính thức cho MCW Launcher v1.2.0.
- PyInstaller dùng `.ico` đa kích thước cho Windows executable.
- One-file build bundle thêm PNG runtime và `QApplication` đặt window/taskbar icon ngay khi khởi động.
- Release preflight kiểm tra icon source, EXE icon binding và runtime icon bundling trước khi build.

### Version metadata

- Launcher runtime: `v1.2.0`
- Update channel: `stable`
- Python distribution metadata: `mcw-core 1.2.0`

## English

MCW Launcher **v1.2.0** is the stable release of the Instance Manager 2.0 line, consolidating Beta 1–3 and RC.1–RC.2. It also introduces the new green hand-drawn **M** as the official launcher icon for the Windows executable and Qt application.

### Highlights

- Instance favorites, groups, tags, richer search/filter/sort and improved instance overview.
- Unified local content import/drag-and-drop plus ownership/pinned filters.
- Version & Loader and Java Runtime pages in Instance Editor, backed by public Core APIs.
- RC storage-lock and overview formatting fixes retained for stable.
- New PyInstaller EXE icon plus bundled Qt window/taskbar icon with release-preflight validation.

### Version metadata

- Launcher runtime: `v1.2.0`
- Update channel: `stable`
- Python distribution metadata: `mcw-core 1.2.0`
