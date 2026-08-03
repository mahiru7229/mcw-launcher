# MCW Launcher v1.0.0-beta.2

## Tiếng Việt

Beta 2 mở rộng Content Browser của beta.1 bằng việc thêm **FTB Modpacks** vào luồng tạo instance. Người dùng có thể tìm kiếm hoặc duyệt các pack phổ biến, xem thông tin dự án, chọn phiên bản cụ thể rồi mới cài đặt.

### Điểm mới

- Thêm nút **Duyệt modpack FTB** trong Add Instance, trang Instances và workspace instance.
- Thêm browser FTB dạng ngang, giới hạn chiều cao theo màn hình và dùng chung `ContentProjectDetailPanel` của beta.1.
- Hiển thị icon, tên pack, tác giả, lượt cài, ngày cập nhật, mô tả, metadata Minecraft/mod loader, gallery và liên kết web khi FTB cung cấp.
- Hỗ trợ tìm kiếm, danh sách pack phổ biến, sắp xếp, phân trang cục bộ, cache metadata, refresh thủ công và stale-cache fallback khi API tạm lỗi.
- Chọn release channel Release/Beta/Alpha và tải metadata phiên bản trước khi bật nút cài.
- Hiển thị Minecraft version, loader, số file client, dung lượng tải và RAM khuyến nghị trước khi cài.
- Khi tạo instance, chỉ lưu manifest và overrides cần thiết; các mod/file quản lý được tải ở lần nhấn Launch đầu tiên.
- Khi Launch, tải file theo thứ tự URL chính rồi các mirror do FTB cung cấp; xác minh size và SHA-1 bằng Download Engine chung.
- Bỏ qua file chỉ dành cho server, cho phép người dùng chọn có cài file tùy chọn hay không.
- Tạo instance, ghi `.mcw/ftb-pack.json` và đặt artwork dự án mà không tải trước toàn bộ mod hoặc chuẩn bị loader. Loader và nội dung được materialize khi Launch.
- Trước khi tạo bất kỳ instance modpack nào, mở bảng Instance Settings với ưu tiên RAM khuyến nghị của pack, sau đó launcher defaults và giá trị tự động; người dùng có thể chỉnh sửa trước khi tiếp tục.
- Progress tải mod được gom thành số file đã tải và tốc độ mạng tổng, không đưa tên từng mod lên thanh progress.
- Nút Launch chiếm trọn vùng điều khiển khi rảnh; Pause và Cancel chỉ xuất hiện cạnh nhau trong lúc launch/download đang chạy.
- Rollback instance nếu bước ghi settings, registry hoặc artwork thất bại.
- Toàn bộ thao tác FTB dùng TaskRunner, progress chung, pause/cancel và phản hồi nút ngay trước khi tác vụ bắt đầu.

### Phạm vi beta.2

Beta này chỉ thêm FTB modpack browsing và cài đặt client instance. Resource pack, shader pack, datapack, world/map và hệ thống export manifest-hybrid vẫn để các beta sau.

### Ghi chú kiểm thử

FTB cung cấp manifest phiên bản gồm targets, specs và files; mỗi file có URL chính, mirrors, SHA-1, size cùng cờ client/server/optional. MCW Launcher chuẩn hóa các trường này, không cài file server-only vào client instance và chỉ chấp nhận đường dẫn nằm trong instance.

## English

Beta 2 extends the beta.1 Content Browser with **FTB Modpacks** in the instance-creation flow. Users can search or browse popular packs, review project metadata, choose a specific version, and only then start installation.

### Highlights

- Add **Browse FTB modpacks** entry points to Add Instance, the Instances page, and the instance workspace.
- Add a wide, screen-bounded FTB browser using the shared beta.1 `ContentProjectDetailPanel`.
- Display icons, pack names, authors, install counts, update dates, descriptions, Minecraft/loader metadata, gallery media, and web links when supplied by FTB.
- Support search, popular packs, sorting, local pagination, metadata cache, manual refresh, and stale-cache fallback during temporary API failures.
- Filter Release/Beta/Alpha versions and load exact version metadata before enabling installation.
- Preview Minecraft version, loader, client file count, download size, and recommended memory.
- Creating an instance stores only the manifest and required overrides; managed mods/files download on the first Launch.
- During Launch, download through the primary URL and then FTB mirrors, with size and SHA-1 verification through the shared Download Engine.
- Skip server-only files and let users include or omit optional files.
- Create the instance, save `.mcw/ftb-pack.json`, and apply project artwork without downloading every mod or preparing the loader up front. Loader/runtime content is materialized on Launch.
- Before any modpack instance is created, open the Instance Settings editor using pack RAM recommendations when available, then launcher defaults and automatic fallbacks; users can edit the values before continuing.
- Aggregate mod downloads into file count and total network speed instead of streaming individual mod names into the progress area.
- Let Launch fill the idle control area; show Pause and Cancel side by side only while launch/download work is active.
- Roll back the instance if settings, registry persistence, or artwork processing fails.
- Route FTB work through TaskRunner, shared progress, pause/cancel handling, and immediate button feedback.

### Beta 2 scope

This beta is limited to FTB modpack browsing and client-instance installation. Resource packs, shader packs, datapacks, worlds/maps, and manifest-hybrid export remain scheduled for later betas.
