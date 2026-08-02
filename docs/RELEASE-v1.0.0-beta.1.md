# MCW Launcher v1.0.0-beta.1

## Tiếng Việt

Đây là bản beta đầu tiên của dòng 1.0, tập trung vào trải nghiệm khám phá nội dung Minecraft thay vì thay đổi nền tảng launch đã ổn định ở v0.12.

### Điểm mới

- Kết quả Modrinth và CurseForge hiển thị icon dự án, được tải qua bộ nhớ đệm HTTPS có giới hạn.
- Chọn mod hoặc modpack sẽ mở bảng thông tin chi tiết thay vì cài ngay lập tức.
- Bảng chi tiết hiển thị mô tả, tác giả, provider, lượt tải, thời gian cập nhật, license, phiên bản Minecraft, loader, category, trạng thái client/server và gallery khi provider cung cấp.
- Có nút mở trang dự án trên web.
- Người dùng vẫn chọn Minecraft version, loader và project version trước khi nhấn Install.
- Manage Mods và các browser Modrinth/CurseForge dùng chung thành phần chi tiết để chuẩn bị cho FTB, resource pack, shader pack và datapack trong các beta tiếp theo.
- Nội dung HTML được làm sạch; mô tả không tự tải tài nguyên web nhúng. Ảnh icon/gallery đi qua lớp tải ảnh riêng với giới hạn kích thước, timeout và cache.

### Phạm vi beta.1

Bản này hoàn thiện nền tảng trình duyệt nội dung cho Modrinth và CurseForge. FTB modpacks, resource packs, shader packs, datapacks và worlds chưa được thêm trong beta.1; chúng sẽ dùng lại nền tảng này ở các beta sau.

## English

This is the first 1.0 beta, focused on Minecraft content discovery and presentation rather than changing the launch foundation stabilized in v0.12.

### Highlights

- Modrinth and CurseForge results now display project icons through a bounded HTTPS image cache.
- Selecting a mod or modpack opens a rich project details panel instead of installing immediately.
- Details include descriptions, authors, provider metadata, downloads, update dates, license, Minecraft versions, loaders, categories, client/server support, and gallery media when available.
- Projects can be opened on their provider website.
- Minecraft version, loader, and project version remain explicit choices before installation.
- Manage Mods and both provider browsers share the same details component, establishing the foundation for FTB, resource packs, shader packs, datapacks, and other content types.
- Provider HTML is sanitized, embedded remote resources are blocked, and icons/gallery images use a dedicated size-limited, timed cache.

### Beta 1 scope

This release establishes the content browser foundation for Modrinth and CurseForge. FTB modpacks, resource packs, shader packs, datapacks, and worlds are planned for later 1.0 betas and are not included yet.
