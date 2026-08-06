# MCW Launcher v1.1.1-beta.4

## Tiếng Việt

MCW Launcher **v1.1.1-beta.4** đơn giản hóa OptiFine thành luồng **chọn file và cài đặt**. Launcher không còn tải hoặc hiển thị danh sách phiên bản OptiFine trực tuyến.

### Thay đổi chính

- Xóa version selector, tùy chọn preview, nút refresh và mọi request metadata OptiFine khỏi giao diện.
- Người dùng chỉ cần chọn file JAR OptiFine chính thức đã tải.
- MCW nhận diện Minecraft version, OptiFine edition/build và trạng thái preview từ tên file gốc, ví dụ `OptiFine_1.12.2_HD_U_G5.jar` hoặc `preview_OptiFine_1.20.1_HD_U_I7_pre1.jar`.
- File có Minecraft version khác instance bị chặn trước khi tạo/cài.
- Core xác minh lại phiên bản, kích thước, cấu trúc ZIP/JAR, Java manifest và class OptiFine trước khi commit.
- **Create Instance**:
  - Vanilla cài OptiFine dưới dạng standalone component/profile.
  - Forge cài OptiFine dưới dạng mod được quản lý.
- **Instance hoặc modpack Forge đã tồn tại** có thể dùng **Manage OptiFine** để chọn JAR và cài trực tiếp vào `mods/`.
- Fabric, Quilt và NeoForge vẫn không được cài trực tiếp trong flow này.
- Hỗ trợ Repair, Uninstall, transaction rollback, provenance và chính sách export thủ công của Beta 3 được giữ nguyên.
- Nhận diện cả file stable và file `preview_OptiFine_*`; không cần tra cứu catalog online.

### Quy tắc an toàn

- Tên file phải giữ nguyên định dạng OptiFine để MCW xác định Minecraft version.
- Một instance không thể có hai OptiFine JAR được quản lý cùng lúc.
- File JAR OptiFine không được nhúng vào portable/full-offline export.
- Repair chỉ dùng bản cache có SHA-256 đúng; nếu cache mất hoặc bị sửa, người dùng phải chọn lại JAR chính thức.

### Phiên bản

- Launcher runtime: `v1.1.1-beta.4`
- Python distribution metadata: `1.1.1b4`
- MCW Core source/wheel riêng: chưa phát hành lại; sẽ đồng bộ khi `v1.1.1` stable.

---

## English

MCW Launcher **v1.1.1-beta.4** simplifies OptiFine into an **import-and-install** workflow. The launcher no longer fetches or displays an online OptiFine version catalog.

### Main changes

- Removes the OptiFine version selector, preview toggle, refresh button, and all OptiFine metadata requests from the UI.
- Users only select the official OptiFine JAR they already downloaded.
- MCW detects the Minecraft version, OptiFine edition/build, and preview state from the original filename, such as `OptiFine_1.12.2_HD_U_G5.jar` or `preview_OptiFine_1.20.1_HD_U_I7_pre1.jar`.
- A JAR targeting a different Minecraft version is rejected before creation or installation.
- Core validates the version again together with file size, ZIP/JAR structure, Java manifest, and expected OptiFine classes before committing changes.
- **Create Instance**:
  - Vanilla installs OptiFine as a standalone component/profile.
  - Forge installs OptiFine as a managed mod.
- Existing **Forge instances and modpacks** can use **Manage OptiFine** to import the JAR directly into `mods/`.
- Fabric, Quilt, and NeoForge remain unsupported by this direct workflow.
- Repair, Uninstall, transactional rollback, provenance, and manual-only export policy from Beta 3 remain intact.
- Both stable and `preview_OptiFine_*` files are recognized without an online catalog.

### Safety rules

- The original OptiFine filename must be preserved so MCW can determine the Minecraft version.
- An instance cannot contain two MCW-managed OptiFine JARs at the same time.
- OptiFine JARs are never embedded in portable or full-offline exports.
- Repair only uses a cached source with a matching SHA-256; otherwise the user must select the official JAR again.

### Versions

- Launcher runtime: `v1.1.1-beta.4`
- Python distribution metadata: `1.1.1b4`
- Separate MCW Core source/wheel: not republished until `v1.1.1` stable.
