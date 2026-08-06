# MCW Launcher v1.1.1-beta.3

## Tiếng Việt

MCW Launcher **v1.1.1-beta.3** bổ sung tích hợp OptiFine theo mô hình component tùy chọn. OptiFine không bị coi là mod loader chính: instance vẫn là Vanilla hoặc Forge, còn OptiFine được quản lý độc lập với hai chế độ cài đặt.

### Tính năng mới

- Đọc danh sách phiên bản từ trang tải OptiFine chính thức, lọc theo Minecraft version và phân biệt stable/preview.
- Cache metadata 6 giờ và dùng cache cũ khi trang chính thức tạm thời không truy cập được.
- Thêm lựa chọn **Install OptiFine** ngay khi tạo instance.
- Thêm nút **Manage OptiFine** cho instance hiện có.
- Vanilla dùng chế độ **Standalone profile**.
- Minecraft Forge dùng chế độ **Forge mod** trong thư mục `mods`.
- Fabric, Quilt và NeoForge chưa được bật cài trực tiếp vì chưa có contract tương thích chính thức ổn định trong flow này.
- Người dùng mở trang tải chính thức và chọn JAR đã tải; launcher không nhúng hoặc phân phối lại OptiFine.
- Kiểm tra tên file, kích thước, cấu trúc ZIP/JAR và class OptiFine trước khi cài.
- Phân loại tương thích thành `compatible`, `warning`, `blocked` hoặc `unknown`; build được OptiFine đánh dấu `Forge N/A` sẽ bị chặn ở chế độ Forge mod.
- Lưu registry tại `.mcw/optifine.json`, hash SHA-256/SHA-1, đường dẫn nguồn cache và file/profile được quản lý.
- Hỗ trợ đổi phiên bản, Repair và Uninstall; chỉ xóa file do MCW quản lý.
- Standalone installer chạy trong staging riêng, nhập profile và libraries sau khi trình cài chính thức hoàn tất, rồi commit profile vào instance.
- Mọi thay đổi trong instance đi qua journal + backup; lỗi hoặc launcher bị đóng giữa chừng sẽ rollback registry, profile, mod và provenance về trạng thái trước đó.
- Launch pipeline tự áp dụng profile OptiFine standalone hoặc kiểm tra integrity của OptiFine Forge mod.
- Portable export luôn ghi OptiFine thành manual-download entry và không nhúng JAR OptiFine, kể cả full-offline mode.

### Lưu ý test

Chế độ Forge mod được kiểm thử tự động. Chế độ standalone cần smoke test trên Windows với JAR OptiFine thật vì nó mở trình cài Java chính thức để người dùng bấm **Install**.

### Phiên bản

- Launcher runtime: `v1.1.1-beta.3`
- Python distribution metadata: `1.1.1b3`
- MCW Core source/wheel riêng: chưa phát hành lại; sẽ đồng bộ khi `v1.1.1` stable.

---

## English

MCW Launcher **v1.1.1-beta.3** adds OptiFine as an optional component instead of treating it as a primary mod loader. Instances remain Vanilla or Forge while OptiFine is managed independently in two installation modes.

### New features

- Reads versions from the official OptiFine downloads page, filters by Minecraft version, and distinguishes stable/preview builds.
- Caches metadata for six hours and falls back to stale cache during temporary outages.
- Adds **Install OptiFine** to instance creation.
- Adds **Manage OptiFine** to existing instances.
- Vanilla uses a **Standalone profile**.
- Minecraft Forge uses **Forge mod** mode in `mods`.
- Fabric, Quilt, and NeoForge direct installation remain disabled until this workflow has a stable verified compatibility contract.
- Users open the official download page and select the downloaded JAR; MCW does not bundle or redistribute OptiFine.
- Validates filename, size, ZIP/JAR structure, and expected OptiFine classes before installation.
- Classifies compatibility as `compatible`, `warning`, `blocked`, or `unknown`; builds marked `Forge N/A` by OptiFine are blocked from Forge-mod installation.
- Stores `.mcw/optifine.json` with SHA-256/SHA-1, source cache path, and managed file/profile paths.
- Supports version replacement, Repair, and Uninstall while deleting only MCW-managed files.
- The standalone installer runs in isolated staging, imports the generated profile and libraries after the official installer completes, then commits the profile to the instance.
- Instance mutations use a journal and backup; failures or an interrupted launcher restore the previous registry, profile, mod, and provenance state.
- The launch pipeline applies the standalone profile or validates the managed Forge mod integrity.
- Portable export always represents OptiFine as a manual-download entry and never embeds the OptiFine JAR, including full-offline mode.

### Testing note

Forge mod mode is covered by automated tests. Standalone mode still requires a Windows smoke test with a real OptiFine JAR because it opens the official Java installer for the user to press **Install**.

### Versions

- Launcher runtime: `v1.1.1-beta.3`
- Python distribution metadata: `1.1.1b3`
- Separate MCW Core source/wheel: not republished until `v1.1.1` stable.
