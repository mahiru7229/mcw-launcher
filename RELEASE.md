# MCW Launcher v1.8.2

Bản phát hành chính thức **MCW Launcher v1.8.2** tập trung giải quyết triệt để vấn đề kết nối mạng LAN offline trên các phiên bản Minecraft cũ, cơ chế nạp hotfix tự động khi khởi động lần đầu, chuẩn hóa skin cho tài khoản offline và hiển thị đúng múi giờ địa phương cho dữ liệu thời gian chơi.

---

## Điểm nổi bật trong bản phát hành (Highlights)

### 1. Mở rộng MCW LAN Agent xuống các phiên bản Minecraft thấp (1.14.0+)
- **Khắc phục lỗi `"Invalid session"`**: Khi người chơi kết nối qua mạng LAN bằng địa chỉ IP và Port vào máy chủ host bật chế độ Offline LAN (`private_offline`), trước đây các phiên bản Minecraft cũ từ 1.14 đến 1.16.5 bị văng do thiếu bytecode target tương ứng.
- **Tự động nhận diện mapping đa nền tảng**: Bộ giải mã bytecode target `LanAgentTargetResolver` mở rộng xuống 1.14+, hỗ trợ đầy đủ:
  - Forge SRG (`func_71229_d`)
  - Fabric Intermediary (`method_3864` / `method_3782`)
  - Mojang Official Mappings (`d`)
- Kết nối LAN ổn định, mượt mà trên tất cả các phiên bản Minecraft từ 1.14 trở lên.

### 2. Tự động đồng bộ & nạp Hotfix ngay khi launcher khởi động lần đầu
- **Pre-bootstrap Auto-Sync**: Tự động kích hoạt cơ chế đồng bộ nhanh fail-open (`auto_sync=True`, timeout 2.0s) khi phát hiện launcher mới tải về hoặc chưa có hotfix cục bộ, nạp các bản vá nóng trước khi import các module giao diện vào bộ nhớ RAM.
- **Dynamic In-memory Eviction**: Tự động dọn dẹp và thu hồi các module cũ trong `sys.modules` (`_evict_cached_hotfix_modules`) ngay sau khi áp dụng bản vá nóng.
- **Toast thông báo khởi động lại**: Hiển thị Toast thông báo khi có bản vá nóng mới được nạp ngầm, cho phép người dùng khởi động lại ngay bằng một cú nhấp.

### 3. Gán model Steve / Alex cục bộ cho tài khoản Offline
- **Chuẩn hóa theo thuật toán Minecraft**: Tự động xác định biến thể Steve (`classic`) hoặc Alex (`slim`) cục bộ theo thuật toán băm UUID chuẩn của Minecraft Java (`DefaultPlayerSkin`).
- **Không truy vấn mạng ngoài**: Vô hiệu hóa hoàn toàn việc tìm kiếm skin từ Minotar hay Mojang đối với tài khoản offline, loại bỏ nguy cơ tải nhầm skin của tài khoản bản quyền khi đặt tên trùng.

### 4. Hiển thị thời gian lần cuối chơi theo múi giờ hệ thống (Local Timezone)
- Chuyển đổi timestamp UTC đã lưu trong metadata sang múi giờ địa phương bằng `astimezone()`.
- Hiển thị chính xác ngày giờ người dùng chơi game (ví dụ: `Hôm nay lúc 23:30` thay vì giờ UTC+0).

---

## Thông tin kiểm thử & Xác thực (Verification)

- **Release Preflight**: Đạt chuẩn 100% cho `v1.8.2` (`python -m tools.release_preflight`).
- **Kiểm thử GUI & Core**: Vượt qua 351/351 tests giao diện và kiểm thử hồi quy.
- **MCW Core Library**: Vượt qua 1,724/1,724 tests trong bộ mã nguồn `mcw-launcher-core`.
- **Gói Wheel**: `mcw_core-1.8.2-py3-none-any.whl` đã được đóng gói sẵn trong thư mục `dist/`.
