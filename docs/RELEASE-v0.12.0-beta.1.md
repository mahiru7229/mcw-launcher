# MCW Launcher v0.12.0-beta.1

## Tiếng Việt

### Unified Provider Artifact Pipeline

- Hợp nhất flow tải artifact của Modrinth và CurseForge trên service trung lập trong core.
- Phân loại lỗi tải có cấu trúc: thiếu URL, timeout, DNS/TLS, HTTP 403/404/429/5xx, reset kết nối, sai size/hash, lỗi file, hết dung lượng và hủy tải.
- Giữ direct URL, trang file/version và project page để tải thủ công khi tự động tải thất bại.
- Hỗ trợ Retry, chọn file đã tải và xác minh file thủ công bằng size/hash.
- Cho phép artifact do manifest quản lý dùng mọi extension, bao gồm ZIP trong thư mục `mods`, mà không ép `.jar` hoặc tự giải nén.
- File thủ công khác tên/extension vẫn được chấp nhận khi hash đúng và được đặt lại theo filename/path mà manifest yêu cầu.
- Cancel dừng retry, không bắt đầu artifact tiếp theo và xóa file `.part`.
- Resolve `${file.jarVersion}` từ `MANIFEST.MF`, provider metadata, filename rồi mới fallback thành `Unknown`.
- Cập nhật metadata sang `v0.12.0-beta.1`, kênh `beta`.

## English

### Unified Provider Artifact Pipeline

- Unified Modrinth and CurseForge artifact downloads behind a provider-neutral core service.
- Added structured failure reasons for missing URLs, timeouts, DNS/TLS, HTTP 403/404/429/5xx, connection resets, size/hash mismatches, file access, disk space, and cancellation.
- Preserved direct download, file/version, and project links for manual fallback.
- Added manual-file verification by size/hash and support for retrying or choosing a downloaded file.
- Manifest-managed artifacts may use any extension, including ZIP files inside `mods`, without forced `.jar` validation or extraction.
- A manually selected file with a different name or extension is accepted when its hash matches, then committed to the manifest-required filename and path.
- Cancellation stops retry/backoff, prevents the next artifact from starting, and removes `.part` files.
- Resolved `${file.jarVersion}` through JAR manifest metadata, provider metadata, filename inference, then `Unknown`.
- Updated release metadata to `v0.12.0-beta.1` on the `beta` channel.
