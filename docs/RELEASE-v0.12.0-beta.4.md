# MCW Launcher v0.12.0-beta.4

## Tiếng Việt

### Standalone MCW Core Library

- Thêm package công khai `mcw_core`, import được mà không cần PySide6.
- Thêm facade `MCWCore` cho instance, mod loader, Java và launch Minecraft.
- Thêm `CorePaths` để chạy core trong thư mục portable, ứng dụng khác hoặc thư mục tạm khi test.
- Thêm `LaunchRequest`, `LaunchResult`, `InstanceCreateRequest` và `OperationHandle` làm contract công khai.
- GUI chuyển sang import core qua `mcw_core` / `mcw_core.api`, không chọc trực tiếp vào `src.core`.
- Thêm runner không giao diện `tools/core_smoke_launch.py` và command `mcw-core-launch`.
- Thêm `pyproject.toml` để build/install MCW Core như một Python package không chứa GUI.
- Đóng gói MCW LAN Agent trong package core để headless launch vẫn dùng được Fabric, Quilt, Forge và NeoForge LAN support.
- Thêm architectural tests khóa chiều phụ thuộc Core → GUI và GUI → public core API.

### Ghi chú

Beta này tập trung vào ranh giới thư viện và khả năng launch headless. Việc sắp xếp lại workflow và layout GUI sẽ được thực hiện sau khi public core API đã ổn định.

---

## English

### Standalone MCW Core Library

- Added the public `mcw_core` package, importable without PySide6.
- Added the `MCWCore` facade for instances, mod loaders, Java, and Minecraft launch operations.
- Added `CorePaths` for portable roots, external applications, and isolated tests.
- Added public `LaunchRequest`, `LaunchResult`, `InstanceCreateRequest`, and `OperationHandle` contracts.
- Migrated the GUI to import core functionality through `mcw_core` / `mcw_core.api` instead of bypassing the library boundary.
- Added the headless `tools/core_smoke_launch.py` runner and `mcw-core-launch` command.
- Added `pyproject.toml` for building and installing MCW Core without the GUI package.
- Bundled the MCW LAN Agent as core package data so headless Fabric, Quilt, Forge, and NeoForge launches retain LAN support.
- Added architectural tests enforcing Core → GUI and GUI → public-core dependency boundaries.

### Note

This beta focuses on the library boundary and headless launch path. GUI workflow and layout reorganization will follow after the public core API is stable.
