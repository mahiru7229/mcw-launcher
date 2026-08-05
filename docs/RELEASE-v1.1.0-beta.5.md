# MCW Launcher v1.1.0-beta.5

## Tiếng Việt

### Phạm vi

Beta 5 sửa lỗi Forge legacy thoát ngay trong LaunchWrapper với `joptsimple.MultipleArgumentsForOptionException`, thường gặp ở Forge 1.12.2 khi `--gameDir` xuất hiện nhiều lần. Nguyên nhân là profile Forge legacy có thể ghép `minecraftArguments` của phiên bản Minecraft gốc với một chuỗi Forge đầy đủ, trong khi custom game arguments cũng có thể thêm lại cùng tùy chọn.

### Thay đổi

- Thêm bước chuẩn hóa game arguments trong pipeline tạo launch command, sau khi metadata và custom arguments đã được hợp nhất nhưng trước khi Java được khởi chạy.
- Nhận diện tùy chọn đơn trị ở cả hai dạng `--option value` và `--option=value`.
- Loại các lần xuất hiện cũ và chỉ giữ lần hợp lệ cuối cùng của mỗi tùy chọn đơn trị.
- Với các tùy chọn launcher kiểm soát như `--gameDir`, `--assetsDir`, `--assetIndex`, `--version` và `--versionType`, luôn dùng giá trị canonical từ launch context.
- Giữ nguyên các tùy chọn được phép lặp như `--tweakClass`; không áp dụng dedup mù cho toàn bộ tham số Forge.
- Kiểm tra mọi tùy chọn đơn trị còn lại có đúng một giá trị không rỗng; nếu lệnh bị hỏng, launcher dừng trước khi tạo tiến trình Java và trả về lỗi rõ ràng.
- Bổ sung regression test mô phỏng Forge 1.12.2/LaunchWrapper với:
  - `minecraftArguments` kế thừa bị ghép lặp `--gameDir`.
  - Xung đột `--gameDir` từ custom game arguments.
  - Dạng inline `--gameDir=...`.
  - Tùy chọn đơn trị thiếu giá trị.
  - `--tweakClass` vẫn được giữ nguyên.

### Phiên bản

- Launcher runtime: `v1.1.0-beta.5`
- Update channel: `beta`
- Không phát hành MCW Core wheel mới; distribution dùng để build vẫn là `mcw-core 1.1.0b2`.
- Patch bàn giao chỉ chứa launcher diff. File triển khai dưới `src/core/` là phần core được bundle trong launcher và chưa được đóng gói thành source/wheel MCW Core riêng.

### Xác thực

- `1304 passed, 81 skipped, 2 warnings` với `PYTHONPATH=.`.
- Regression test mới cho Forge legacy và game-argument normalization đã chạy thành công.
- Toàn bộ source và test đã qua `compileall`.
- Cần smoke test cuối trên Windows với Forge 1.12.2 thực tế để xác nhận LaunchWrapper không còn báo nhiều giá trị cho `gameDir`.

### Không nằm trong Beta 5

- Sửa progress của kiểm tra bảo vệ tài khoản.

---

## English

### Scope

Beta 5 fixes legacy Forge exiting inside LaunchWrapper with `joptsimple.MultipleArgumentsForOptionException`, most commonly on Forge 1.12.2 when `--gameDir` appears more than once. Legacy Forge profiles can concatenate the inherited Minecraft `minecraftArguments` string with another complete Forge argument string, while custom game arguments may introduce the same option again.

### Changes

- Adds a game-argument normalization step after metadata/custom arguments are merged and before the final Java command is spawned.
- Recognizes single-value options in both `--option value` and `--option=value` forms.
- Removes older occurrences and keeps one valid value for every protected single-value option.
- Uses canonical launch-context values for launcher-controlled options such as `--gameDir`, `--assetsDir`, `--assetIndex`, `--version`, and `--versionType`.
- Preserves legitimately repeatable options such as `--tweakClass`; the fix does not blindly deduplicate every Forge argument.
- Validates that each remaining single-value option has exactly one non-empty value. A malformed command fails clearly before a Java process is created.
- Adds regression coverage for Forge 1.12.2/LaunchWrapper scenarios involving:
  - Inherited `minecraftArguments` with duplicate `--gameDir`.
  - Conflicting custom `--gameDir` values.
  - Inline `--gameDir=...` syntax.
  - Missing single-option values.
  - Preserved `--tweakClass` behavior.

### Versioning

- Launcher runtime: `v1.1.0-beta.5`
- Update channel: `beta`
- No new MCW Core wheel is published; the build distribution remains `mcw-core 1.1.0b2`.
- The delivery contains launcher diff files only. The implementation under `src/core/` is the core bundled with the launcher and is not delivered as a separate MCW Core source/wheel package yet.

### Validation

- `1304 passed, 81 skipped, 2 warnings` with `PYTHONPATH=.`.
- The new Forge legacy and argument-normalization regression tests pass.
- All source and test files pass `compileall`.
- Perform a final Windows smoke test with a real Forge 1.12.2 instance to confirm LaunchWrapper no longer reports multiple values for `gameDir`.

### Not included in Beta 5

- Account-protection progress reset fixes.
