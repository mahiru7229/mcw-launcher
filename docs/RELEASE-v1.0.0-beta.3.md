# MCW Launcher v1.0.0-beta.3

## Tiếng Việt

Beta 3 mở rộng Content Browser thành hệ thống quản lý **Resource Packs** và **Shader Packs** theo từng instance, đồng thời hoàn thiện cụm Launch Control để các nút Launch, Pause và Cancel sử dụng trọn vùng điều khiển theo cả hai chiều.

### Điểm mới

- Thêm **Quản lý gói nội dung** vào Instance Workspace và menu chuột phải.
- Thêm hai thư viện riêng cho Resource Packs và Shader Packs đã cài.
- Duyệt project từ Modrinth và CurseForge bằng cùng giao diện có icon, summary, metadata, gallery, mô tả tùy chọn, version selector và nút mở web.
- Tìm kiếm theo Minecraft version của instance; Release/Beta/Alpha tiếp tục dùng setting chung của launcher.
- Cài đúng file ZIP vào `minecraft/resourcepacks` hoặc `minecraft/shaderpacks` qua Download Engine chung.
- Hỗ trợ nhập ZIP cục bộ, bật/tắt bằng thư mục `.disabled`, gỡ pack, mở thư mục và mở trang project.
- Resource pack phải có `pack.mcmeta` hợp lệ ở root và `pack_format` dương.
- Shader pack phải có thư mục `shaders` ở root.
- Chặn path traversal, đường dẫn tuyệt đối, symlink, duplicate member, archive quá lớn và file không đúng hash/size.
- Không ghi đè pack không liên quan có cùng tên; launcher tạo tên đích an toàn thay thế.
- Cập nhật cùng project thay thế binary cũ theo transaction; lỗi ghi registry sẽ rollback file.
- Lưu metadata tại `.mcw/content-packs.json`: content type, provider, project/version/file ID, version, pack format, hash, size, URL nguồn, URL project, thời điểm cài và trạng thái bật/tắt.
- Khi cài shader mà chưa phát hiện Iris/Oculus/OptiFine/Canvas, launcher chỉ cảnh báo thay vì tự ý cài dependency.
- Progress tải content dùng stage `DOWNLOADING_CONTENT` và pipeline pause/resume/cancel chung.
- Launch Control cao hơn; Launch chiếm toàn bộ vùng nút khi idle, còn Pause/Cancel hoặc Resume/Cancel chia đều vùng trong lúc tác vụ hoạt động.

### Tương thích

- Giữ nguyên Rich Content Browser của beta.1.
- Giữ FTB modpacks, manifest-first creation, deferred first-launch downloads và settings review của beta.2.
- Metadata beta.3 được thiết kế để beta.5 Content Library và beta.6 multi-source manifest export có thể tái sử dụng.

## English

Beta 3 expands the Content Browser into per-instance **Resource Pack** and **Shader Pack** management while finishing the Launch Control layout so Launch, Pause, and Cancel fill the available action area in both dimensions.

### Highlights

- Add **Manage Content Packs** to the Instance Workspace and context menu.
- Add separate installed libraries for resource packs and shader packs.
- Browse Modrinth and CurseForge projects through the shared icon/detail/gallery/version-selection experience.
- Install verified ZIP files into `minecraft/resourcepacks` or `minecraft/shaderpacks` through the shared Download Engine.
- Support local ZIP import, safe enable/disable through `.disabled`, removal, folder access, and provider project links.
- Require a valid root `pack.mcmeta` and positive `pack_format` for resource packs.
- Require a root `shaders` directory for shader packs.
- Reject traversal, absolute paths, symlinks, duplicate members, oversized archives, and hash/size mismatches.
- Avoid overwriting unrelated files with the same name and roll back file changes when registry persistence fails.
- Persist source identity and integrity metadata in `.mcw/content-packs.json` for later update, repair, library, and manifest-export workflows.
- Warn when no known shader environment is detected instead of installing dependencies without approval.
- Add `DOWNLOADING_CONTENT` progress through the shared pause/resume/cancel pipeline.
- Increase Launch Control height; Launch fills the idle action area and Pause/Cancel or Resume/Cancel split the active area evenly.

### Compatibility

- Preserve the beta.1 rich browsing foundation.
- Preserve beta.2 FTB modpacks, manifest-first creation, first-launch downloads, and settings review.
- Keep beta.3 metadata reusable for the planned beta.5 Content Library and beta.6 multi-source manifest export.
