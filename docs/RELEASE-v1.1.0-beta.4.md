# MCW Launcher v1.1.0-beta.4

## Tiếng Việt

### Phạm vi

Beta 4 hoàn thiện cơ chế phục hồi các yêu cầu metadata khi mạng hoặc máy chủ gặp lỗi tạm thời. Launcher tự thử lại có giới hạn trước, sau đó cung cấp nút **Thử lại** để người dùng chạy lại đúng yêu cầu vừa thất bại mà không cần đóng cửa sổ hoặc thực hiện lại toàn bộ luồng.

### Thay đổi

- Tự động thử tối đa **3 lần** cho các yêu cầu metadata đã đăng ký.
- Chờ lần lượt **0,5 giây** và **1 giây** trước lần thử thứ hai và thứ ba.
- Chỉ thử lại các lỗi có khả năng phục hồi, gồm timeout, DNS/kết nối tạm thời, reset kết nối và HTTP `408`, `425`, `429`, `500`, `502`, `503`, `504`.
- Không thử lại các lỗi cố định như metadata sai định dạng, loader không hỗ trợ, xác thực thất bại hoặc HTTP `400`, `401`, `403`, `404` và các lỗi client vĩnh viễn khác.
- Sau khi ba lần tự động đều thất bại, hiển thị hộp thoại có nút **Thử lại** và **Hủy**.
- Nút **Thử lại** chạy lại chính xác tác vụ, tham số, trạng thái blocking và thông báo tiến trình của yêu cầu trước đó.
- Mỗi lần thử thủ công bắt đầu một vòng tự động mới có giới hạn; không tạo vòng lặp retry vô hạn.
- Không cho chạy trùng cùng một task ID khi yêu cầu cũ vẫn còn hoạt động.
- Giới hạn số tác vụ mạng được ghi nhớ để không giữ vô hạn các closure truy vấn cũ.
- Mọi lỗi đưa vào log hoặc hộp thoại retry đều được lọc qua `SensitiveDataRedactor`.
- Trạng thái và log phân biệt rõ retry tự động, retry thủ công, hủy retry và trường hợp task không thể khởi động lại.
- Áp dụng cho metadata của:
  - Minecraft version manifest.
  - Fabric, Quilt, Forge và NeoForge.
  - Modrinth mod/modpack và mod catalog.
  - CurseForge project/file catalog.
  - FTB project/version metadata.
  - Resource pack và shader pack từ Modrinth/CurseForge.
- Bổ sung bản dịch tiếng Anh và tiếng Việt cho toàn bộ giao diện retry.
- Bổ sung regression test cho phân loại lỗi mạng, giới hạn ba lần, đăng ký lại đúng task và hành vi nút Retry/Cancel.

### Phiên bản

- Launcher runtime: `v1.1.0-beta.4`
- Update channel: `beta`
- Không thay đổi triển khai trong `src/core/` hoặc `mcw_core/`.
- Không phát hành wheel mới; distribution dùng để build vẫn là `mcw-core 1.1.0b2`.

### Xác thực

- `1299 passed, 81 skipped, 2 warnings` với `PYTHONPATH=.`.
- Toàn bộ source và test đã qua `compileall`.
- Kiểm tra translation coverage đạt: không có literal `tr(...)` mới bị thiếu key.
- Hai test GUI mới cho cơ chế retry được thu thập nhưng bị skip trong môi trường hiện tại vì PySide6 không được cài đặt; cần smoke test hộp thoại Retry/Cancel trực tiếp trên Windows.

### Không nằm trong Beta 4

- Sửa Forge legacy trùng singleton argument như `--gameDir`.
- Sửa progress của kiểm tra bảo vệ tài khoản.

---

## English

### Scope

Beta 4 completes recovery for metadata requests affected by temporary network or provider failures. The launcher first performs bounded automatic retries, then offers a **Retry** button that restarts the exact failed request without requiring the user to close the window or repeat the whole workflow.

### Changes

- Automatically makes up to **3 attempts** for registered metadata requests.
- Waits **0.5 seconds** and **1 second** before the second and third attempts.
- Retries only recoverable failures, including timeouts, temporary DNS/connectivity failures, connection resets, and HTTP `408`, `425`, `429`, `500`, `502`, `503`, and `504`.
- Does not retry permanent failures such as invalid metadata, unsupported loaders, authentication failures, HTTP `400`, `401`, `403`, `404`, and other permanent client errors.
- Shows a dialog with **Retry** and **Cancel** after all three automatic attempts fail.
- **Retry** reruns the exact task, parameters, blocking mode, and progress message from the failed request.
- Each manual retry starts a fresh bounded automatic round; it cannot create an infinite retry loop.
- Prevents duplicate execution of the same task ID while the previous request is still active.
- Caps remembered network-task registrations so old query closures are not retained indefinitely.
- Redacts every error shown in retry logs and dialogs through `SensitiveDataRedactor`.
- Provides distinct status/log messages for automatic retry, manual retry, cancellation, and failure to restart a task.
- Covers metadata for:
  - The Minecraft version manifest.
  - Fabric, Quilt, Forge, and NeoForge.
  - Modrinth mods/modpacks and the mod catalog.
  - CurseForge project/file catalogs.
  - FTB project/version metadata.
  - Modrinth/CurseForge resource packs and shader packs.
- Adds English and Vietnamese translations for the complete retry flow.
- Adds regression coverage for network-error classification, the three-attempt bound, exact task resubmission, and Retry/Cancel behavior.

### Versioning

- Launcher runtime: `v1.1.0-beta.4`
- Update channel: `beta`
- No implementation changes under `src/core/` or `mcw_core/`.
- No new wheel is published; the build distribution remains `mcw-core 1.1.0b2`.

### Validation

- `1299 passed, 81 skipped, 2 warnings` with `PYTHONPATH=.`.
- All source and test files pass `compileall`.
- Translation coverage passes with no newly unresolved literal `tr(...)` calls.
- The two new GUI tests for the retry flow are collected but skipped in the current environment because PySide6 is not installed; perform a Windows smoke test for the Retry/Cancel dialog.

### Not included in Beta 4

- Forge legacy singleton-argument deduplication such as duplicate `--gameDir`.
- Account-protection progress reset fixes.
