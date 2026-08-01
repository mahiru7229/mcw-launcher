# MCW Launcher v0.12.0-beta.3

## Tiếng Việt

### Quilt Loader

- Thêm Quilt như một mod loader độc lập với metadata `loader="quilt"`, không alias instance thành Fabric.
- Dùng Quilt Meta v3 để lấy danh sách Loader, installation metadata và launcher profile theo Minecraft version.
- Hỗ trợ tạo instance, cài Quilt Loader, đổi phiên bản, repair và rollback mod loader.
- Cache catalog/profile có TTL, hỗ trợ dùng cache cũ khi Quilt Meta tạm thời không truy cập được.
- Tải và xác minh các thư viện Quilt/Fabric/Maven qua Download Engine và progress chung.

### Mods và modpack

- Đọc `quilt.mod.json`, dependency Quilt và metadata mod Fabric trong ngữ cảnh tương thích Quilt.
- Tích hợp Quilt với Manage Mods, Modrinth và CurseForge.
- Khi tìm/cài trên Quilt, ưu tiên file gắn nhãn Quilt rồi mới dùng file Fabric tương thích.
- Hỗ trợ `.mrpack` khai báo `quilt-loader` và CurseForge manifest khai báo Quilt.
- Giữ nguyên manual fallback, hash/size verification, safe path và cancel cleanup từ Beta 1.

### LAN Agent và diagnostics

- MCW LAN Agent nhận `loader=quilt` và resolve target qua Fabric intermediary hoặc Quilt Hashed mappings.
- Java smoke test của agent kiểm tra cả NeoForge và Quilt.
- Thêm gói `MCW-Quilt-Diagnostics` gồm profile, inventory mod, game log và LAN Agent log đã lọc dữ liệu nhạy cảm.
- e4mc và LAN hosting cho phép instance Quilt.

### Giao diện

- Thêm Quilt vào Create Instance, Change Loader, Repair, Manage Mods và bộ lọc Modrinth/CurseForge.
- Thêm danh sách Quilt Loader tương thích và bản dịch Việt/Anh.
- Cập nhật metadata sang `v0.12.0-beta.3`, kênh `beta`.

### Giới hạn xác minh

- Quilt Meta, profile merge, repair, provider filters, modpack parser, diagnostics và LAN target resolution được kiểm tra tự động.
- Môi trường phát triển không có DNS cho tiến trình Python, vì vậy chưa thực hiện live install Quilt, live Minecraft launch hoặc live e4mc host/join trong lần build này.

## English

### Quilt Loader

- Added Quilt as an independent mod loader with `loader="quilt"` metadata instead of aliasing instances to Fabric.
- Integrated Quilt Meta v3 for Loader catalogs, installation metadata, and Minecraft-specific launcher profiles.
- Added instance creation, Quilt Loader installation, version switching, repair, and mod-loader rollback.
- Added TTL-backed catalog/profile caching with stale-cache fallback when Quilt Meta is temporarily unavailable.
- Routed Quilt/Fabric/Maven libraries through the shared Download Engine and progress pipeline.

### Mods and modpacks

- Added `quilt.mod.json`, Quilt dependency, and Quilt-context Fabric metadata parsing.
- Integrated Quilt with Manage Mods, Modrinth, and CurseForge.
- Quilt searches and installs rank exact Quilt files before compatible Fabric files.
- Added `.mrpack` `quilt-loader` and CurseForge Quilt manifest support.
- Preserved Beta 1 manual fallback, hash/size verification, safe paths, and cancellation cleanup.

### LAN Agent and diagnostics

- MCW LAN Agent now receives `loader=quilt` and resolves targets through Fabric intermediary or Quilt Hashed mappings.
- The Java agent smoke test covers both NeoForge and Quilt.
- Added `MCW-Quilt-Diagnostics` packages containing the profile, mod inventory, game logs, and filtered LAN Agent logs.
- Enabled e4mc and LAN hosting for Quilt instances.

### Interface

- Added Quilt to Create Instance, Change Loader, Repair, Manage Mods, and Modrinth/CurseForge filters.
- Added compatible Quilt Loader lists and English/Vietnamese translations.
- Updated release metadata to `v0.12.0-beta.3` on the `beta` channel.

### Validation limitation

- Quilt Meta, profile merging, repair, provider filters, modpack parsing, diagnostics, and LAN target resolution are covered by automated tests.
- The development environment did not provide DNS to the Python process, so live Quilt installation, live Minecraft launch, and live e4mc host/join were not performed for this build.
