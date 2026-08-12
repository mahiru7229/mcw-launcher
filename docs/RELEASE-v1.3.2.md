# MCW Launcher v1.3.2

## Tiếng Việt

MCW Launcher **v1.3.2** là bản ổn định/hardening sau v1.3.1, tập trung vào lỗi filesystem race trên Windows được ghi nhận trong issue #19 và các boundary an toàn đã phát hiện trong review code.

### Sửa WinError 32 / fixed `.tmp` race

- Minecraft version manifest không còn ghi vào tên cố định `version_manifest_v2.json.tmp`.
- Instance registry và metadata quan trọng dùng atomic writer với temporary file riêng cho từng operation.
- Atomic publish dùng `os.replace()` với retry ngắn cho `PermissionError` / Windows sharing violation.
- Cleanup temporary file là best-effort nên lỗi cleanup không còn che mất fallback/cache hợp lệ.
- GitHub release cache cũng dùng cùng atomic writer.

### Filesystem safety

- `Paths.cleanup_short_workspace()` resolve canonical path trước khi `rmtree()`.
- Chặn đường dẫn chứa `..` thoát khỏi short-workspace root.
- Chặn xoá trực tiếp chính short-workspace root.
- Test short-workspace của v1.3.1 được đổi sang tên pytest collect được và bổ sung regression cho hai guard trên.

### Auto-update integrity và lifecycle

- Auto-update không còn cho phép download archive ở chế độ unverified.
- SHA-256 được lấy từ GitHub release asset digest; nếu digest không có, launcher dùng asset `<archive>.sha256`.
- Nếu không có SHA-256 tin cậy, launcher từ chối automatic update thay vì chỉ kiểm tra ZIP hợp lệ.
- `mcw-update.json` là bắt buộc cho update package do v1.3.2+ xử lý.
- Release builder thêm `files` inventory vào manifest mà vẫn giữ `schema_version: 1` để updater v1.3.1 có thể cài v1.3.2.
- Updater v1.3.2+ backup và loại bỏ file từng do release trước quản lý nhưng không còn trong release mới; rollback khôi phục chúng nếu update thất bại.

### Package/theme safety

- Modpack package path validation dùng cùng Windows-safe contract với MCW package importer: reject absolute path, traversal, NUL/control chars, reserved device names, trailing dot/space và ký tự tên file Windows không hợp lệ.
- Theme overwrite import không xoá theme cũ trước khi package mới được publish; theme cũ được tạm backup và restore nếu publish thất bại.

### Release hygiene

- Release preflight kiểm tra `TEST-RESULTS.txt` và `CHANGES.diff` có tham chiếu version hiện tại.
- Release preflight khóa dependency rule: GUI source không được import `src.core` trực tiếp.
- `GUI_ARCHITECTURE.md` được chỉnh để phản ánh đúng trạng thái migration: service calls qua `mcw_core`/`mcw_core.api`, trong khi một số shared DTO vẫn còn ở `src.models`.

### Compatibility

- Update channel: `stable`.
- Package manifest vẫn dùng schema 1 để không phá upgrade path từ v1.3.1.
- Không thay đổi format instance, account database, theme schema hay modpack format.
- Không di chuyển permanent launcher data.

### Version metadata

- Launcher runtime: `v1.3.2`
- Python distribution metadata: `mcw-core 1.3.2`

## English

MCW Launcher **v1.3.2** is a stability and hardening release focused on Windows filesystem races reported in issue #19 and the safety boundaries found during the v1.3.1 code review.

### Highlights

- Replaces deterministic temporary filenames in the affected manifest/instance state paths with per-operation atomic writes and retryable `os.replace()` publishing.
- Canonicalizes short-workspace cleanup paths before recursive deletion and refuses both parent escapes and deletion of the workspace root itself.
- Requires a trusted SHA-256 for automatic launcher updates, using either the GitHub release asset digest or the matching `.sha256` sidecar asset.
- Requires an update package manifest and records managed release files while retaining manifest schema 1 for v1.3.1 compatibility.
- Adds managed-file removal with rollback for updater versions running v1.3.2 or later.
- Aligns modpack archive path validation with the existing Windows-safe MCW package policy.
- Makes theme overwrite publishing transactional.
- Extends release preflight to catch stale release evidence and direct GUI-to-implementation imports.

### Version metadata

- Launcher runtime: `v1.3.2`
- Update channel: `stable`
- Python distribution metadata: `mcw-core 1.3.2`
