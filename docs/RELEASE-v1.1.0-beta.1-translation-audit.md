# MCW Launcher v1.1.0-beta.1 — Translation Audit Correction

## Tiếng Việt

Bản sửa bổ sung này vẫn thuộc phạm vi **v1.1.0-beta.1** và chỉ gia cố phần bản địa hóa.

### Đã sửa

- Sửa chuỗi `Loading compatible CurseForge files...` còn hiển thị tiếng Anh.
- Chuyển các thông báo tác vụ từ controller sang khóa dịch ngữ nghĩa thay vì dựa vào chuỗi tiếng Anh và reverse lookup.
- Bổ sung 108 khóa dịch cho các tiến trình và trạng thái của:
  - CurseForge, Modrinth và FTB;
  - mod loader và quản lý mod;
  - instance, import/export, repair và icon;
  - content pack/content library;
  - LAN hosting và thông báo hoàn tất/hủy tác vụ.
- Dịch footer sidebar vốn được viết trực tiếp trong code.
- Thêm kiểm thử tĩnh để phát hiện thông báo controller chưa đi qua hệ thống dịch.
- Thêm regression test riêng cho tiến trình tải file CurseForge tương thích.

### Xác minh

- `1284 passed, 79 skipped, 2 warnings`
- Hai language pack có cùng tập khóa và không lệch placeholder.
- Không thay đổi MCW Core, public API, database hoặc định dạng dữ liệu.

## English

This correction remains part of **v1.1.0-beta.1** and only hardens localization coverage.

### Fixed

- Localized `Loading compatible CurseForge files...`.
- Replaced raw controller task/status strings with semantic translation-key calls.
- Added 108 runtime translation keys covering providers, mods, instances, content, LAN hosting, and task completion states.
- Localized the previously hard-coded sidebar footer.
- Added static coverage and regression tests for controller runtime text.

### Validation

- `1284 passed, 79 skipped, 2 warnings`
- Language packs have matching keys and valid placeholders.
- MCW Core and its wheel are unchanged.
