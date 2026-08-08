# MCW Launcher v1.2.0-beta.1

## Tiếng Việt

MCW Launcher **v1.2.0-beta.1** mở đầu nhánh feature v1.2. Mục tiêu của beta đầu tiên là xây nền tảng **Instance Manager 2.0** mà không thay đổi các pipeline dependency/modpack đã ổn định ở v1.1.2.

### Instance library organization

- Mỗi instance có thêm ba metadata tùy chọn trong `instance.json`: `favorite`, `group` và `tags`.
- Instance cũ từ v1.1.2 không cần migrate schema; các trường thiếu tự dùng giá trị mặc định an toàn.
- Tags được trim và loại trùng không phân biệt hoa/thường trước khi lưu.
- GUI chỉ cập nhật metadata qua public MCW Core `InstanceService`, giữ nguyên ranh giới Core/GUI.

### Library UX

- Thêm bộ lọc group, chế độ chỉ hiện favorites và lựa chọn sort theo tên, lần chơi gần nhất hoặc Minecraft version.
- Search hiện tìm cả tên instance, Minecraft version, loader, health, group và tags.
- Favorite được ưu tiên trong thư viện và có dấu `★` trên item.
- Context menu có thao tác thêm/bỏ favorite, đặt group và chỉnh tags.
- Panel chi tiết và Instance Editor hiển thị metadata tổ chức của instance cùng state/health hiện có.

### Compatibility

- Không tăng `instance.json` metadata schema version vì các trường mới đều optional và backward-compatible.
- Không thay đổi dependency resolver, loader install, repair, process supervision hoặc modpack lifecycle trong beta này.

### Release metadata

- Launcher runtime: `v1.2.0-beta.1`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0b1`

---

## English

MCW Launcher **v1.2.0-beta.1** starts the v1.2 feature line with the **Instance Manager 2.0** foundation while leaving the stabilized v1.1.2 dependency and modpack pipelines unchanged.

### Instance library organization

- Adds optional `favorite`, `group`, and `tags` metadata to each `instance.json`.
- Existing v1.1.2 instances require no schema migration; missing fields use safe defaults.
- Tags are trimmed and deduplicated case-insensitively before persistence.
- The GUI updates library metadata through the public MCW Core `InstanceService`, preserving the Core/GUI boundary.

### Library UX

- Adds group filtering, a favorites-only view, and sorting by name, last played time, or Minecraft version.
- Search now includes instance name, Minecraft version, loader, health, group, and tags.
- Favorite instances are prioritized and marked with `★` in the library.
- The context menu can toggle favorite status, assign a group, and edit tags.
- The selected-instance panel and Instance Editor surface organization metadata alongside existing runtime and health information.

### Compatibility

- The `instance.json` metadata schema version is unchanged because the new fields are optional and backward-compatible.
- Dependency resolution, loader installation, repair, process supervision, and modpack lifecycle behavior are intentionally unchanged in this beta.

### Release metadata

- Launcher runtime: `v1.2.0-beta.1`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0b1`
