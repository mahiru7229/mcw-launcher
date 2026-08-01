# MCW Launcher v0.11.0-beta.1 — Default GUI Fixes

## Tiếng Việt

Bản Beta 1 chuyển nhánh v0.11 từ giai đoạn thử nghiệm animation sang giai đoạn ổn định giao diện mặc định. Bản phát hành này sửa ba vấn đề được phát hiện khi dùng theme MCW Default PNG.

### Thay đổi

- Tăng kích thước nút thu gọn/mở rộng sidebar và dùng icon mũi tên chuẩn của Qt để không phụ thuộc glyph của custom font.
- Sửa cảnh báo giả `1 issue(s), fallback active` của theme mặc định. Nguyên nhân là manifest dùng `icon.nav.mods` nhưng key này bị thiếu trong theme asset catalog, dù file PNG vẫn tồn tại.
- Các trang bị khóa trong lúc launcher đang chạy tác vụ nặng giờ chuyển sang chế độ chỉ xem:
  - thao tác chỉnh sửa và nút hành động vẫn bị chặn;
  - bánh xe chuột và thanh cuộn vẫn hoạt động;
  - người dùng vẫn có thể chuyển tab và đọc thông tin trong khi game đang được chuẩn bị.
- Áp dụng busy overlay dạng read-only cho Accounts, Instances, Mods, Instance Settings và Launcher Settings.
- Thêm regression test cho theme mặc định, nút sidebar và busy-page scrolling.

## English

Beta 1 moves the v0.11 branch from animation experimentation into default-interface stabilization. This release fixes three issues found while using the MCW Default PNG theme.

### Changes

- Enlarged the sidebar collapse/expand control and switched it to Qt standard arrow icons so it no longer depends on custom-font glyph coverage.
- Fixed the false `1 issue(s), fallback active` warning on the bundled default theme. The manifest referenced `icon.nav.mods`, but that key was missing from the theme asset catalog even though the PNG file existed.
- Pages locked during blocking launcher tasks now use a read-only viewing mode:
  - editing and action controls remain blocked;
  - mouse-wheel and scrollbar navigation continue to work;
  - users can switch pages and read information while the game is being prepared.
- Applied the read-only busy overlay to Accounts, Instances, Mods, Instance Settings, and Launcher Settings.
- Added regression coverage for the default theme, sidebar toggle, and scroll-friendly busy pages.

## Metadata

- Version: `v0.11.0-beta.1`
- Update channel: `beta`
