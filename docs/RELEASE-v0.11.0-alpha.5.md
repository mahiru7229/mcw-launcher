# MCW Launcher v0.11.0-alpha.5 — Motion Polish & Performance

## Tiếng Việt

Bản Alpha 5 hoàn thiện nền tảng animation theo theme với toast notification, giới hạn FPS và cơ chế tự tạm dừng khi launcher bị ẩn hoặc thu nhỏ. Trang Appearance nay có khu xem trước animation để kiểm tra theme mà không cần khởi chạy Minecraft.

### Thay đổi chính

- Theme schema 5 với cấu hình `motion.toast` và `motion.performance`.
- Toast notification hỗ trợ `none`, `fade`, `slide` và `slide_fade`.
- Toast thành công cho backup, restore, repair, cập nhật modpack, export và reload theme.
- Animation clock dùng chung hỗ trợ FPS riêng cho Full/Reduced và dừng khi toàn bộ cửa sổ bị ẩn hoặc minimize.
- Timeline animation được đóng băng khi tạm dừng, tránh nhảy frame khi cửa sổ hiện lại.
- Preview trong Appearance cho state animation, determinate progress, indeterminate progress và toast.
- Default theme có spritesheet mẫu cho success, warning và error.
- Theme schema 1–4 tiếp tục tương thích.

## English

Alpha 5 polishes the theme animation foundation with toast notifications, FPS limits, and automatic pausing while the launcher is hidden or minimized. Appearance now includes a motion preview area so theme authors can validate animations without launching Minecraft.

### Highlights

- Theme schema 5 with `motion.toast` and `motion.performance` configuration.
- Toast notifications support `none`, `fade`, `slide`, and `slide_fade` transitions.
- Success toasts for backup, restore, repair, modpack update, export, and theme reload operations.
- Shared animation clock supports separate Full/Reduced FPS limits and pauses when all windows are hidden or minimized.
- Animation time freezes while suspended, preventing frame jumps after restoring the window.
- Appearance preview for state animations, determinate progress, indeterminate progress, and toast motion.
- Default theme includes sample success, warning, and error sprite sheets.
- Theme schemas 1–4 remain compatible.
