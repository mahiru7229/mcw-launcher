# Kiến trúc MCW Launcher (v1.8.0)

Tài liệu này mô tả ranh giới kiến trúc áp dụng từ `v1.5.0` và hoàn thiện **tách biệt 100% giữa Core và GUI trong `v1.8.0`**. Mục tiêu là loại bỏ hoàn toàn phụ thuộc chéo, cho phép bất kỳ giao diện người dùng nào (PySide6 hiện tại hoặc Tauri v2 / TypeScript + React / C# trong tương lai) giao tiếp với `mcw-launcher-core` qua chuẩn **JSON-RPC 2.0** hoặc bề mặt API công khai `mcw_core`.

## Các lớp chính

| Lớp | Vị trí | Trách nhiệm |
| --- | --- | --- |
| Entry point | `launcher.py` | Update mode, startup lifecycle, Qt application và báo lỗi khởi động. |
| GUI | `src/gui/` | Widget, dialog, presenter, `GuiCoreRpcBridge` và tương tác người dùng. |
| Public Core & JSON-RPC 2.0 | `mcw_core/`, `mcw_core/rpc/`, `mcw_core/api/`, `mcw_core/api/models/` | Giao thức JSON-RPC 2.0 (`direct`, `stdio` Sidecar, `http` + SSE) và Facade/API công khai ổn định mà GUI và consumer headless được phép sử dụng. |
| Core implementation | `src/core/` | Minecraft, instance, account, network, Java, loader, repair, hotfix và storage (nội bộ). |
| Domain models | `src/models/` | Các object dữ liệu nội bộ (được xuất công khai qua `mcw_core/api/models/`). |
| Runtime data | `lang/`, `themes/`, `runtime/`, `assets/` | Resource được bundle hoặc đặt cạnh executable. |

Luồng phụ thuộc nghiêm ngặt trong `v1.8.0`:

```text
launcher / external GUI -> mcw_core.rpc / mcw_core.api / mcw_core.api.models -> src.core -> src.models
```

- `src/core/` và `src/models/` tuyệt đối không import widget hoặc tạo `QApplication`.
- `src/gui/` và `launcher.py` **tuyệt đối không import trực tiếp `src.core.*` hoặc `src.models.*`**; quy tắc này được kiểm tra tự động bằng cây cú pháp trừu tượng (AST) trong `test/test_v18_gui_core_decoupling.py` và trong `tools/release_preflight.py`.

## Giao thức Kép JSON-RPC 2.0 (`mcw_core.rpc`)

Từ `v1.8.0`, `mcw_core.rpc` hỗ trợ 3 kênh truyền tải (Transport Modes) dùng chung một `CoreRpcDispatcher`:

1. **Direct Mode (`mode="direct"`)**: Tuần tự hóa JSON trực tiếp trong cùng tiến trình Python (`CoreRpcDispatcher.handle_json`), đảm bảo ranh giới dữ liệu thuần JSON với độ trễ bằng 0.
2. **Stdio Sidecar Mode (`mode="stdio"` / `mcw-core-rpc --stdio`)**: Giao tiếp qua `stdin`/`stdout` theo từng dòng JSON-RPC 2.0, phục vụ kiến trúc **Sidecar Process** cho Tauri v2 (Rust + TypeScript/React), Electron hoặc C#.
3. **Local HTTP + SSE Mode (`mode="http"` / `mcw-core-rpc --http`)**: Máy chủ HTTP cục bộ trên `127.0.0.1` cung cấp `GET /health`, `POST /rpc` và stream sự kiện tiến trình thời gian thực qua `GET /events` (Server-Sent Events).

## Startup và I/O

- Import module phải an toàn và không tự tải metadata từ Internet.
- Phát hiện phần cứng đồ họa (`GpuPreferenceManager`) được lưu đệm (`Hardware GPU Caching`) để tăng tốc khởi động ở các lần mở tiếp theo.
- Đồng bộ Hotfix từ Cloudflare Edge CDN (`_start_background_hotfix_sync`) chạy trên luồng nền không chặn giao diện Splash.
- Metadata Minecraft được cache, kiểm tra SHA-1 khi có digest và chỉ dùng cache đã xác minh khi request thất bại.

## Filesystem và dữ liệu không tin cậy

Metadata từ Mojang, loader hoặc content provider là dữ liệu không tin cậy. Identifier và relative path phải được validate trước khi nối với project root. Không chấp nhận absolute path, `..`, drive prefix, NUL hoặc digest không hợp lệ.

Các thư mục runtime chính do `Paths` quản lý:

- `instances/`: dữ liệu game theo instance.
- `cache/`: artifact tải về, metadata và staging.
- `accounts/`: account database; không commit.
- `config/`: launcher settings và cấu hình local; private config không commit.
- `logs/`, `backups/`, `runtimes/`, `hotfixes/`: log, backup, managed Java và bản vá nóng runtime.

## Biên nền tảng

Rule của Minecraft dùng tên chuẩn `windows`, `linux`, `osx` và kiến trúc `x86`, `x64`, `arm64`. Code nghiệp vụ không được giả định `windows`, `javaw.exe`, dấu `;` của classpath hoặc archive ZIP nếu chưa đi qua abstraction theo nền tảng.

## Release gate

Một bản phát hành cần vượt qua:

- `python -m pytest test -v` trên Windows và Linux CI (bao gồm kiểm tra ranh giới AST `0` vi phạm).
- `python -m tools.release_preflight`.
- Smoke test startup, tạo instance, tải game, launch/exit và diagnostics.
- Kiểm tra artifact không chứa account, config private, cache, logs hoặc token.
