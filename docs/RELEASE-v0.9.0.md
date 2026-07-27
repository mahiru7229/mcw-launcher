# MCW Launcher v0.9.0

## Bản phát hành Stable

MCW Launcher v0.9.0 là bản Stable hoàn thiện từ chuỗi Beta 3 đến Beta 6 và
Release Candidate 1. Phạm vi tính năng đã được đóng băng; bản phát hành này
không bổ sung tính năng mới so với RC1.

## Điểm nổi bật

- Khôi phục các lượt tải bị gián đoạn bằng file tạm đã xác minh và download journal bền vững.
- Hiển thị bản xem trước thay đổi trước khi cập nhật modpack được quản lý.
- Tạo recovery point trước các thao tác Repair Center có ảnh hưởng đến instance.
- Tự động rollback khi quá trình repair instance thất bại.
- Xuất gói diagnostics ZIP có giới hạn dung lượng và lọc dữ liệu nhạy cảm.
- Hỗ trợ chuỗi tác vụ preview → update mà không bị khóa sai trạng thái.
- Restore backup an toàn hơn khi Windows chặn đổi tên thư mục staging như `.fabric`.

## Tính tương thích

- Không thay đổi định dạng instance, account database, modpack hoặc launcher settings so với RC1.
- Người dùng mới sử dụng kênh cập nhật `stable` theo mặc định.
- Lựa chọn tham gia chương trình tester trước đó vẫn được giữ nguyên.
- Dữ liệu trong `instances/`, `accounts/`, `cache/`, `config/` và `logs/` không được đóng gói vào release.

## Xác minh nguồn

- Toàn bộ test: `1023 passed`, `0 failed`, `0 errors`.
- Release preflight: đạt.
- Language parity: `1047` key trong cả `en-US` và `vi-VN`.
- Merge marker chưa xử lý: `0`.

## Metadata phát hành

- Phiên bản: `v0.9.0`
- Version ID: `0.9.0`
- Tag: `v0.9.0`
- Update channel: `stable`
- GitHub Release: bản phát hành thông thường, không đánh dấu Pre-release
