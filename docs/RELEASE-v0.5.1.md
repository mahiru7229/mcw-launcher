# MCW Launcher v0.5.1

> Bản Stable đầu tiên của dòng `v0.5.x`, tập trung vào độ ổn định, downloader, Modrinth, Import/Export, bảo mật dữ liệu và trải nghiệm cập nhật rõ ràng hơn.

---

## Tiếng Việt

### Stable channel và chương trình tester

- Tất cả người dùng được chuyển sang **Stable** đúng một lần khi nâng cấp lên `v0.5.1`.
- Người dùng mới luôn sử dụng Stable mặc định.
- Kênh Beta không còn xuất hiện như lựa chọn ngang hàng thông thường.
- Người muốn thử nghiệm có thể bật:

```text
Launcher Settings
└── Launcher updates
    └── Join tester program and receive experimental updates
```

- Khi bật Tester Program, launcher chuyển nội bộ sang channel `beta` để nhận các bản thử nghiệm `v0.6.x`.
- Khi tắt, launcher quay lại `stable` ngay lập tức.
- Tester Program mặc định tắt và có cảnh báo sao lưu instance/world trước khi tham gia.

### Downloader và progress

- Hiển thị tốc độ mạng, dung lượng còn lại và số file còn lại.
- Tổng tốc độ được hiển thị khi nhiều file tải song song.
- Hỗ trợ giới hạn tổng tốc độ tải theo `MB/s`.
- Tốc độ chỉ xuất hiện khi dữ liệu thực sự đang được tải.
- Hỗ trợ retry, resume `.part`, HTTP Range và nhiều URL fallback.
- Modrinth tải song song có giới hạn để cải thiện tốc độ trên máy có latency cao.
- Giảm tần suất progress event và log để hạn chế UI lag.

### Pause và Resume

- Nút Launch chuyển thành Cancel khi đang chuẩn bị hoặc tải.
- Nhấn Cancel tạm dừng tác vụ và giữ file `.part`.
- Nhấn Launch lần sau tiếp tục tải từ phần còn thiếu.
- Theme thiếu PNG Cancel tự fallback về theme mặc định.

### Modrinth

```text
Check toàn bộ
→ Tải toàn bộ file thiếu
→ Check lại
→ Retry tối đa 3 vòng
→ Launch hoặc báo lỗi
```

- File đúng hash chỉ được kiểm tra, không tải lại.
- Có tùy chọn theo từng instance để cho phép người chơi tự tải file lỗi thủ công.
- Giữ tương thích registry và modpack từ các bản beta trước.

### Import và Export

- Import/Export `.mcwpack` sử dụng thanh progress chung.
- Hiển thị file hiện tại, dung lượng đã xử lý, còn lại và phần trăm.
- Export dùng file `.part` và chỉ thay thế file đích khi hoàn tất.
- Import kiểm tra ZIP trước khi ghi dữ liệu.

### Sửa lỗi và bảo mật

- Sửa `WinError 206` bằng classpath manifest JAR.
- Phục hồi version manifest từ cache khi offline.
- Settings JSON lỗi được backup và tự tạo lại an toàn.
- Một instance hỏng không làm mất toàn bộ danh sách.
- Chặn path traversal, symlink và entry ZIP không an toàn.
- Đóng SQLite connection và file log handle đúng cách.
- Giữ tương thích settings, account database và instance cũ.

### Version

```text
Display version: v0.5.1
Version ID: 0.5.1
Update channel: stable
```

### Kiểm thử

```text
659 passed
32 skipped
0 failed
0 errors
```

---

## English

### Stable channel and tester program

- All existing users are migrated to **Stable** once when upgrading to `v0.5.1`.
- New users always default to Stable.
- Beta is no longer shown as a normal equal update-channel choice.
- Users who want experimental builds can enable:

```text
Launcher Settings
└── Launcher updates
    └── Join tester program and receive experimental updates
```

- Enabling the tester program switches the internal channel to `beta` for experimental `v0.6.x` builds.
- Disabling it immediately returns the launcher to `stable`.
- The tester program is disabled by default and includes a backup warning.

### Main improvements

- Faster concurrent Modrinth downloads with bounded workers.
- Reduced UI lag from progress and logging updates.
- Download speed, remaining size, remaining files and global bandwidth limits.
- Retry, resume, partial-file recovery and fallback URLs.
- Pause/Resume through the Launch/Cancel control.
- Full Import/Export progress for `.mcwpack` packages.
- Safer ZIP extraction, settings recovery and resource cleanup.
- Windows long-classpath recovery for `WinError 206`.

### Version

```text
Display version: v0.5.1
Version ID: 0.5.1
Update channel: stable
```

### Testing

```text
659 passed
32 skipped
0 failed
0 errors
```

---

## Installation

1. Download the Windows x64 ZIP package.
2. Extract the complete archive into a new or existing launcher folder.
3. Allow files to be replaced when updating.
4. Run `MCW Launcher.exe`.
5. Do not run the EXE directly from inside the ZIP archive.

Recommended installation path:

```text
C:\MCW
```

## GitHub Release

```text
Tag: v0.5.1
Title: MCW Launcher v0.5.1
Pre-release: disabled
```

Upload only:

```text
MCW-Launcher-v0.5.1-windows-x64.zip
MCW-Launcher-v0.5.1-windows-x64.zip.sha256
```
