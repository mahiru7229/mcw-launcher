# MCW Launcher v0.11.0-alpha.2

## Tiếng Việt — Theme Custom Font

Alpha 2 mở rộng hệ thống theme của v0.11 để theme có thể đóng gói font TTF/OTF và áp dụng font đó cho toàn bộ chữ trong launcher.

### Điểm mới

- Thêm manifest schema 3 với field `font`.
- Theme có thể khai báo một hoặc nhiều file `.ttf`/`.otf`.
- Hỗ trợ family, point size, weight, italic, letter spacing và fallback family.
- Font được đăng ký ở runtime; người dùng không cần cài font vào Windows.
- Font đổi ngay khi nhấn **Reload and preview theme**.
- Áp dụng trên widget, button, input, dialog, message box, startup splash, tooltip và log.
- Gỡ các `font-family` hard-code khiến một số khu vực không nhận theme font.
- Theme schema 1 và 2 tiếp tục tương thích.

### An toàn và fallback

- Chặn path tuyệt đối và path traversal.
- Chỉ nhận TTF/OTF với signature hợp lệ.
- Giới hạn 8 file, 16 MiB mỗi file và 32 MiB tổng.
- Nếu font thiếu, hỏng hoặc Qt không nhận, launcher quay về font mặc định mà không crash.

### Tài liệu

- `docs/THEME_FONT_GUIDE.md`
- `docs/THEME_CREATION_GUIDE.md`
- `themes/README.md`

## English — Theme Custom Font

Alpha 2 extends the v0.11 theme engine with packaged TTF/OTF fonts that can style all launcher text without requiring a system font installation.

### Highlights

- Adds theme manifest schema 3 and the `font` section.
- Supports one or more TTF/OTF files, family selection, point size, weight, italic, letter spacing and fallback families.
- Registers fonts at runtime and updates them immediately during theme preview.
- Applies the selected family across widgets, controls, dialogs, the startup splash, tooltips and logs.
- Removes hard-coded font families that previously prevented full-theme font coverage.
- Keeps schema 1 and schema 2 themes compatible.

### Release metadata

- Version: `v0.11.0 Alpha 2`
- Version ID: `0.11.0-alpha.2`
- Tag: `v0.11.0-alpha.2`
- Build update channel: `beta`
- Fresh-user channel policy remains `stable`; tester opt-in is preserved
- GitHub Release type: Pre-release
