# Changelog

Các thay đổi đáng chú ý của MCW Launcher được ghi tại đây. Dự án dùng semantic versioning cho version public; bản `alpha`, `beta` và `rc` có thể thay đổi API nội bộ.

## [1.5.0-alpha.1] - 2026-08-21

### Changed

- Chuẩn hóa metadata dự án, dependency groups và version `1.5.0-alpha.1`.
- Tách việc tải version metadata khỏi import-time để startup không tự phụ thuộc mạng.
- Dùng downloader có xác minh checksum và verified-cache fallback cho version JSON.
- Chọn native library theo hệ điều hành thay vì hard-code Windows.
- Nhận diện riêng Linux ARM64 thay vì ánh xạ nhầm sang x64.
- Validate identifier, artifact path và digest từ metadata trước khi tạo đường dẫn local.
- Chấp nhận các Minecraft version ID legacy chính thức có dấu cách; một entry lỗi không còn làm rỗng toàn bộ manifest.
- Sắp xếp lại tài liệu, release notes và quy trình preflight.

### Removed

- File delivery/patch/test output tạm ở repository root.
- Module rỗng hoặc legacy không có consumer.
- Cấu hình Microsoft trùng lặp; client metadata chỉ còn một nguồn trong `src/config.py`.
- Hàng trăm release-note rời của các bản cũ; lịch sử đầy đủ vẫn có trong Git/GitHub Releases.

### Known limitations

- Linux packaging và managed Java provisioning chưa hoàn chỉnh.
- Windows vẫn là nền tảng release chính của Alpha 1.

## [1.4.1]

Maintenance release của nhánh 1.4, tập trung Java recovery/download và Diagnostics v2.1. Xem tag `v1.4.1` trong GitHub Releases để đọc release notes đầy đủ.

[1.5.0-alpha.1]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0-alpha.1
[1.4.1]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.4.1
