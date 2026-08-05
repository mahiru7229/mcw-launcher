# MCW Launcher v1.1.0-beta.3 — Step 2

Patch này **chỉ chứa launcher diff** của bước 2 và phải được áp dụng sau patch:

- `v1.1.0-beta.3-responsive-step1`

## Nội dung

- Xóa toàn bộ khu vực **Create instance** khỏi cửa sổ **Advanced Instance Management**.
- Loại bỏ các signal, bộ lọc manifest và handler tạo/import modpack không còn thuộc cửa sổ nâng cao.
- Giữ luồng tạo instance duy nhất tại nút **Add Instance** và `CreateInstanceDialog`.
- Ngừng chuyển manifest/snapshot settings sang trang nâng cao.
- Đổi mô tả trang nâng cao để chỉ nói về quản lý instance hiện tại.
- Thêm regression tests bảo đảm phần tạo instance không quay trở lại cửa sổ nâng cao.

## Áp dụng

Giải nén ZIP vào thư mục gốc repository launcher và cho phép ghi đè file.

## Xác thực đã chạy

- `compileall`/AST parse: đạt.
- JSON ngôn ngữ: hợp lệ và có key mới ở cả `en-US`/`vi-VN`.
- `test/test_language_runtime.py` + `test/test_public_api.py`: **8 passed**.
- GUI tests được cập nhật nhưng không thể thực thi trong môi trường đóng gói vì không có PySide6; pytest xác nhận **3 module skipped**.

MCW Core không thay đổi và không nằm trong patch này.
