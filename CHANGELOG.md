# Changelog

Các thay đổi đáng chú ý của MCW Launcher được ghi tại đây. Dự án dùng semantic versioning cho version public; bản `alpha`, `beta` và `rc` có thể thay đổi API nội bộ.

## [1.5.0-beta.3] - 2026-08-30

### Changed

- Dialog OptiFine mở từ panel chức năng của instance dùng lưới hai cột ổn định thay cho form có thể nén sai chiều cao trên Linux.
- Giá trị Detected version giữ một dòng với chiều rộng tự nhiên; đường dẫn JAR dài vẫn được xuống dòng.
- Nội dung OptiFine cuộn dọc khi thiếu chiều cao, trong khi hàng nút Install/Repair/Uninstall/Close luôn cố định.

### Fixed

- Không còn cắt hoặc chồng dòng Detected version trong dialog OptiFine trên Lubuntu.

### Release status

- Automatic update Beta 1 → Beta 2 trên Linux x64 đã được xác nhận hoạt động thành công; Beta 3 tập trung chốt UI regression trước RC.

## [1.5.0-beta.2] - 2026-08-29

### Changed

- OptiFine và Instance Info giữ kích thước tự nhiên; khi thiếu chiều cao, nội dung cuộn dọc còn action/footer vẫn truy cập được.
- Các thao tác mở file/thư mục trên Linux ưu tiên `xdg-open`, sau đó `gio open`, rồi mới dùng Qt desktop services.

### Fixed

- Sửa dialog OptiFine và panel Instance Info bị cắt/chồng nội dung trên Linux ở cửa sổ nhỏ.
- Sửa các nút Open Folder không phản hồi trên một số desktop Lubuntu.

### Release status

- Beta 2 là live update gate để xác nhận updater Beta 1 → Beta 2 giữ nguyên dữ liệu XDG và khởi động lại đúng phiên bản.

## [1.5.0-beta.1] - 2026-08-28

### Added

- Automatic updater thử nghiệm cho packaged Linux x64 release.
- Platform-aware GitHub asset selection cho ZIP Windows/Linux riêng biệt.
- Linux updater helper chạy tách session, kiểm tra quyền ghi, giữ executable mode và tự restart.
- Integration test giả lập toàn bộ Beta 1 → Beta 2 mà không thay đổi dữ liệu XDG.

### Changed

- Release manifest bắt buộc khớp schema, version, platform, executable và managed-file set.
- Update applier thay từng file atomically và dùng chung backup/rollback cho Windows/Linux.

### Security

- Từ chối path traversal, symlink, duplicate archive path, file ngoài manifest và sai platform.
- Updater Linux không gọi `sudo`; thư mục cài đặt chỉ đọc phải update thủ công.

### Release status

- Beta 2 sẽ là live update gate đầu tiên cho luồng Beta 1 → Beta 2 trên Lubuntu.

## [1.5.0-alpha.5] - 2026-08-28

### Changed

- Compatibility confirmation tạm dừng launch attempt hiện tại và tiếp tục tại chỗ sau khi người dùng cho phép.
- Dialog giữ kích thước tự nhiên của action button; nội dung Add Instance tiếp tục dùng cuộn dọc khi thiếu chiều cao.

### Fixed

- Không còn chạy lại toàn bộ dependency resolving, managed-file checking và loader preflight sau cảnh báo tương thích có thể bỏ qua.
- Các nút dài trong dialog tương thích không còn bị ép nhỏ làm cắt chữ.
- Trạng thái OptiFine trong Add Instance nằm trên một hàng tự nhiên, không còn căn lệch/chồng hàng khi bị vô hiệu hóa.
- Cross-platform test không còn thay đổi `os.name` toàn cục làm pytest dùng sai `PosixPath`/`WindowsPath`; version contract cũng không còn ghim số Alpha cũ.

### Release status

- Alpha 5 là Alpha cuối của nhánh `1.5.0`; bước tiếp theo là Beta release gate trên Windows và Linux.

## [1.5.0-alpha.4] - 2026-08-23

### Added

- Forge và NeoForge được đưa vào Linux release gate.
- Fallback xác định Java 8/16/17/21 theo Minecraft release khi profile cũ hoặc custom bị thiếu `javaVersion`.
- Scrollable page dùng chung giữ minimum size tự nhiên của widget và chỉ hiện thanh cuộn dọc khi thiếu không gian.

