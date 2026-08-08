# MCW Launcher v1.3.0-beta.1

## Tiếng Việt

MCW Launcher **v1.3.0-beta.1** mở đầu nhánh v1.3 bằng việc thay đổi nền tảng cài đặt và vòng đời lưu trữ. Mục tiêu của Beta 1 là giảm dữ liệu bị copy/build lặp, dọn staging đúng lúc và cung cấp đường migrate an toàn cho cache còn tồn đọng từ các bản launcher trước.

### Shared content storage

- Thêm `ContentStore` content-addressed theo SHA-256 cho binary artifact được provider quản lý.
- Mod tải từ CurseForge/Modrinth được publish vào shared store và ưu tiên NTFS hardlink vào instance; nếu filesystem không hỗ trợ hardlink, launcher tự fallback về copy.
- Local user import vẫn giữ copy semantics cũ, không tự biến file người dùng thành managed shared content.
- Preview cleanup tính **dung lượng vật lý có thể giải phóng**, không báo sai dung lượng khi một artifact vẫn còn hardlink ở nơi khác.

### Forge / NeoForge staging lifecycle

- Minecraft client JAR và base libraries được reuse bằng hardlink/copy fallback khi chuẩn bị Forge/NeoForge installer staging.
- Generated libraries sau installer được publish về canonical global `libraries` thay vì giữ thêm một bản staging lâu dài.
- Forge và NeoForge staging được cleanup bằng `finally` trên cả success lẫn failure.
- Forge và NeoForge vẫn giữ pipeline riêng; NeoForge không được xử lý như Forge alias.

### API cache và binary content được tách rõ

- Provider API/metadata cache được đặt tên rõ thành `CurseForgeApiCache`, `FTBApiCache`, `ATLauncherApiCache` và các client/controller dùng `api_cache_status()` / `clear_api_cache()`.
- API cache của provider tiếp tục được giữ để giảm request mạng; đặc biệt CurseForge API cache không bị Legacy Storage Cleanup hoặc ContentStore GC đụng tới.
- Compatibility aliases cũ vẫn còn để tránh phá caller hiện có trong chu kỳ beta.
- Downloaded binary artifacts dùng lifecycle riêng thông qua `ContentStore` và provider artifact paths.

### Legacy Storage Migration & Cleanup

- Thêm `LegacyStorageMigrationService` để phát hiện dữ liệu còn tồn đọng từ pre-v1.3:
  - Forge/NeoForge installer staging cũ;
  - launcher update packages cũ;
  - Minecraft/loader version cache không còn instance tham chiếu;
  - CurseForge/Modrinth binary artifact version không còn được instance tham chiếu;
  - stale `.part`/temporary/update staging;
  - orphan ContentStore blobs.
- Minecraft version cleanup theo reference graph và `inheritsFrom`; metadata instance không đọc được sẽ làm cleanup bảo thủ hơn thay vì đoán rồi xóa.
- Provider binary cleanup dùng provider registry và pack metadata references và không bao gồm Provider API metadata cache.
- Retention/grace trong Beta 1: loader staging 1 giờ; stale temp 7 ngày; unused versions và unreferenced provider/content-store artifacts 14 ngày.

### Cleanup preview và startup notification

- Launcher Settings có mục **Storage** với `Notify about old cache/storage` mặc định bật và nút **Review old storage**.
- Startup chỉ chạy lightweight probe; không hash toàn ổ đĩa và không xóa file tự động.
- Khi tìm thấy legacy candidates, launcher hiển thị thông báo non-destructive với Review / Later / Don't show again.
- Cleanup dialog hiển thị từng candidate, path, category, reason, safety, file/folder counts, subtotal theo category và tổng dung lượng vật lý có thể giải phóng.
- Người dùng có thể bỏ chọn từng item/category trước khi xác nhận.
- Trước khi delete, Core scan/revalidate lại toàn bộ selected candidates; item thay đổi hoặc trở thành referenced sẽ bị skip.
- Kết quả cuối báo actual reclaimed bytes, removed, skipped và failures.

### Protected data

Legacy cleanup không được phép xóa:

- Provider API/metadata caches;
- `instances/`, saves, configs, worlds, screenshots và instance state;
- accounts;
- Java runtimes;
- shared Minecraft assets/libraries;
- artifact còn active/referenced hoặc chưa qua safety retention.

### Version metadata

- Launcher runtime: `v1.3.0-beta.1`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.3.0b1`

## English

MCW Launcher **v1.3.0-beta.1** starts the v1.3 line with a shared-storage and cache-lifecycle foundation. It reduces persistent installer/provider duplication, cleans temporary loader staging deterministically, and adds a reference-aware migration path for storage left by pre-v1.3 builds.

### Highlights

- SHA-256 `ContentStore` for immutable provider binaries with NTFS hardlink reuse and copy fallback.
- Forge/NeoForge installer staging reuses canonical inputs and is always removed after success or failure.
- Provider API/metadata caches are explicitly separated from downloaded binary content and are protected from legacy cleanup.
- Reference-aware cleanup for old loader staging, superseded launcher updates, unused version profiles, unreferenced provider binaries, stale temporary data and orphan shared blobs.
- Lightweight startup notification (enabled by default) plus a manual **Review old storage** action.
- Exact cleanup preview with paths, reasons, safety, counts, per-category totals and physical reclaimable bytes; selected candidates are revalidated immediately before deletion.

### Version metadata

- Launcher runtime: `v1.3.0-beta.1`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.3.0b1`
