# MCW Launcher v0.11.0-rc.2 — Theme Palette & Accent Color

## Tiếng Việt

RC2 là release candidate cuối của dòng v0.11.0. Bản này bổ sung mảnh ghép cuối cho hệ thống theme trước khi phát hành Stable và bắt đầu MCW Theme Studio.

### Thay đổi chính

- Theme schema 6 hỗ trợ block `palette` với màu primary, hover, pressed, focus, selection, link, success, warning và error.
- Theme có thể khai báo `accent_assets` để cho phép launcher nhuộm màu PNG/spritesheet một cách có chủ đích.
- Launcher Settings có lựa chọn **Dùng màu của theme** hoặc **Dùng màu tùy chỉnh**.
- Màu tùy chỉnh được preview ngay, lưu trong launcher settings và áp dụng cho QPalette, QSS, progress animation, nút chính, selection, focus và scrollbar.
- Startup splash sử dụng theme và accent đã lưu.
- Theme schema 1–6 vẫn tương thích; các field palette mới đều optional.
- Theme Runtime Contract v1 và JSON Schema v6 đã được cập nhật nhưng không thay đổi ý nghĩa các field đã khóa.

## English

RC2 is the final release candidate for v0.11.0. It adds the last theme-system feature required before Stable and MCW Theme Studio development.

### Highlights

- Theme schema 6 now supports a `palette` block for primary, hover, pressed, focus, selection, link, success, warning, and error colors.
- Themes may opt PNG and sprite assets into accent tinting through `accent_assets`.
- Launcher Settings now offers **Use theme color** and **Use custom color** modes.
- Custom accents preview immediately, persist in launcher settings, and apply to QPalette, QSS, progress animations, primary controls, selection, focus, and scrollbars.
- The startup splash uses the saved theme and accent.
- Theme schemas 1–6 remain compatible; all new schema 6 fields are optional.
- Theme Runtime Contract v1 and JSON Schema v6 are updated without changing existing frozen field semantics.