### Changed

- Metadata `javaVersion` của Mojang luôn được ưu tiên; fallback release mapping chỉ dùng khi metadata không tồn tại.
- Add Instance, First Run Setup và các tab Runtime/Policy của Instance Settings dùng cùng một quy tắc responsive.
- Forge/NeoForge installer chạy trong process group riêng trên POSIX.

### Fixed

- Modern Forge/NeoForge không còn mặc định nhầm Java 8 khi version profile thiếu Java metadata.
- Loader installer bị timeout trên Linux dọn cả process group thay vì có thể để lại Java child process.

### Known limitations

- Forge/NeoForge vẫn cần smoke test launch thực tế trên Lubuntu trước khi chốt Alpha 4.
- Chưa có AppImage/DEB, Linux updater hoặc cam kết Linux ARM64.

## [1.5.0-alpha.3] - 2026-08-22

### Added

- XDG storage layout cho config, data, cache và state trên Linux.
- Migration một lần, copy-only từ layout portable Alpha 2; dữ liệu cũ không bị xóa hay ghi đè khi có xung đột.
- Linux Secret Service/keyring cho khóa bảo vệ refresh token Microsoft, kèm fallback local có cảnh báo.
- OAuth browser fallback qua `xdg-open` và callback server chỉ bind loopback IPv4.
- Trạng thái Online/Offline thường trực trên thanh điều hướng.
- Process group riêng cho mỗi phiên Minecraft trên POSIX để Stop/Kill xử lý đúng cây tiến trình.

### Changed

- Fabric và Quilt được đưa vào Linux release gate cùng với Vanilla và Microsoft login.
- Theme, account, instance, managed Java, backup và log dùng đúng XDG root sau bootstrap.
- Credential audit hiển thị backend bảo vệ đang dùng.

### Fixed

- Tiến trình con của loader/Java trên Linux không còn dễ bị bỏ lại khi dừng game từ launcher.
- Microsoft sign-in có thể mở trình duyệt trên các desktop Linux nơi module `webbrowser` không tìm được handler.

### Known limitations

- Chưa có AppImage/DEB và automatic updater cho Linux.
- Forge/NeoForge và Linux ARM64 chưa nằm trong release gate Alpha 3.

## [1.5.0-alpha.2] - 2026-08-21

### Added

- Linux platform profile, Adoptium metadata selection và managed Java TAR.GZ extraction.
- Linux credential encryption backend và Linux preflight tool.
- Adaptive sizing cho toàn bộ combobox trong GUI.
- Ubuntu Qt dependencies trong CI.
- Cảnh báo offline không chặn launch và thông báo khi kết nối Internet được khôi phục.

### Changed

- Java discovery dùng executable/path theo nền tảng.
- HTTP client hỗ trợ SOCKS proxy từ environment.
- Linux x64 được nâng từ nền tảng ban đầu thành source-test target.
- Manifest, Minecraft version metadata và Java startup dùng chiến lược cache-first để tránh chờ network timeout khi offline.
- Kiểm tra cập nhật và JDK online được hoãn hoặc bỏ qua khi chưa có kết nối.

### Fixed

- Adaptive combobox lấy icon của mục đang chọn qua API `itemIcon()` tương thích PySide6.
- Bổ sung lại các module cấu hình Core bị thiếu khỏi source package.
- Vanilla Minecraft 1.21.1 đã được smoke-test thành công trên Lubuntu 24.04 trong VirtualBox, gồm cả cached offline launch.

### Known limitations

- Chưa có AppImage/DEB và automatic updater cho Linux.
- Forge/NeoForge, Microsoft login và Linux ARM64 chưa nằm trong release gate.

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

[1.5.0-beta.1]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0-beta.1
[1.5.0-beta.2]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0-beta.2
[1.5.0-beta.3]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0-beta.3
## [1.4.1]

Maintenance release của nhánh 1.4, tập trung Java recovery/download và Diagnostics v2.1. Xem tag `v1.4.1` trong GitHub Releases để đọc release notes đầy đủ.

[1.4.1]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.4.1
