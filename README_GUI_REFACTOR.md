# MCW Launcher — GUI SRP + Managed Java

Bộ file này giữ GUI PySide6 theo kiến trúc SRP và bổ sung cơ chế tự tải Java khi Minecraft cần runtime chưa có.

## Cách áp dụng

1. Tạo branch hoặc sao lưu repo hiện tại.
2. Giải nén gói này.
3. Chạy PowerShell:

```powershell
.\apply_gui_refactor.ps1 -RepoPath "D:\path\to\mcw-launcher"
```

Hoặc chép thủ công `launcher.py`, `src/` và `test/` vào repo, cho phép ghi đè các file trùng tên.

## Managed Java

Launcher chỉ quản lý ba major:

| Java Minecraft yêu cầu | Runtime launcher dùng |
|---|---:|
| Không có metadata hoặc `<= 8` | Java 8 |
| `9` đến `17` | Java 17 |
| `18` đến `25` | Java 25 |

Nếu metadata yêu cầu Java lớn hơn 25, launcher báo lỗi rõ ràng thay vì dùng runtime không tương thích.

### Luồng hoạt động

1. Đọc `version.json` của Minecraft.
2. Chuẩn hóa major về `8`, `17` hoặc `25`.
3. Tìm đúng major đã cài trên máy.
4. Nếu thiếu, tải Eclipse Temurin JDK cho Windows x64.
5. Kiểm tra SHA-256.
6. Giải nén an toàn vào thư mục tạm.
7. Di chuyển nguyên tử vào thư mục runtime của launcher.
8. Chạy bằng `javaw.exe` vừa cài.

Runtime được lưu tại:

```text
<launcher-root>/runtimes/java-8/
<launcher-root>/runtimes/java-17/
<launcher-root>/runtimes/java-25/
```

Đây là bản cài portable: không chạy MSI, không sửa registry, không cần quyền quản trị và không thay đổi `JAVA_HOME` của Windows.

### Progress mới

```text
selecting_java
downloading_java
installing_java
```

GUI hiện tại nhận `ProgressEvent` tổng quát nên thanh tiến trình tải Java hoạt động mà không cần nhét logic Java vào `MainWindow`.

## Phân chia trách nhiệm

- `JavaMajorPolicy`: ánh xạ major Minecraft sang 8/17/25.
- `AdoptiumClient`: tìm URL bản Temurin mới nhất và checksum.
- `JavaArchiveDownloader`: tải file và báo byte progress.
- `JavaChecksum`: xác minh SHA-256.
- `JavaArchiveExtractor`: giải nén an toàn.
- `ManagedJavaRepository`: quản lý đường dẫn runtime.
- `JavaProvisioner`: điều phối tìm/tải/cài runtime.
- `JavaSelector`: public entry point để lấy `javaw.exe`.
- `MinecraftExecutor`: quyết định thời điểm gọi Java selector, không tự tải hay giải nén.

## Chạy test

```bash
pytest test/core/java
```

Các test bổ sung kiểm tra mapping major và chống ZIP Slip.

## Chạy launcher

```bash
python launcher.py
```

## Phạm vi hiện tại

Managed Java đang hướng tới Windows x64, đúng với target build hiện tại của MCW Launcher. Java được tải dưới dạng JDK ZIP để cả Java 8, 17 và 25 dùng cùng một pipeline ổn định.
