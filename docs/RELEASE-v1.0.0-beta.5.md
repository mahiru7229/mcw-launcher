# MCW Launcher v1.0.0-beta.5

## Tiếng Việt

Beta 5 bổ sung **Installed Content Library** — một nơi duy nhất để xem và quản lý toàn bộ nội dung của từng instance mà không phải chuyển qua nhiều cửa sổ riêng.

### Điểm mới

- Gom modpack, mod, resource pack và shader pack vào cùng một bảng.
- Hiển thị đúng nguồn Modrinth, CurseForge, FTB, local hoặc manual; mod thuộc modpack vẫn giữ provider và pack sở hữu từ `.mcw/mod-provenance.json`.
- Đọc cả file thực tế lẫn manifest đang chờ tải, vì vậy mod deferred ở lần Launch đầu vẫn xuất hiện với trạng thái `Pending` thay vì biến mất.
- Phân biệt các trạng thái ready, disabled, pending, missing và broken.
- Thêm tìm kiếm cùng bộ lọc loại nội dung, provider và trạng thái.
- Hiển thị tổng số mục, số mục đang hoạt động, nội dung do modpack quản lý, file pending/missing và tổng dung lượng.
- Panel chi tiết cho biết version, đường dẫn, project/version/file ID và hash khi registry có dữ liệu.
- Mở nhanh trình quản lý tương ứng, thư mục đích hoặc trang project trên web.
- Hỗ trợ chọn nhiều mục để bật, tắt hoặc gỡ; mod được modpack quản lý được bảo vệ khỏi thao tác xóa trực tiếp.
- Cho phép ghim phiên bản và bỏ qua cập nhật cho nhiều mục cùng lúc.
- Lưu các lựa chọn tại `.mcw/content-library.json` bằng ghi file nguyên tử và tự dọn entry không còn tồn tại.
- Giữ nguyên provenance, FTB, deferred modpack download, resource pack, shader pack và Launch Control từ các beta trước.

### Chuẩn bị cho beta.6

Installed Content Library tạo một danh sách nội dung đã chuẩn hóa với provider ID, file identity, hash, kích thước và đường dẫn đích. Beta.6 có thể dùng trực tiếp dữ liệu này để xây manifest nhiều nguồn và chỉ nhúng các file không thể tải lại an toàn.

## English

Beta 5 adds an **Installed Content Library** — a single per-instance view for inspecting and managing installed content without jumping between separate dialogs.

### Highlights

- Combine modpacks, mods, resource packs, and shader packs in one table.
- Preserve Modrinth, CurseForge, FTB, local, and manual source identity; modpack-managed mods retain their provider and owning pack from `.mcw/mod-provenance.json`.
- Read both materialized files and pending manifest entries, so deferred first-launch mods appear as Pending instead of disappearing.
- Distinguish ready, disabled, pending, missing, and broken states.
- Add search plus type, provider, and status filters.
- Show totals for active items, modpack-managed content, pending/missing files, and aggregate size.
- Expose version, target path, project/version/file IDs, and hashes in the detail panel when available.
- Open the relevant manager, destination folder, or provider project page directly.
- Support multi-selection for enable, disable, and removal; modpack-managed mods are protected from direct deletion.
- Add version pinning and ignored-update preferences for one or many selected items.
- Persist preferences atomically in `.mcw/content-library.json` and prune stale entries automatically.
- Preserve provenance, FTB support, deferred downloads, resource/shader packs, and Launch Control behavior from earlier betas.

### Beta 6 preparation

The Installed Content Library provides a normalized inventory containing provider identity, file IDs, hashes, size, and target paths. Beta 6 can consume this inventory directly to create multi-source manifests and embed only files that cannot be downloaded safely.
