# Kiến trúc MCW Launcher

Tài liệu này mô tả ranh giới kiến trúc áp dụng từ `v1.5.0-beta.4`. Mục tiêu là giảm phụ thuộc chéo, giữ startup không bị network I/O ngầm và chuẩn bị implementation đa nền tảng.

## Các lớp chính

| Lớp | Vị trí | Trách nhiệm |
| --- | --- | --- |
| Entry point | `launcher.py` | Update mode, startup lifecycle, Qt application và báo lỗi khởi động. |
| GUI | `src/gui/` | Widget, dialog, presenter và tương tác người dùng. |
| Public core | `mcw_core/`, `mcw_core/api/` | Facade/API ổn định mà GUI và consumer headless được phép sử dụng. |
| Core implementation | `src/core/` | Minecraft, instance, account, network, Java, loader, repair và storage. |
| Domain models | `src/models/` | Các object dữ liệu không phụ thuộc GUI. |
| Runtime data | `lang/`, `themes/`, `runtime/`, `assets/` | Resource được bundle hoặc đặt cạnh executable. |

Luồng phụ thuộc mong muốn:

```text
launcher -> GUI -> public core -> core implementation -> models
```

Core implementation không được import widget hoặc tạo `QApplication`. GUI không được import trực tiếp `src.core`; quy tắc này được kiểm tra trong release preflight.

## Startup và I/O

- Import module phải an toàn và không tự tải metadata từ Internet.
- Network I/O chỉ bắt đầu từ một operation rõ ràng, có timeout và lỗi có ngữ cảnh.
- Metadata Minecraft được cache, kiểm tra SHA-1 khi có digest và chỉ dùng cache đã xác minh khi request thất bại.
- Task dài phải đi qua task runner/progress callback để không chặn GUI thread.

## Filesystem và dữ liệu không tin cậy

Metadata từ Mojang, loader hoặc content provider là dữ liệu không tin cậy. Identifier và relative path phải được validate trước khi nối với project root. Không chấp nhận absolute path, `..`, drive prefix, NUL hoặc digest không hợp lệ.

Các thư mục runtime chính do `Paths` quản lý:

- `instances/`: dữ liệu game theo instance.
- `cache/`: artifact tải về, metadata và staging.
- `accounts/`: account database; không commit.
- `config/`: launcher settings và cấu hình local; private config không commit.
- `logs/`, `backups/`, `runtimes/`: log, backup và managed Java.

## Biên nền tảng

Rule của Minecraft dùng tên chuẩn `windows`, `linux`, `osx` và kiến trúc `x86`, `x64`, `arm64`. Code nghiệp vụ không được giả định `windows`, `javaw.exe`, dấu `;` của classpath hoặc archive ZIP nếu chưa đi qua abstraction theo nền tảng.

Trong Alpha 2, native selection, Java discovery/provisioning, archive extraction và credential protection đã có nhánh Linux. Executable packaging, Forge-family smoke test và một số OS integration vẫn cần hoàn thiện trước khi Linux được đánh dấu stable.

Từ Beta 2, thao tác mở file/thư mục đi qua `src.gui.platform_open`: Linux ưu tiên freedesktop handler (`xdg-open`, rồi `gio open`) và Qt là fallback đa nền tảng.

## Nguyên tắc refactor

1. Giữ public API tương thích hoặc ghi migration note.
2. Tách một responsibility có test trước khi di chuyển code lớn.
3. Không thêm wrapper chỉ để đổi tên; abstraction phải loại bỏ phụ thuộc hoặc duplication thực tế.
4. Mọi downloader mới phải có timeout, status handling, checksum và ghi file an toàn.
5. Không thay đổi schema dữ liệu bền vững mà thiếu migration/fallback.

## Release gate

Một release candidate cần vượt qua:

- `python -m pytest test -v` trên Windows và Linux CI.
- `python -m tools.release_preflight`.
- Smoke test startup, tạo instance, tải game, launch/exit và diagnostics.
- Kiểm tra artifact không chứa account, config private, cache, logs hoặc token.
