# MCW Launcher v0.11.0-beta.2 — Theme Authoring Toolkit

## Tiếng Việt

Beta 2 biến hệ thống theme/animation của v0.11 thành một workflow có thể sử dụng trực tiếp trong launcher.

### Thay đổi chính

- Thêm cửa sổ **Validation details** với mức độ và nhóm lỗi rõ ràng.
- Thêm các thao tác **Open folder**, **Duplicate**, **Import ZIP** và **Export ZIP**.
- Export theme kèm báo cáo SHA-256 cho từng file.
- Import ZIP được bảo vệ khỏi path traversal, symlink, archive quá lớn và file script/executable.
- Thêm live reload có debounce cho manifest, PNG, font và QSS.
- Khi file đang chỉnh dở bị lỗi, launcher giữ theme hợp lệ gần nhất.
- Mở rộng preview với mẫu font tiếng Việt, button thường/chính/disabled, dialog, state, progress và toast.
- Thêm theme schema 6 với custom stylesheet QSS cục bộ, giới hạn an toàn và không hỗ trợ `@import`/`url()`.
- Lưu lựa chọn live reload trong launcher settings schema 12.
- Thêm tài liệu Theme Authoring Toolkit và template tối thiểu.

## English

Beta 2 turns the v0.11 theme and animation system into an authoring workflow that can be used directly inside the launcher.

### Main changes

- Added a detailed validation dialog with severity and issue categories.
- Added Open folder, Duplicate, Import ZIP, and Export ZIP actions.
- Theme exports include per-file SHA-256 checksums.
- ZIP imports reject traversal, symlinks, oversized archives, scripts, and executables.
- Added debounced live reload for manifests, PNG assets, fonts, and QSS.
- Invalid in-progress edits keep the last valid theme active.
- Expanded preview coverage for Vietnamese glyphs, default/primary/disabled buttons, dialogs, states, progress, and toasts.
- Added theme schema 6 with a validated local QSS stylesheet and no `@import`/`url()` directives.
- Persisted live reload through launcher settings schema 12.
- Added authoring documentation and a minimal template.

## Metadata

- Version: `v0.11.0-beta.2`
- Update channel: `beta`
