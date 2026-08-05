# MCW Launcher v1.1.0-beta.2

> Beta thứ hai của nhánh 1.1.0, chỉ tập trung vào lựa chọn Java và tự phục hồi khi Java đã chọn không thể chạy Minecraft.

---

# Tiếng Việt

## Phạm vi

v1.1.0-beta.2 xử lý mục **2 — chọn Java theo đường dẫn hoặc tự động, kèm phục hồi khi chọn sai Java**.

Các mục responsive cài mod loader, retry mạng có nút Retry, Forge legacy `--gameDir` và progress kiểm tra bảo vệ tài khoản chưa thuộc bản này.

## Thay đổi giao diện

- Thêm lựa chọn Java rõ ràng cho từng instance:
  - **Tự động (khuyến nghị)**.
  - **Đường dẫn file thực thi tùy chọn**.
- Khi chọn Tự động, ô đường dẫn và nút duyệt Java bị khóa để tránh cấu hình mơ hồ.
- Khi chọn đường dẫn tùy chọn, launcher yêu cầu một file `javaw.exe` hoặc `java.exe` hợp lệ.
- Áp dụng cùng hành vi cho:
  - Trang **Instance Settings**.
  - Trình chỉnh sửa **thiết lập mặc định của instance**.
- Thêm mô tả trực tiếp trong giao diện về cơ chế thử lại Java.

## Tự phục hồi Java

- Nếu đường dẫn tùy chọn bị thiếu, không đọc được phiên bản hoặc không tương thích với Minecraft, MCW bỏ runtime đó và chuyển sang chọn tự động.
- Sau khi tạo process, MCW quan sát ngắn giai đoạn khởi động đầu tiên để nhận diện các lỗi Java có độ tin cậy cao, gồm:
  - `UnsupportedClassVersionError`.
  - Class được biên dịch bằng Java mới hơn runtime hiện tại.
  - JVM không nhận diện phiên bản class.
  - JNI/JVM initialization error.
  - JVM option không được runtime hỗ trợ.
- Khi phát hiện lỗi Java ở giai đoạn này, launcher thử lại **tối đa một lần** bằng:
  1. Một bản Java tương thích khác đã có trên máy; hoặc
  2. Java tương thích do MCW Launcher quản lý.
- Nếu phục hồi thành công từ một đường dẫn tùy chọn, instance được chuyển về chế độ Tự động để không lặp lại lỗi ở lần launch sau.
- Nếu không thể chọn hoặc cài Java thay thế, launcher dừng launch an toàn và trả về lỗi Java rõ ràng.
- Log của lần Java thất bại không còn bị ghi đè khi retry xảy ra trong cùng một giây.

## Tương thích

- Không thay đổi schema `settings.json`; đường dẫn rỗng vẫn đại diện cho chế độ Tự động.
- Instance cũ tự động được ánh xạ sang đúng chế độ:
  - Có `java.path` → Đường dẫn tùy chọn.
  - Không có `java.path` → Tự động.
- `JavaResolver.resolve(...)` vẫn giữ hợp đồng cũ cho caller hiện tại.
- Kết quả launch vẫn giữ các trường chính `javaPath`, `minecraftJavaMajorVersion` và `minecraftVersion`.
- Bản này không thay đổi dữ liệu tài khoản, modpack, provider hoặc cấu trúc instance.

## Xác thực tự động

- Launcher: **1292 passed, 79 skipped, 2 warnings**.
- MCW Core: **130 passed**.
- Wheel `mcw_core-1.1.0b2-py3-none-any.whl` đã được cài vào thư mục độc lập và import public API thành công.
- Metadata đã xác nhận:
  - Runtime: `1.1.0-beta.2`.
  - Python distribution: `1.1.0b2`.

## Kiểm tra thủ công đề xuất

```text
1. Mở Instance Settings và xác nhận chế độ Tự động khóa ô đường dẫn.
2. Chuyển sang Đường dẫn tùy chọn, chọn một javaw.exe hợp lệ và lưu.
3. Chọn Java sai major cho instance, sau đó Launch.
4. Xác nhận launcher tự chọn Java tương thích, launch lại và chuyển setting về Tự động.
5. Thử đường dẫn Java không tồn tại và xác nhận launcher tự phục hồi hoặc báo lỗi rõ ràng nếu không có Java thay thế.
6. Kiểm tra thư mục logs khi có retry và xác nhận log lần đầu không bị ghi đè.
```

---

# English

## Scope

v1.1.0-beta.2 addresses only item **2 — explicit automatic/custom Java selection and recovery from an invalid runtime**.

Responsive mod-loader installation, network Retry UX, the Forge legacy `--gameDir` fix, and account-security progress restoration remain for later betas.

## UI changes

- Add explicit per-instance Java modes:
  - **Automatic (recommended)**.
  - **Custom executable path**.
- Automatic mode disables the path field and browse button.
- Custom mode requires a valid `javaw.exe` or `java.exe` file.
- Apply the same behavior to Instance Settings and the instance-defaults editor.
- Explain the one-time Java recovery behavior directly in the settings UI.

## Runtime recovery

- Invalid, unreadable, or incompatible custom runtimes fall back to automatic selection.
- MCW briefly observes the first process startup for strong Java-runtime mismatch signatures.
- A recognized Java-specific early failure is retried at most once with another compatible local runtime or a launcher-managed runtime.
- Successful recovery clears the rejected custom path and leaves the instance in Automatic mode.
- If no alternative can be selected or installed, launch stops safely with an actionable Java error.
- Same-second retry logs use unique filenames so the first failure log is preserved.

## Compatibility

- No `settings.json` schema migration is required.
- Existing custom paths and automatic settings are inferred exactly as before.
- Existing `JavaResolver.resolve(...)` callers retain the original strict contract.
- Main launch-result fields remain unchanged.

## Automated validation

- Launcher: **1292 passed, 79 skipped, 2 warnings**.
- MCW Core: **130 passed**.
- The `mcw_core-1.1.0b2-py3-none-any.whl` wheel was installed into an isolated directory and its public API imported successfully.
- Verified metadata: runtime `1.1.0-beta.2`, Python distribution `1.1.0b2`.
