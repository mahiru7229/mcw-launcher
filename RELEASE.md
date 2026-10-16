# MCW Launcher v1.8.3-beta.1

Bản thử nghiệm **MCW Launcher v1.8.3-beta.1** mang đến bước nhảy vọt về hiệu năng khởi động ứng dụng, hoàn thiện cơ chế lazy-loading cho toàn bộ các hộp thoại chức năng và tăng cường độ ổn định, bảo mật cho hệ thống Qt Signal và JSON-RPC.

---

## Điểm nổi bật trong bản phát hành (Highlights)

### 1. Tối ưu hóa vượt bậc tốc độ khởi động lạnh (Cold Boot Optimization)
- **Tăng tốc hơn 11 lần**: Rút ngắn thời gian khởi động launcher từ ~18.2 giây xuống còn **~1.61 giây**.
- **Cơ chế Lazy-load 17 hộp thoại (`QDialog`)**:
  - Chuyển đổi toàn bộ 17 hộp thoại chức năng (Quản lý mod, trình duyệt Modrinth/CurseForge/FTB/ATLauncher, thư viện nội dung, trung tâm sửa chữa, v.v.) sang nạp động theo yêu cầu (on-demand).
  - Loại bỏ hoàn toàn tình trạng khởi tạo đồng loạt 17 cây widget nặng nề trong RAM ngay khi vừa bật ứng dụng.
- **Trì hoãn kiểm tra Hotfix về nền (Deferred Hotfix Check)**:
  - Tách luồng kiểm tra bản vá CDN Cloudflare ra khỏi giai đoạn hiển thị Splash.
  - Sau khi giao diện chính hiển thị xong, launcher mới âm thầm kiểm tra trên luồng phụ và hiện thông báo xác nhận nếu có bản vá mới.
- **Nạp sớm Stylesheet & Nhận diện GPU bất đồng bộ**:
  - Gắn stylesheet cơ sở lên `QApplication` trước khi dựng widget, cho phép Qt áp dụng style trực tiếp ở tầng C++.
  - Nhận diện card đồ họa chạy bất đồng bộ trong background thread có cơ chế khóa luồng `gpu_lock`.

### 2. Dịch thuật & Theme hoàn chỉnh cho các hộp thoại nạp động
- **Tự động dịch và gán asset khi mở dialog lần đầu (`_finalize_lazy_dialog`)**:
  - Đảm bảo toàn bộ văn bản và theme asset (icon, svg) của hộp thoại được dịch chuẩn xác theo ngôn ngữ người dùng lựa chọn ngay khi hiển thị lần đầu.
- **Đồng bộ hóa toàn diện khi đổi ngôn ngữ (`_retranslate_ui`)**:
  - Bổ sung các dialog còn thiếu (`_modrinth_manual_dialog`, `_optifine_dialog`, `_microsoft_device_code_dialog`) vào chu trình cập nhật ngôn ngữ.
- **Chặn khởi tạo ngầm hộp thoại khi thao tác trên ModsPage**:
  - Khi xem chi tiết hoặc tìm kiếm mod trên `ModsPage`, dữ liệu được cập nhật trực tiếp mà không kích hoạt tạo ngầm các hộp thoại modal.
- **Đọc kênh phát hành trực tiếp từ cấu hình**:
  - Helper `_allowed_modrinth_version_types()` đọc cấu hình kênh phát hành trực tiếp mà không cần khởi tạo `ModrinthBrowserDialog`.
- **Khử trùng lặp khởi tạo Theme và Reload ngôn ngữ**:
  - Loại bỏ các lệnh gọi lặp `ThemeRuntime.apply` và `language_manager.reload()` trong giai đoạn khởi tạo ban đầu.

### 3. Đồng bộ Qt Signal an toàn luồng & Tăng cường an toàn RPC
- **Cơ chế Qt Signals chuẩn luồng**:
  - Thay thế các lệnh gọi `QTimer.singleShot` từ background worker thread sang các Qt Signal chuyên biệt (`_mclogs_uploaded`, `_mclogs_failed`, `hotfix_available`, `hotfix_failed`, `gpu_detected`).
- **Khắc phục lỗi hiển thị hộp thoại sự cố khởi động**:
  - Định nghĩa đầy đủ `path_text` và `stage_text`, loại bỏ lỗi `NameError` khi launcher gặp sự cố ngoài ý muốn.
- **SSE Keepalive & Phòng vệ bảo mật Origin cho HTTP RPC**:
  - Bổ sung heartbeat keepalive (`: keepalive\n\n`) cho endpoint `/events`, khắc phục hiện tượng ngắt kết nối client sau 5 giây không có sự kiện.
  - Bổ sung bộ lọc `_is_trusted_origin()` chặn các website lạ truy cập trái phép vào RPC cục bộ (trả về HTTP 403).

---

## Thông tin kiểm thử & Xác thực (Verification)

- **Release Preflight**: Đạt chuẩn 100% cho `v1.8.3-beta.1` (`python -m tools.release_preflight`).
- **Kiểm thử GUI & Core**: Vượt qua toàn bộ 2,145 tests hồi quy và hệ thống (`2145 passed, 10 skipped`).
- **Kiểm thử giao diện (GUI Tests)**: Vượt qua toàn bộ 293/293 GUI tests.
