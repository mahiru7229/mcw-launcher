# MCW Launcher v1.1.1-beta.5 — Pack dependency compatibility hotfix

## Tiếng Việt

Hotfix này sửa trường hợp launcher chặn một modpack đã hoạt động hợp lệ chỉ vì bộ so sánh phiên bản nội bộ diễn giải khác Forge hoặc tác giả modpack.

### Chính sách mới

- Dependency bắt buộc bị thiếu hoặc bị disable vẫn chặn launch.
- Nếu mod yêu cầu và dependency đã cài đều được đánh dấu là file do cùng pipeline modpack quản lý, phiên bản mà manifest ghim được chấp nhận.
- Nếu parser nội bộ vẫn cho rằng version range không khớp, launcher chỉ ghi warning `pack-pinned-dependency-requirement`; warning này không nằm trong nhóm lỗi dependency chặn launch.
- Dependency do người dùng tự thêm vẫn bị kiểm tra nghiêm và tiếp tục tạo lỗi `dependency-version` khi thực sự không đạt yêu cầu.

### Trường hợp regression

- Elytra Slot / Caelus: `1.19.2-3.0.0.6` với `[1.19-3.0.0.3,)`
- Elytra Slot / Curios: `1.19.2-5.1.4.3` với `[1.19-5.1.0.0,)`
- Quark / AutoRegLib: `1.8.2-55` với `[1.8-54,)`
- Sky GUIs / LibX: `1.19.2-4.2.8` với `[1.19-4.0.7,)`
- Sky GUIs / Skyblock Builder: `1.19.2-4.2.18` với `[1.19-4.0.12,)`

### Xác thực

- `1382 passed, 88 skipped, 2 warnings`
- `compileall` đạt cho `src` và `test`

## English

This hotfix prevents MCW from blocking a working managed modpack merely because the launcher's internal version parser disagrees with Forge metadata or the pack author's pinned selection.

Missing or disabled required dependencies remain blocking. A version mismatch becomes a non-blocking pack-pinned warning only when both sides of the dependency relation are managed by the modpack. Manually added dependencies remain strictly validated.
