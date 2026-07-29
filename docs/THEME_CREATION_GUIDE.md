# Hướng dẫn tạo theme cho MCW Launcher

Tài liệu này hướng dẫn tạo theme ngoài EXE cho MCW Launcher. Từ v0.11.0-alpha.1, theme có thể kèm PNG spritesheet animation; từ v0.11.0-alpha.2, theme có thể đóng gói font TTF/OTF cho toàn bộ chữ; từ v0.11.0-alpha.4, theme có thể điều khiển chuyển động giao diện.

## 1. Tạo thư mục theme

```text
themes/
└── my-theme/
    └── theme.json
```

`my-theme` là ID thư mục. Nên dùng chữ thường, số và dấu gạch ngang.

## 2. Tạo manifest

```json
{
  "schema_version": 4,
  "id": "my-theme",
  "name": "My Theme",
  "author": "Artist name",
  "description": "A custom MCW Launcher theme.",
  "assets": {}
}
```

Các field `id`, `name`, `author` chỉ là metadata hiển thị. `assets` ánh xạ key launcher tới đường dẫn PNG tương đối bên trong theme.

## 3. Bắt đầu từ một asset nhỏ

Theme không cần đủ toàn bộ file. Ví dụ chỉ thay background và logo:

```text
themes/my-theme/
├── theme.json
├── backgrounds/
│   └── window.png
└── logos/
    └── main.png
```

```json
{
  "schema_version": 1,
  "id": "my-theme",
  "name": "My Theme",
  "author": "Artist name",
  "assets": {
    "background.window": "backgrounds/window.png",
    "logo.main": "logos/main.png"
  }
}
```

Mọi widget khác tiếp tục dùng CSS mặc định.

## 4. Asset cho Beta 9

Các màn hình mới có asset riêng:

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

Khai báo:

```json
{
  "assets": {
    "surface.microsoft_card": "surfaces/cards/microsoft.png",
    "surface.java_card": "surfaces/cards/java.png",
    "surface.lifecycle_card": "surfaces/cards/lifecycle.png",
    "badge.locked": "surfaces/badges/locked.png",
    "icon.action.microsoft": "icons/actions/microsoft.png",
    "icon.action.java": "icons/actions/java.png",
    "icon.action.backup": "icons/actions/backup.png",
    "icon.action.restore": "icons/actions/restore.png"
  }
}
```

Canvas chính xác được liệt kê trong [`THEME_ASSET_GUIDE.md`](THEME_ASSET_GUIDE.md).

## 5. Asset bảo mật Beta 10

```text
surfaces/cards/security.png       480 × 260
icons/actions/shield.png          24 × 24
icons/actions/reprotect.png       24 × 24
```

Khai báo:

```json
{
  "assets": {
    "surface.security_card": "surfaces/cards/security.png",
    "icon.action.shield": "icons/actions/shield.png",
    "icon.action.reprotect": "icons/actions/reprotect.png"
  }
}
```

Card security chứa nội dung động như số account protected/legacy/invalid, vì vậy không nên vẽ sẵn các con số hoặc trạng thái vào PNG.

## 6. PNG có chữ sẵn

Chỉ dùng cho chữ cố định. Ví dụ nút Launch đã vẽ chữ `LAUNCH`:

```json
{
  "assets": {
    "button.launch": "controls/buttons/launch/default.png"
  },
  "text_assets": {
    "control.launch": "button.launch",
    "control.cancel": "button.cancel"
  }
}
```

**Show static text over themed controls** mặc định tắt trong `v0.6.0`. Launcher chỉ ẩn chữ khi PNG hợp lệ đã được load; thiếu ảnh thì chữ tự quay lại. Người dùng có thể bật lại nếu muốn chữ Qt đè lên PNG.

Không vẽ sẵn nội dung thay đổi theo thời gian như username, tên instance, version, trạng thái tải hoặc error message.


## 7. Animation spritesheet trong v0.11.0-alpha.1

Theme có thể vẽ progress, trạng thái busy và các animated asset tương lai bằng PNG spritesheet:

```json
{
  "schema_version": 2,
  "animations": {
    "progress.chunk": {
      "type": "spritesheet",
      "path": "animations/progress/chunk.png",
      "fallback_asset": "progress.chunk",
      "frame_size": [16, 16],
      "frame_count": 8,
      "columns": 8,
      "frame_duration_ms": 80,
      "loop": true,
      "render_mode": "tile_x",
      "filtering": "nearest"
    }
  }
}
```

Theme schema 1 cũ vẫn hoạt động. Xem [`THEME_ANIMATION_GUIDE.md`](THEME_ANIMATION_GUIDE.md) để biết cách xếp frame, animation key, fallback và giới hạn an toàn.

## 8. Custom font trong v0.11.0-alpha.2

Đặt font vào thư mục theme và khai báo manifest schema 3:

