# MCW Launcher v0.9.0-beta.2

> Unified Download Engine 2: shared connections, resumable `.part` files, classified retries, controlled concurrency, pause/resume, cancellation, and a persistent download journal.

---

## 🇻🇳 Tiếng Việt

### Điểm nổi bật

- Thêm **Download Engine 2** dùng chung cho các file tải xuống của launcher.
- Dùng một `httpx.Client` chia sẻ để tái sử dụng kết nối và giảm chi phí thiết lập kết nối mới.
- Tải vào file `.part`, xác minh checksum rồi mới thay thế file đích theo kiểu atomic.
- Hỗ trợ tiếp tục tải bằng HTTP Range khi máy chủ cho phép.
- Giữ file tải dở sau lỗi mạng hoặc khi người dùng hủy, để lần sau có thể tiếp tục.
- Thêm retry policy phân biệt lỗi tạm thời và lỗi cố định.
- Thêm giới hạn tổng số lượt tải và giới hạn theo từng host.
- Thêm thiết lập số lượt tải đồng thời trong Launcher Settings.
- Nâng cấp nút Launch thành **Tạm dừng / Tiếp tục**, kèm nút **Hủy** riêng.
- Thêm download journal để ghi nhận file đang tải, tạm dừng, bị hủy hoặc thất bại.

### Hệ thống tải thống nhất

Các luồng sau sử dụng engine mới trực tiếp hoặc thông qua lớp tương thích `HttpDownloader`:

```text
Minecraft client
Libraries và natives
Assets
Java runtime
Modrinth files
CurseForge files và modpack archives
Launcher update archive
Repair Center downloads
```

Các module cũ vẫn có thể gọi `HttpDownloader`, nhưng việc tải file được điều phối qua cùng session, bandwidth limiter, retry policy và journal.

### File `.part` và atomic replace

Launcher không ghi trực tiếp vào file đích:

```text
example.jar.part
→ tải hoàn tất
→ kiểm tra kích thước và checksum
→ atomic replace thành example.jar
```

File `.part` không bao giờ được coi là file hoàn chỉnh. Nếu checksum sai, file tạm bị xóa trước khi retry.

### Resume bằng HTTP Range

Khi đã có file tải dở:

```text
Range: bytes=<kích-thước-hiện-tại>-
```

Launcher chỉ nối tiếp khi máy chủ trả `206 Partial Content` cùng `Content-Range` hợp lệ. Nếu máy chủ không hỗ trợ hoặc trả range sai, launcher xóa phần tải dở không an toàn và tải lại từ đầu.

### Retry policy

Được retry với exponential backoff:

```text
Timeout
Connection reset
HTTP 408 / 409 / 425 / 429
HTTP 5xx
Checksum hoặc kích thước sai trong giới hạn retry
```

Không retry vô ích:

```text
HTTP 400 / 401 / 403 / 404 / 410 / 422
CurseForge manual_download_required
Permission denied
Disk full
Read-only filesystem
Unsafe path hoặc invalid URL
Người dùng hủy tác vụ
```

`Retry-After` của HTTP 429/503 được tôn trọng khi có.

### Nguồn tải dự phòng

Một request có thể chứa nhiều URL đã được xác minh. Khi nguồn đầu tiên gặp lỗi cố định, engine chuyển sang nguồn tiếp theo thay vì retry cùng URL nhiều lần.

Checksum và kích thước vẫn được kiểm tra sau khi tải từ nguồn dự phòng.

### Concurrency

Launcher Settings có lựa chọn:

```text
Automatic (recommended)
2 / 4 / 6 / 8 / 12 / 16 simultaneous downloads
```

Mặc định Automatic dùng 6 lượt tải tổng và tối đa 3 lượt cho cùng một host. Bandwidth limit hiện có vẫn được áp dụng trên toàn bộ engine.

### Pause, Resume và Cancel

Trong lúc Launch đang chuẩn bị hoặc tải file:

```text
Pause
→ worker vẫn được giữ
→ file và queue không bị mất

Resume
→ tiếp tục ngay trong cùng task

Cancel
→ kết thúc task an toàn
→ giữ file .part hợp lệ để lần sau resume
```

Nút Pause/Resume và Cancel được tách riêng để tránh nhầm giữa tạm dừng và hủy hoàn toàn.

### Download journal

Journal được lưu tại cache của launcher và dùng atomic write. Nó ghi:

```text
request ID
operation ID
source
file đích
file .part
host
trạng thái
số byte đã tải
kích thước dự kiến
lỗi rút gọn
thời gian cập nhật
```

Journal **không lưu URL đầy đủ**, query token, header xác thực hoặc API key.

Các trạng thái có thể phục hồi:

```text
downloading
paused
cancelled
failed
```

### Launcher updater

Archive cập nhật launcher giờ được tải qua Download Engine 2:

- file `.part`;
- resume;
- giới hạn kích thước;
- SHA-256 khi release metadata cung cấp;
- atomic replace sau xác minh.

### Tương thích

- Giữ API `HttpDownloader` để các manager cũ và plugin nội bộ không bị gãy.
- Giữ cơ chế manual recovery của CurseForge.
- Giữ progress, bandwidth limit và Repair Center của Beta 1.
- Settings schema được nâng lên phiên bản 9 và tự migration.

---

## 🇬🇧 English

### Highlights

- Added a unified **Download Engine 2** for launcher file transfers.
- Added a shared `httpx.Client` with connection pooling.
- Downloads now use `.part` files and atomic replacement after verification.
- Added HTTP Range resume with strict `Content-Range` validation.
- Retry behavior now distinguishes temporary and permanent failures.
- Added global and per-host concurrency limits.
- Added a simultaneous-download setting to Launcher Settings.
- Added true **Pause / Resume** behavior and a separate **Cancel** action.
- Added an atomic, sanitized download journal.

### Retry classification

Temporary network failures, rate limits, and supported server errors use bounded exponential backoff. Authentication errors, restricted CurseForge files, invalid paths, disk failures, and user cancellation stop immediately.

### Safety

- Final files appear only after size and checksum verification.
- Invalid partial data is removed before a clean retry.
- Restricted or manual CurseForge downloads are not retried repeatedly.
- Journal entries do not contain full URLs, credentials, authorization headers, or API keys.

### Version information

```text
Version: v0.9.0 Beta 2
Version ID: 0.9.0-beta.2
Release channel: beta
Settings schema: 9
```

### Testing target

This beta focuses on network reliability and recovery. Test interrupted downloads, pause/resume, cancellation, bandwidth limiting, CurseForge manual recovery, Java downloads, Repair Center, and launcher updates before promotion to the next milestone.
