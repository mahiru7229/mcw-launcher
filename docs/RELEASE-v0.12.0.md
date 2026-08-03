# MCW Launcher v0.12.0 — Core Separation, Loader Expansion & Stability

## Tiếng Việt

`v0.12.0` là bản Stable hoàn thiện quá trình tách MCW Core khỏi GUI, mở rộng hệ mod loader và gia cố toàn bộ vòng đời instance trước khi Minecraft khởi chạy, trong lúc chạy và sau khi thoát. Bản phát hành bao gồm toàn bộ thay đổi đã xác minh từ chuỗi `v0.12.0-beta.1` đến `v0.12.0-beta.9`.

### Điểm nổi bật

- Hợp nhất pipeline tải artifact cho Modrinth và CurseForge, hỗ trợ retry, xác minh, khôi phục download và fallback tải thủ công rõ ràng hơn.
- Hỗ trợ NeoForge như một loader độc lập và hoàn thiện Quilt Loader, bao gồm cài đặt, launch, repair, diagnostics, mod/modpack và MCW LAN Agent.
- Sửa Java selector để không chọn runtime quá mới cho Minecraft cũ; thêm trình cài Java do launcher quản lý cho Java 8, 17, 21, 25 và JDK GA mới nhất từ Adoptium.
- Công bố package headless `mcw_core`, facade `MCWCore`, public models và CLI `mcw-core-launch`; core có thể import và sử dụng mà không cần PySide6.
- Chuyển GUI sang ranh giới API công khai của `mcw_core`, giữ core độc lập khỏi GUI và Qt.
- Tổ chức lại giao diện theo instance workspace, bổ sung trạng thái runtime, icon instance, badge vòng đời và export/import icon trong `.mcwpack`.
- Thêm transactional staging, operation journal, rollback và startup recovery cho rename, clone, import và delete instance.
- Thêm persisted process supervision, process-session ID, stop an toàn, khôi phục session bị gián đoạn và chống watcher cũ ghi đè kết quả mới.
- Thêm fast instance-health report, cleanup download journal và `.part` an toàn, cùng diagnostic bundle đã redaction với health, sessions và journals.
- Sửa import `.mcwpack` trên Windows khi gặp sharing/access-denied tạm thời; chống duplicate ZIP path xung đột và không ghi đè thư mục không rõ nguồn gốc.
- Sửa crash detection theo từng launch session, tránh crash report cũ làm phiên chạy thành công bị đánh dấu lỗi.
- Cải thiện tài khoản Microsoft: chuyển tài khoản ngay khi chọn, lưu metadata skin và hiển thị skin face trong instance workspace mà không để lỗi tải skin chặn launch.

### Tương thích

- Hỗ trợ cập nhật từ `v0.11.0`, `v0.11.1` và toàn bộ chuỗi thử nghiệm `v0.12.0` qua updater package chuẩn.
- Metadata instance cũ vẫn được migrate; `.mcwpack` format version 1 tiếp tục được hỗ trợ.
- Fabric, Quilt, Forge và NeoForge đều đi qua cùng public core boundary và progress pipeline.
- Stable sử dụng kênh cập nhật `stable`; các bản pre-release tương lai vẫn cần bật tester program.

### Metadata

```text
VERSION = v0.12.0
VERSION_ID = 0.12.0
UPDATE_CHANNEL = stable
MCW Core package = 0.12.0
```

## English

`v0.12.0` is the Stable release that completes the MCW Core/GUI separation, expands loader support, and hardens the full instance lifecycle before launch, while Minecraft is running, and after exit. It includes all verified changes from `v0.12.0-beta.1` through `v0.12.0-beta.9`.

### Highlights

- Unified the Modrinth and CurseForge artifact pipeline with retry, verification, download recovery, and clearer manual-download fallbacks.
- Added NeoForge as a distinct loader and completed Quilt Loader integration across installation, launch, repair, diagnostics, mods/modpacks, and the MCW LAN Agent.
- Corrected Java selection so older Minecraft versions do not receive unnecessarily new runtimes; added launcher-managed Java 8, 17, 21, 25, and latest Adoptium GA installation.
- Published the headless `mcw_core` package, `MCWCore` facade, public models, and `mcw-core-launch` CLI; the core can be imported and used without PySide6.
- Migrated the GUI to the public `mcw_core` boundary while keeping core code independent from GUI and Qt.
- Reorganized the interface around the instance workspace, with runtime states, managed instance icons, lifecycle badges, and `.mcwpack` icon import/export.
- Added transactional staging, operation journals, rollback, and startup recovery for instance rename, clone, import, and deletion.
- Added persisted process supervision, process-session IDs, safe stopping, interrupted-session recovery, and protection against stale watchers overwriting newer results.
- Added fast instance-health reports, safe download-journal and `.part` cleanup, and redacted diagnostic bundles containing health, sessions, and operation journals.
- Fixed Windows `.mcwpack` commits affected by transient sharing/access-denied errors; conflicting duplicate ZIP paths are rejected and unknown directories are preserved.
- Made crash detection launch-session scoped so old crash reports cannot mark a later successful run as crashed.
- Improved Microsoft account UX with immediate account switching, stored skin metadata, and skin-face display without allowing skin download failures to block launch.

### Compatibility

- Supports updates from `v0.11.0`, `v0.11.1`, and the full `v0.12.0` pre-release series through the standard updater package.
- Existing instance metadata remains migratable, and `.mcwpack` format version 1 remains supported.
- Fabric, Quilt, Forge, and NeoForge use the same public core boundary and progress pipeline.
- Stable uses the `stable` update channel; future pre-releases still require tester-program opt-in.

### Metadata

```text
VERSION = v0.12.0
VERSION_ID = 0.12.0
UPDATE_CHANNEL = stable
MCW Core package = 0.12.0
```

## Suggested commit

```text
release: publish MCW Launcher v0.12.0 stable
```
