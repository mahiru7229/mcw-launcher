# MCW Launcher v0.11.1

## Tiếng Việt

Đây là bản vá bảo trì cho **MCW Launcher v0.11**.

### Thay đổi

- Cố định line ending **LF** cho các tài liệu Theme Runtime Contract.
- Sửa lỗi SHA-256 contract không khớp khi checkout hoặc chạy test trên Windows.
- Khôi phục tính nhất quán của `release_preflight` và Theme Contract Audit.
- Bổ sung regression test để ngăn tài liệu contract bị chuyển lại sang CRLF.
- Không thay đổi Theme Schema, runtime, tính năng launcher hoặc dữ liệu người dùng.

### Tương thích

- Có thể cập nhật trực tiếp từ **v0.11.0**.
- Không cần tạo lại instance, tài khoản hoặc theme.
- Theme schema 1–6 tiếp tục hoạt động bình thường.

### Kiểm tra phát hành

```text
Full test suite: passed
Release preflight: passed
Theme contract audit: passed
```

---

## English

This is a maintenance patch for **MCW Launcher v0.11**.

### Changes

- Enforced **LF** line endings for Theme Runtime Contract documents.
- Fixed SHA-256 contract mismatches when checking out or testing the project on Windows.
- Restored consistent `release_preflight` and Theme Contract Audit results.
- Added regression coverage to prevent contract documents from being converted back to CRLF.
- No changes to the Theme Schema, launcher runtime, features, or user data.

### Compatibility

- Direct update from **v0.11.0** is supported.
- Instances, accounts, and themes do not need to be recreated.
- Theme schemas 1–6 remain fully supported.

### Release validation

```text
Full test suite: passed
Release preflight: passed
Theme contract audit: passed
```
