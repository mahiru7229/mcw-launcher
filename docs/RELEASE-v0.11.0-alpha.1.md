# MCW Launcher v0.11.0-alpha.1

## Tiếng Việt — Theme Animation Engine

Đây là bản Alpha đầu tiên của nhánh v0.11, tập trung xây dựng animation thành
một phần chính thức của hệ thống theme thay vì gắn hiệu ứng riêng lẻ vào từng
widget.

### Điểm mới

- Thêm **MCW Theme Animation Schema v1** trên `theme.json` schema 2.
- Theme có thể cung cấp PNG spritesheet cùng metadata frame, tốc độ, loop,
  filtering và cách render.
- Thêm animation clock dùng chung để tránh tạo một timer riêng cho từng widget.
- Thêm `ThemeAnimationPlayer` có thể tái sử dụng cho progress, icon trạng thái và
  các animated asset tương lai.
- Thay các progress bar chính bằng `ThemedProgressBar` hỗ trợ:
  - progress xác định theo phần trăm;
  - progress không xác định;
  - clip animation theo vùng đã hoàn thành;
  - `tile_x`, `stretch` và `contain`;
  - nearest-neighbor cho pixel art;
  - fallback về PNG tĩnh hoặc CSS.
- Launch Control có thể phát animation `state.busy` do theme cung cấp.
- Default theme đi kèm spritesheet mẫu cho progress và trạng thái busy.
- Theme schema 1 cũ tiếp tục tương thích mà không cần sửa manifest.

### An toàn và validation

- Chỉ hỗ trợ PNG spritesheet; không chạy script hoặc executable từ theme.
- Chặn path tuyệt đối và path traversal ra ngoài thư mục theme.
- Giới hạn kích thước frame, số frame và thời gian mỗi frame.
- Kiểm tra spritesheet có đủ diện tích cho metadata đã khai báo.
- Animation thiếu hoặc hỏng chỉ fallback riêng thành phần đó, không làm launcher
  crash.

### Tài liệu

- `docs/THEME_ANIMATION_GUIDE.md`
- `docs/THEME_CREATION_GUIDE.md`
- `themes/README.md`

## English — Theme Animation Engine

This is the first Alpha build in the v0.11 line. It turns animation into a
first-class theme capability instead of attaching isolated effects directly to
individual widgets.

### Highlights

- Introduces **MCW Theme Animation Schema v1** through theme manifest schema 2.
- Themes can provide PNG sprite sheets with frame size, timing, looping,
  filtering and render metadata.
- Adds a shared animation clock to avoid one timer per animated widget.
- Adds a reusable `ThemeAnimationPlayer` for progress bars, state indicators and
  future animated assets.
- Replaces the main progress bars with `ThemedProgressBar`, supporting
  determinate and indeterminate progress, clipped animated fill, pixel-art
  filtering and safe static/CSS fallback.
- Launch Control can use the theme-provided `state.busy` animation.
- The default theme includes sample progress and busy-state sprite sheets.
- Existing schema 1 themes remain compatible without manifest changes.

### Release metadata

- Version: `v0.11.0 Alpha 1`
- Version ID: `0.11.0-alpha.1`
- Tag: `v0.11.0-alpha.1`
- Build update channel: `beta`
- Fresh-user channel policy remains `stable`; tester opt-in is preserved
- GitHub Release type: Pre-release
