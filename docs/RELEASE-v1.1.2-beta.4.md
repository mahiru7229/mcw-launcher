# MCW Launcher v1.1.2-beta.4

## Tiếng Việt

MCW Launcher **v1.1.2-beta.4** là đợt hardening trước stable, tập trung vào độ chính xác của mod preflight và độ ổn định/tốc độ cài mod loader.

### Mod preflight correctness

- `Duplicate enabled mod ID` giờ chỉ so sánh primary/top-level mod IDs; embedded/provided capabilities vẫn dùng để thỏa dependency nhưng không bị báo duplicate giả.
- Giữ duplicate thật giữa hai top-level JAR để phát hiện stale/duplicate mod thực sự.
- Forge/Maven-style version matching hỗ trợ numeric revision như `3.0.1.10`, qualifier như `2.4-Fix`, combined loader versions và danh sách version alternatives như `1.19,1.20.1,`.
- Optional `recommends` và foreign-loader provider metadata của file được modpack pin được hạ xuống informational thay vì launch warning.
- Required dependency do resolver tự thêm có thể được dọn khi manifest hiện tại đã pin cùng provider project hoặc capability đã được embedded; file có SHA1 provenance bị người dùng sửa sẽ không tự động bị xóa.

### Mod-loader installation

- Fabric và Quilt resolve metadata cho các library còn thiếu song song với tối đa 6 worker, vẫn giữ thứ tự profile và dùng shared HTTP client hiện có.
- Forge và NeoForge staging tái sử dụng Vanilla libraries đã có trong MCW library cache để giảm download lặp trong Java installer.
- Java-based Forge/NeoForge installer retry đúng một lần với cùng Java khi output cho thấy lỗi mạng tạm thời; lỗi Java runtime vẫn dùng recovery Java riêng như trước.
- Installer timeout được chuyển thành `JavaRecoveryError` có diagnostic rõ ràng thay vì để `TimeoutExpired` thô thoát ra ngoài.

### Regression coverage

- ATM9-style primary-vs-embedded duplicate identities.
- TerraBlender `3.0.1.10 >= [3.0.1.7,)`, `2.4-Fix >= [2.4,)`, Aether-style combined version strings và Minecraft version alternatives.
- Safe stale managed dependency cleanup và bảo vệ file managed đã bị chỉnh sửa.
- Fabric/Quilt bounded concurrent metadata resolution.
- Forge/NeoForge cached Vanilla library staging.
- Transient installer-network retry và timeout reporting.

### Release metadata

- Launcher runtime: `v1.1.2-beta.4`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b4`

---

## English

MCW Launcher **v1.1.2-beta.4** is a pre-stable hardening pass focused on accurate mod preflight diagnostics and faster, more reliable mod-loader installation.

### Mod preflight correctness

- `Duplicate enabled mod ID` now compares primary/top-level mod IDs only. Embedded/provided capabilities still satisfy dependencies without creating false duplicate warnings.
- Real duplicates between two top-level JARs remain detectable.
- Forge/Maven-style version matching now handles numeric revisions such as `3.0.1.10`, qualifiers such as `2.4-Fix`, combined loader versions, and version alternatives such as `1.19,1.20.1,`.
- Optional recommendations and foreign-loader provider metadata from pack-pinned files are informational rather than launch warnings.
- Resolver-added required dependencies can be removed when the current manifest pins the same provider project or an embedded capability already supplies them; managed files with a recorded SHA1 are preserved if the user modified them.

### Mod-loader installation

- Fabric and Quilt resolve missing library metadata concurrently with at most 6 workers while preserving profile order and the existing shared HTTP client.
- Forge and NeoForge staging reuse Vanilla libraries already present in MCW's library cache to reduce repeated installer downloads.
- Java-based Forge/NeoForge installers retry once with the same Java runtime on clearly transient network failures; Java-runtime recovery remains separate.
- Installer timeouts are reported as diagnostic `JavaRecoveryError` failures instead of leaking raw `TimeoutExpired` exceptions.

### Regression coverage

- ATM9-style primary-versus-embedded duplicate identities.
- Forge/Maven version edge cases, safe stale managed dependency cleanup, bounded Fabric/Quilt metadata concurrency, cached Forge/NeoForge staging, transient installer-network retry, and timeout reporting.

### Release metadata

- Launcher runtime: `v1.1.2-beta.4`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b4`