```text
themes/my-theme/
├── theme.json
└── fonts/
    ├── ui-regular.ttf
    └── ui-bold.otf
```

```json
{
  "schema_version": 3,
  "font": {
    "files": [
      "fonts/ui-regular.ttf",
      "fonts/ui-bold.otf"
    ],
    "family": "My Pixel Font",
    "point_size": 10.5,
    "weight": 400,
    "letter_spacing": 0,
    "fallback_families": ["Segoe UI", "Arial"]
  }
}
```

Font được áp dụng cho toàn bộ chữ và đổi ngay khi preview theme. Font nên chứa glyph tiếng Việt; nếu thiếu, hãy khai báo `fallback_families`. Xem [`THEME_FONT_GUIDE.md`](THEME_FONT_GUIDE.md) để biết đầy đủ field và giới hạn an toàn.

## 9. Motion trong v0.11.0-alpha.4

Theme schema 4 có thể cấu hình chuyển trang, button, dialog, sidebar và Launch Control:

```json
{
  "schema_version": 4,
  "motion": {
    "page": {"type": "fade_slide", "duration_ms": 170, "easing": "out_cubic", "distance_px": 18},
    "button": {"hover_duration_ms": 100, "press_duration_ms": 70, "easing": "out_quad"},
    "dialog": {"type": "fade", "duration_ms": 160, "easing": "out_cubic"},
    "sidebar": {"duration_ms": 220, "easing": "out_cubic", "collapsed_width": 72},
    "launch_control": {"type": "fade", "duration_ms": 140, "easing": "out_cubic"}
  }
}
```

Người dùng vẫn có thể chọn Full, Reduced hoặc Off. Xem [`THEME_MOTION_GUIDE.md`](THEME_MOTION_GUIDE.md) để biết loại transition và giới hạn hợp lệ.

## 10. Trạng thái button

Một nút nên có đủ state khi có thể:

```text
controls/buttons/launch/
├── default.png
├── hover.png
├── pressed.png
├── disabled.png
├── cancel.png
├── cancel_hover.png
├── cancel_pressed.png
└── cancel_disabled.png
```

Các state Launch thiếu sẽ fallback về CSS. Riêng state Cancel có bộ PNG fallback đi kèm launcher, nên nút vẫn hiện rõ khi theme cũ chưa khai báo asset mới.

## 11. Background và vùng an toàn

- `background.window`: 1600 × 900.
- Sidebar: 220 × 900.
- Right panel: 400 × 900.
- Center/page: 980 px chiều rộng.
- Không đặt chữ quan trọng sát mép vì cửa sổ có thể scale hoặc resize.
- Kiểm tra theme trên 1366 × 768 và 1600 × 900.

## 12. Kiểm tra theme

1. Đặt folder cạnh source hoặc cạnh EXE:

```text
MCW Launcher.exe
themes/
└── my-theme/
```

2. Mở **Launcher Settings → Appearance**.
3. Chọn theme.
4. Nhấn **Reload and preview theme**.
5. Kiểm tra Accounts, Instances, Launcher Settings, Mod Manager, Modrinth Browser và các dialog.

Nếu theme không xuất hiện:

- kiểm tra `theme.json` là JSON hợp lệ;
- kiểm tra `id` không rỗng;
- kiểm tra path dùng `/` hoặc path tương đối hợp lệ;
- kiểm tra file thật sự là PNG;
- không dùng `..`, drive letter hoặc path tuyệt đối.

## 13. Fallback và theme chưa hoàn chỉnh

Theme có thể được phát hành khi mới có vài PNG. Launcher không crash vì:

- file thiếu;
- PNG hỏng;
- canvas khác khuyến nghị;
- key lạ;
- asset không đọc được.

Asset lỗi bị bỏ qua riêng lẻ. Tuy vậy, nên test console/log để phát hiện typo trong manifest.

## 14. Đóng gói cùng release

Công cụ release tự copy toàn bộ `themes/`:

```powershell
python tools/build_release_zip.py --exe ".\dist\MCW Launcher.exe" --version "0.5.1"
```

Người dùng cũng có thể thêm theme mới vào folder `themes/` mà không cần rebuild EXE.

## Checklist cho theme author

```text
[ ] theme.json hợp lệ
[ ] ID theme duy nhất
[ ] Không có path tuyệt đối hoặc ..
[ ] PNG có alpha đúng
[ ] Background được test ở nhiều độ phân giải
[ ] Button có hover/pressed khi cần
[ ] PNG có chữ được khai báo trong text_assets
[ ] Nội dung động không bị vẽ cứng vào PNG
[ ] Font TTF/OTF nằm trong theme và có glyph tiếng Việt
[ ] Font thiếu glyph có fallback_families phù hợp
[ ] Thiếu asset/font vẫn fallback dễ đọc
[ ] Theme xuất hiện sau Reload and preview theme
```
