# MCW Launcher v1.3.0

## Tiếng Việt

MCW Launcher **v1.3.0** là bản stable của nhánh **Shared Storage & Cache Lifecycle**. Bản phát hành này hợp nhất Beta 1–3 và bổ sung hardening cuối cho cleanup trên launcher Windows đang được sử dụng thực tế.

### Shared storage và install lifecycle

- Provider-managed binary content được publish vào SHA-256 `ContentStore`; trên NTFS launcher ưu tiên hardlink vào instance và fallback copy khi cần.
- Forge/NeoForge installer reuse client/libraries đã có và staging được cleanup sau install thay vì tích tụ thành cache thứ hai.
- Provider API/metadata cache tiếp tục là một hệ riêng để giảm request; Storage Cleanup không xóa cache API.

### Storage cleanup

- Legacy Storage Cleanup hiển thị chính xác candidate, path, lý do, safety, subtotal theo category và tổng dung lượng vật lý có thể reclaim trước khi xóa.
- Selected candidates được scan/revalidate lại ngay trước deletion.
- Old loader staging, superseded launcher update packages, stale temp, unreferenced provider binaries/content-store blobs và unused Minecraft version JARs được quản lý theo lifecycle riêng.
- Minecraft version cleanup chỉ xóa `cache/versions/<version>/<version>.jar`; JSON/profile metadata vẫn được giữ.

### Final stable hardening

- Launcher Settings có **Unused Minecraft version JAR retention** với mặc định 14 ngày và range 1–365 ngày.
- Cleanup có thể phát hiện thư mục instance cũ bị launcher trước xóa dở khi thư mục không còn `instance.json`, không còn registry reference và chỉ còn `.mcw` / `crash-reports`.
- Storage analysis có progress profile riêng nên không còn hiển thị nhầm 100% và completion detail của Update Check trước đó.
- Instance deletion vẫn chờ runtime finalization để `.mcw` / `crash-reports` không bị tạo lại sau khi xóa.

### Version metadata

- Launcher runtime: `v1.3.0`
- Update channel: `stable`
- Python distribution metadata: `mcw-core 1.3.0`

## English

MCW Launcher **v1.3.0** is the stable Shared Storage & Cache Lifecycle release. It consolidates Beta 1–3 and adds final cleanup hardening for real Windows launcher installations.

### Highlights

- SHA-256 ContentStore with NTFS hardlink reuse for managed immutable content.
- Forge/NeoForge staging cleanup and reuse of existing canonical artifacts.
- Provider API cache remains explicitly separate and protected from binary cleanup.
- Reference-aware cleanup preview with exact paths, reasons, categories and reclaimable bytes.
- Configurable 1–365 day retention for unused Minecraft version JARs (14 days by default).
- Conservative cleanup of incomplete legacy instance folders containing only `.mcw` / `crash-reports` and no metadata/registry reference.
- Dedicated storage-analysis progress lifecycle fixes stale 100%/update-check detail in the launcher UI.

### Version metadata

- Launcher runtime: `v1.3.0`
- Update channel: `stable`
- Python distribution metadata: `mcw-core 1.3.0`
