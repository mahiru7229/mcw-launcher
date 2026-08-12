# MCW Launcher v1.3.1

## Tiếng Việt

MCW Launcher **v1.3.1** là hotfix cho lỗi cài Java/modpack trên một số máy Windows khi launcher được chạy từ thư mục có đường dẫn sâu.

### Short installation workspace

- Các tác vụ tạm thời không còn phụ thuộc vào toàn bộ launcher root dài.
- Java/JVM extraction dùng `%LOCALAPPDATA%\MCW\t\jvm\<id>` trên Windows.
- Forge staging dùng `frg`, NeoForge dùng `neo`, Modrinth dùng `mrd`.
- Workspace ID được rút xuống 8 ký tự thay vì UUID 32 ký tự ở các staging mới.
- Permanent data (`instances`, `cache`, `runtimes`, settings) vẫn ở launcher root mà người dùng chọn.
- Temporary workspace được cleanup khi task hoàn tất hoặc lỗi.

### Windows long-path hardening

- Java archive extraction dùng Windows extended-path filesystem operations khi chạy trên Windows.
- Modrinth override extraction/copy và CurseForge override extraction dùng cùng filesystem boundary để không phụ thuộc vào giới hạn Win32 `MAX_PATH` cổ điển.
- CurseForge overrides được stage qua short workspace `cfr` trước khi publish vào instance.
- Unified download I/O và Modrinth verification cũng dùng extended-path-aware filesystem boundary.
- Regression tests khóa lại hai path đã gây lỗi thực tế trên Windows 10: Java 8 `DirectoryScannerConfig.java` và Modrinth `zlm_arab.json`.

### Compatibility

- Không thay đổi Shared Storage/ContentStore lifecycle của v1.3.0.
- Không thay đổi Provider API Cache.
- Không di chuyển instance hay cache của người dùng sang root mới.
- Forge và NeoForge vẫn giữ implementation riêng.

### Version metadata

- Launcher runtime: `v1.3.1`
- Update channel: `stable`
- Python distribution metadata: `mcw-core 1.3.1`

## English

MCW Launcher **v1.3.1** is a Windows compatibility hotfix for Java/modpack installation failures when the launcher is stored under a deeply nested directory.

### Highlights

- Temporary installation work now uses a short Windows workspace under `%LOCALAPPDATA%\MCW\t`.
- Human-readable three-character prefixes: `jvm`, `frg`, `neo`, `mrd`, and `cfr`.
- Java extraction, Modrinth override extraction/copy, and CurseForge override extraction use an extended-path-aware filesystem boundary on Windows.
- Permanent launcher data remains portable at the user-selected launcher root.
- Regression coverage includes the exact long Java and Modrinth paths observed in diagnostics from the affected Windows 10 machine.

### Version metadata

- Launcher runtime: `v1.3.1`
- Update channel: `stable`
- Python distribution metadata: `mcw-core 1.3.1`
