# MCW Launcher themes

Mỗi theme nằm trong `themes/<theme-id>/` và có một `theme.json`.

- Mọi PNG và font theme đều tùy chọn.
- Thiếu hoặc hỏng một file chỉ làm đúng thành phần đó fallback về CSS mặc định.
- Launcher không dừng khởi động vì theme chưa hoàn chỉnh.
- Có thể reload/preview trong **Launcher Settings → Appearance**.
- Theme ngoài EXE có thể được thêm hoặc cập nhật mà không cần build lại launcher.

Tài liệu:

- [`docs/THEME_CREATION_GUIDE.md`](../docs/THEME_CREATION_GUIDE.md) — hướng dẫn tạo theme từng bước.
- [`docs/THEME_ASSET_GUIDE.md`](../docs/THEME_ASSET_GUIDE.md) — toàn bộ key, đường dẫn và canvas PNG.
- [`docs/THEME_ANIMATION_GUIDE.md`](../docs/THEME_ANIMATION_GUIDE.md) — PNG spritesheet và animation metadata.
- [`docs/THEME_FONT_GUIDE.md`](../docs/THEME_FONT_GUIDE.md) — đóng gói TTF/OTF và áp dụng font toàn launcher.
- [`docs/THEME_MOTION_GUIDE.md`](../docs/THEME_MOTION_GUIDE.md) — page, button, dialog, sidebar và Launch Control motion.

## Asset mới của Beta 9

```text
surfaces/cards/microsoft.png
surfaces/cards/java.png
surfaces/cards/lifecycle.png
surfaces/badges/locked.png
icons/actions/microsoft.png
icons/actions/java.png
icons/actions/backup.png
icons/actions/restore.png
```

Các asset này tương ứng với card Microsoft approval, Java diagnostics, Backup/Modpack lifecycle và các nút hành động mới.

## PNG đã chứa chữ

Khi một PNG đã vẽ sẵn nội dung cố định, khai báo role tương ứng:

```json
{
  "text_assets": {
    "control.launch": "button.launch"
  }
}
```

**Show static text over themed controls** mặc định tắt. Launcher chỉ ẩn chữ khi asset được khai báo tồn tại và là PNG hợp lệ; thiếu hoặc lỗi file thì chữ fallback vẫn xuất hiện. Người dùng vẫn có thể bật lại chữ trong Launcher Settings.

Không nên vẽ cứng nội dung động như tên instance, username, version, progress hoặc error message lên PNG.

## Asset mới của Beta 10

```text
surfaces/cards/security.png
icons/actions/shield.png
icons/actions/reprotect.png
```

Các asset này dùng cho card Account Security, nút kiểm tra integrity và nút mã hóa lại credential. Tất cả vẫn là optional và fallback về CSS/icon trống khi chưa có PNG.

## Asset Cancel của Beta 2

Khi một tác vụ Launch đang chuẩn bị hoặc tải file, nút Launch chuyển sang trạng thái Cancel. Theme có thể tùy chỉnh:

```text
controls/buttons/launch/cancel.png
controls/buttons/launch/cancel_hover.png
controls/buttons/launch/cancel_pressed.png
controls/buttons/launch/cancel_disabled.png
```

Các key tương ứng là `button.cancel`, `button.cancel_hover`, `button.cancel_pressed`, `button.cancel_disabled`. Có thể khai báo `control.cancel` trong `text_assets` nếu PNG đã chứa chữ. Theme cũ không có các file này sẽ tự dùng PNG Cancel mặc định của launcher.

## Animation của v0.11.0-alpha.1

Theme schema 2 có thể khai báo PNG spritesheet trong field `animations`. Alpha 1 hỗ trợ trực tiếp:

```text
progress.chunk
progress.indeterminate
state.busy
```

Ví dụ tối thiểu:

```json
{
  "schema_version": 2,
  "animations": {
    "progress.chunk": {
      "type": "spritesheet",
      "path": "animations/progress.png",
      "frame_size": [16, 16],
      "frame_count": 8,
      "columns": 8,
      "frame_duration_ms": 80,
      "render_mode": "tile_x",
      "filtering": "nearest"
    }
  }
}
```

Xem [`docs/THEME_ANIMATION_GUIDE.md`](../docs/THEME_ANIMATION_GUIDE.md) để biết đầy đủ schema, fallback, giới hạn an toàn và cách bố trí frame.


## Custom font của v0.11.0-alpha.2

Theme schema 3 có thể đóng gói font mà không yêu cầu người dùng cài font vào Windows:

```json
{
  "schema_version": 3,
  "font": {
    "path": "fonts/ui.ttf",
    "family": "My Pixel Font",
    "point_size": 10.5,
    "weight": 400,
    "fallback_families": ["Segoe UI", "Arial"]
  }
}
```

Font được áp dụng lên toàn bộ widget, dialog, splash, tooltip và log. Khi file thiếu, hỏng hoặc Qt không đọc được, launcher tự quay về font hệ thống. Xem [`docs/THEME_FONT_GUIDE.md`](../docs/THEME_FONT_GUIDE.md) để biết cách dùng nhiều weight, glyph tiếng Việt và giới hạn file.


## Motion Polish của v0.11.0-alpha.5

Theme schema 5 có thể khai báo field `motion` để điều khiển transition, toast, FPS, duration, easing và độ mạnh interaction. Người dùng vẫn có quyền chọn Full, Reduced hoặc Off trong Launcher Settings. Theme schema cũ tự dùng motion mặc định an toàn.

```json
{
  "schema_version": 5,
  "motion": {
    "page": {"type": "fade_slide", "duration_ms": 170, "easing": "out_cubic", "distance_px": 18},
    "button": {"hover_duration_ms": 100, "press_duration_ms": 70, "easing": "out_quad"},
    "dialog": {"type": "fade", "duration_ms": 160, "easing": "out_cubic"},
    "sidebar": {"duration_ms": 220, "easing": "out_cubic", "collapsed_width": 72},
    "launch_control": {"type": "fade", "duration_ms": 140, "easing": "out_cubic"},
    "toast": {"type": "slide_fade", "duration_ms": 180, "visible_duration_ms": 3000, "distance_px": 24, "max_visible": 3},
    "performance": {"full_fps": 60, "reduced_fps": 30, "pause_when_hidden": true}
  }
}
```

## Theme Authoring Toolkit của v0.11.0-beta.2

Appearance hiện có validation details, live reload, duplicate, import và export ZIP. Schema 6 hỗ trợ custom stylesheet qua field `stylesheet`, với giới hạn 512 KiB và chặn `@import`/`url()`.

Xem [`docs/THEME_AUTHORING_TOOLKIT.md`](../docs/THEME_AUTHORING_TOOLKIT.md) và template trong [`docs/theme-template`](../docs/theme-template).

## Runtime Contract của v0.11.0-rc.1

Schema 6 đã được đóng băng để MCW Theme Studio và các công cụ ngoài launcher có thể dùng chung một hợp đồng ổn định. Không hard-code asset key từ source; hãy đọc các tệp máy có thể đọc trong [`docs/schema`](../docs/schema):

- `theme.schema.v6.json`
- `theme-assets.v1.json`
- `theme-runtime-contract.v1.json`

Package export từ RC 1 dùng ZIP deterministic và `theme-checksums.json` format 1. Xem [`docs/THEME_RUNTIME_CONTRACT.md`](../docs/THEME_RUNTIME_CONTRACT.md).
