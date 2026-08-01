# MCW Launcher v0.11.0 — Theme Runtime & Animation Update

## Tiếng Việt

`v0.11.0` là bản Stable hoàn thiện hệ thống giao diện động và theme có thể mở rộng của MCW Launcher. Bản phát hành giữ nguyên Theme Runtime Contract v1 và Theme Schema 6 đã được khóa từ giai đoạn RC, đồng thời bao gồm toàn bộ hotfix startup và circular import đã xác minh trên RC2.

### Điểm nổi bật

- Thêm animation engine dùng chung cho giao diện, spritesheet và animated assets theo theme.
- Progress bar hỗ trợ determinate/indeterminate animation, clip theo tiến độ, tile/stretch/contain và fallback tĩnh an toàn.
- Theme có thể đóng gói font `.ttf`/`.otf` và áp dụng cho toàn bộ chữ do Qt render mà không cần cài font vào Windows.
- Hỗ trợ chuyển trang, sidebar collapse, button feedback, dialog fade, Launch Control motion và toast notification.
- Có ba chế độ chuyển động: **Full**, **Reduced** và **Off**; animation tự dừng khi cửa sổ bị ẩn hoặc thu nhỏ.
- Theme Authoring Toolkit hỗ trợ validation chi tiết, live reload, duplicate, import/export ZIP, checksum và preview trực tiếp.
- Theme Runtime Contract v1 công bố JSON Schema v6, asset catalog v1, validation report v1 và package format v1 cho MCW Theme Studio.
- Theme schema 6 hỗ trợ `palette` và `accent_assets`; người dùng có thể dùng màu của theme hoặc chọn màu chủ đạo tùy chỉnh trong Launcher Settings.
- Màu chủ đạo được đồng bộ với QPalette, QSS, focus, selection, progress, primary controls, scrollbar, splash và các PNG/spritesheet được theme cho phép tint.
- Sửa cảnh báo fallback giả của default theme, cải thiện nút thu gọn sidebar và giữ khả năng cuộn các trang read-only trong khi launcher đang bận.
- Sửa lỗi startup splash do dấu ngoặc QSS trong f-string và loại bỏ circular import giữa animation, theme runtime và themed widgets.

### Tương thích

- Theme schema 1–6 tiếp tục được hỗ trợ.
- Các field palette/accent của schema 6 là optional; theme cũ vẫn dùng fallback mặc định.
- Update từ `v0.10.0` và các bản thử nghiệm `v0.11.0` được hỗ trợ qua updater package chuẩn.
- Stable dùng kênh cập nhật `stable`; người dùng muốn nhận pre-release sau này vẫn cần chủ động tham gia tester program.

### Dành cho tác giả theme

Các contract machine-readable nằm trong:

```text
docs/schema/
├── theme.schema.v6.json
├── theme-assets.v1.json
└── theme-runtime-contract.v1.json
```

Validate theme bằng CLI:

```powershell
python tools/validate_theme.py themes/my-theme --json
```

## English

`v0.11.0` is the Stable release that completes MCW Launcher's animated and extensible theme runtime. It preserves the Theme Runtime Contract v1 and frozen Theme Schema 6 from the RC cycle, and includes the verified RC2 startup and circular-import hotfixes.

### Highlights

- Add a shared animation engine for interface motion, sprite sheets, and theme-driven animated assets.
- Support determinate and indeterminate animated progress with clipping, tile/stretch/contain rendering, and safe static fallbacks.
- Allow themes to bundle `.ttf`/`.otf` fonts and apply them across Qt-rendered text without installing fonts in Windows.
- Add page transitions, sidebar collapse, button feedback, dialog fades, Launch Control motion, and animated toast notifications.
- Provide **Full**, **Reduced**, and **Off** motion modes, including automatic pause while the launcher is hidden or minimized.
- Add a Theme Authoring Toolkit with detailed validation, live reload, duplication, ZIP import/export, checksums, and integrated previews.
- Publish Theme Runtime Contract v1 with JSON Schema v6, asset catalog v1, validation report v1, and theme package format v1 for MCW Theme Studio.
- Extend schema 6 with `palette` and `accent_assets`; users can select the theme accent or a custom accent in Launcher Settings.
- Synchronize accent colors with QPalette, QSS, focus, selection, progress, primary controls, scrollbars, the startup splash, and opt-in PNG/sprite assets.
- Fix the false fallback warning in the default theme, improve the sidebar collapse control, and preserve scrolling on read-only pages while the launcher is busy.
- Fix startup splash QSS interpolation and remove circular imports between animation, theme runtime, and themed widgets.

### Compatibility

- Theme schemas 1–6 remain supported.
- Schema 6 palette/accent fields are optional; older themes continue using safe defaults.
- Updates from `v0.10.0` and the `v0.11.0` pre-release series are supported through the standard updater package.
- Stable uses the `stable` update channel; future pre-releases still require tester opt-in.

### For theme authors

Machine-readable contracts are available under:

```text
docs/schema/
├── theme.schema.v6.json
├── theme-assets.v1.json
└── theme-runtime-contract.v1.json
```

Validate a theme from the command line:

```powershell
python tools/validate_theme.py themes/my-theme --json
```
