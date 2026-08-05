# MCW Launcher v1.1.0-beta.6

## Tiếng Việt

### Phạm vi

Beta 6 hoàn tất ba lỗi còn lại được phát hiện sau Beta 5:

1. Progress của tác vụ **bảo vệ lại tài khoản** không trở về trạng thái hoàn tất hoặc thất bại.
2. Trình cài Forge/NeoForge chưa dùng đúng Java đã chọn cho instance và chưa tự phục hồi khi Java đó không thể chạy installer.
3. Forge rất cũ, điển hình Forge `9.11.1.1345` cho Minecraft `1.6.4`, bị báo sai rằng runtime Forge không tồn tại.

### Bảo vệ tài khoản

- Thêm progress profile riêng cho `account.security.reprotect`.
- Khi bắt đầu, launcher hiển thị trạng thái đang bảo vệ lại thông tin đăng nhập.
- Khi hoàn tất, progress chuyển sang trạng thái thành công với thanh tiến trình 100%.
- Khi lỗi, progress chuyển sang trạng thái thất bại thay vì mắc kẹt ở thông báo đang xử lý.
- Bổ sung bản dịch tiếng Anh và tiếng Việt cho trạng thái hoàn tất/thất bại.

### Java cho trình cài mod loader

- Forge và NeoForge installer nhận đường dẫn Java đã chọn trong thiết lập instance.
- Luồng tạo instance sử dụng Java từ thiết lập mặc định của instance khi cần chạy installer.
- Luồng đổi, sửa chữa, khôi phục mod loader và cài profile còn thiếu khi Launch đều truyền đúng Java đã chọn.
- Nếu Java tùy chọn không tồn tại, sai major hoặc không đọc được phiên bản, launcher tự chuyển sang runtime tương thích.
- Nếu installer thực sự thoát với dấu hiệu lỗi Java như `UnsupportedClassVersionError`, JNI/JVM initialization error hoặc JVM option không được hỗ trợ, launcher thử lại đúng một lần bằng Java tương thích khác.
- Log installer giữ riêng nội dung của từng lần chạy cùng đường dẫn Java đã dùng, giúp chẩn đoán chính xác hơn.
- Không retry các lỗi installer thông thường không liên quan đến Java.

### Forge cũ báo “no runtime”

Diagnostic của Forge `9.11.1.1345` cho Minecraft `1.6.4` cho thấy profile đã được import và instance được đánh dấu healthy, nhưng pre-launch validator vẫn chặn với:

```text
The Forge runtime is missing from the launch profile.
```

Nguyên nhân là các bản Forge rất cũ dùng Maven artifact `net.minecraftforge:minecraftforge`, trong khi validator trước đây chỉ nhận `net.minecraftforge:forge` và các component FML hiện đại.

Beta 6 bổ sung `minecraftforge` vào danh sách runtime hợp lệ. Profile legacy vẫn phải có main class, metadata Forge đúng và các thư viện bắt buộc vẫn được kiểm tra bình thường.

### Phiên bản

- Launcher runtime: `v1.1.0-beta.6`
- Update channel: `beta`
- Không phát hành MCW Core wheel mới; distribution dùng để build vẫn là `mcw-core 1.1.0b2`.
- Gói bàn giao chỉ chứa launcher diff. Các file trong `src/core/` là implementation được bundle trong launcher; không có thay đổi trong package `mcw_core/` và không phát hành Core riêng.

### Xác thực

- Regression test cho Forge 1.6.4 sử dụng artifact `minecraftforge`.
- Regression test cho retry Java của mod-loader installer.
- Regression test cho việc truyền Java tùy chọn qua load/prepare/repair.
- Regression test cho progress profile của bảo vệ tài khoản.
- Toàn bộ source và test qua `compileall`.
- Toàn bộ test suite: **1312 passed, 82 skipped, 2 warnings**.

### Smoke test Windows đề xuất

1. Mở một instance Forge 1.6.4 với Forge 9.11.1.1345 và Launch.
2. Xác nhận không còn lỗi `The Forge runtime is missing from the launch profile`.
3. Chọn một Java sai hoặc không tương thích trong Instance Settings, sau đó đổi/cài Forge hoặc NeoForge.
4. Xác nhận launcher tự chọn Java khác và installer tiếp tục, không lặp vô hạn.
5. Chạy **Re-protect account credentials** và xác nhận progress kết thúc ở trạng thái thành công hoặc thất bại rõ ràng.

---

## English

### Scope

Beta 6 closes three issues found after Beta 5:

1. The **re-protect account credentials** task did not return the shared progress area to a terminal state.
2. Forge/NeoForge installers did not consistently use the instance-selected Java runtime and could not recover from a Java-specific installer failure.
3. Very old Forge releases, notably Forge `9.11.1.1345` for Minecraft `1.6.4`, were incorrectly reported as having no Forge runtime.

### Account protection progress

- Adds a dedicated progress profile for `account.security.reprotect`.
- Success now produces a terminal 100% completion state.
- Failure now produces a terminal failed state instead of leaving the UI stuck on the running message.
- Adds English and Vietnamese completion/failure translations.

### Mod-loader installer Java selection

- Forge and NeoForge installers receive the Java path selected for the instance.
- New-instance installation uses the Java path from instance defaults.
- Loader change, repair, restore, and launch-time profile installation pass the selected Java consistently.
- Invalid custom paths recover to an automatic compatible runtime.
- A Java-specific installer exit is retried once with another compatible runtime.
- Installer logs preserve each attempt and the Java executable used.
- Non-Java installer failures are not retried.

### Legacy Forge “no runtime” false positive

Old Forge profiles can use the Maven artifact `net.minecraftforge:minecraftforge`. The validator previously recognized only `net.minecraftforge:forge` and newer FML component artifacts. Beta 6 recognizes `minecraftforge` as a valid legacy Forge runtime while retaining all existing metadata and file verification.

### Versioning

- Launcher runtime: `v1.1.0-beta.6`
- Update channel: `beta`
- No new MCW Core wheel is published; the build distribution remains `mcw-core 1.1.0b2`.
- The delivery contains launcher diff files only. Files under `src/core/` are the implementation bundled with the launcher; the `mcw_core/` package is unchanged and no standalone Core release is published.

### Validation

- Full test suite: **1312 passed, 82 skipped, 2 warnings**.
- Source and tests pass `compileall`.
- Regression coverage includes Forge 1.6.4 `minecraftforge` runtime detection, mod-loader Java recovery, preferred-Java forwarding, and account-protection progress completion.

### Recommended Windows smoke test

1. Launch a Forge 1.6.4 instance with Forge 9.11.1.1345.
2. Confirm that `The Forge runtime is missing from the launch profile` no longer appears.
3. Select an invalid or incompatible Java executable in Instance Settings, then install or change Forge/NeoForge.
4. Confirm that the launcher selects another compatible Java runtime and retries at most once.
5. Run **Re-protect account credentials** and confirm that progress ends in a clear success or failure state.
