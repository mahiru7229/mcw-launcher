# MCW Launcher v1.1.1-beta.2

## Tiếng Việt

MCW Launcher **v1.1.1-beta.2** là bản hotfix cho các modpack Forge cũ sử dụng **LibLoader** để tải dependency lúc khởi động. Bản này bao gồm toàn bộ tích hợp ATLauncher của Beta 1 và không thay đổi contract public của MCW Core.

### Nguyên nhân

Log thực tế cho thấy Forge 1.12.2 đã nhận đúng instance directory và bắt đầu quét thư mục `mods`. Lỗi xuất hiện sau đó khi coremod LibLoader cố tải các dependency từng được phát hành trên JCenter. JCenter đã ngừng phục vụ các artifact đó, trong khi một số file cũng không tồn tại trên Maven Central, dẫn đến `FileNotFoundException` và FML dừng launch.

Vì vậy, lỗi này không bắt nguồn từ dấu ngoặc, hậu tố `(2)` hay việc truyền `--gameDir`.

### Legacy LibLoader recovery

- Quét manifest của các mod JAR trong instance Forge trước khi Minecraft được khởi chạy.
- Đọc contract `LibLoader-groupN`, `nameN`, `versionN`, `sha512hashN`, `urlN`, `fileN`, `classifierN` và `buildTimeN`.
- Dựng đúng đường dẫn `libraries/` mà LibLoader mong đợi, kể cả thư mục có 16 ký tự đầu của SHA-512 đối với phiên bản có suffix.
- Dùng artifact pipeline hiện có của MCW Launcher để tải, retry giới hạn, giới hạn kích thước và dọn file `.part` khi thất bại.
- Thử URL gốc hợp lệ, hai host Maven Central chuẩn hóa và fallback được giới hạn cho sáu dependency JCenter-only đã biết:
  - `me.nallar.whocalled:WhoCalled:1.1`
  - `com.eclipsesource.minimal-json:minimal-json:0.9.4`
  - `org.minimallycorrect.javatransformer:JavaTransformer:1.8.3`
  - `org.javassist:javassist:3.22.0-CR1`
  - `com.github.javaparser:javaparser-core:3.2.4`
  - `org.json:json:20090211`
- Xác minh **SHA-512 bắt buộc** bằng hash nằm trong manifest của mod. Một mirror chỉ cung cấp byte; nó không được launcher tin cậy nếu hash không khớp.
- Hỗ trợ dependency được nhúng trực tiếp trong mod JAR, với cùng kiểm tra hash và giới hạn dung lượng.
- Tiếp tục quét dependency lồng nhau trong số thư viện vừa khôi phục, với giới hạn tối đa tám vòng để tránh vòng lặp.
- Không tự động tải từ host tùy ý. Dependency custom ngoài allowlist được để cho mod xử lý như hành vi trước đây, thay vì MCW Launcher mở rộng trust boundary.

### Trải nghiệm người dùng

- Progress mới: kiểm tra và khôi phục thư viện mod Forge cũ.
- Nếu có file được khôi phục, kết quả launch chứa một warning tóm tắt số file.
- File đã tồn tại và khớp SHA-512 được dùng lại, không tải lại.
- Instance không dùng Forge không chạy bước này.

### Phiên bản

- Launcher runtime: `v1.1.1-beta.2`
- Update channel: `beta`
- Python distribution metadata: `1.1.1b2`
- Không phát hành MCW Core wheel/source riêng trong beta này. Thay đổi được bundle trong launcher và sẽ được đồng bộ vào Core ở mốc stable theo flow của nhánh 1.1.1.

### Xác thực

- Toàn bộ launcher test suite: `1356 passed, 86 skipped, 2 warnings`.
- Nhóm test Forge/Minecraft/network/config liên quan: `458 passed`.
- Regression test mới bao phủ JCenter fallback, Maven path normalization, SHA-512 cache, embedded dependency, snapshot path, non-Forge bypass và custom-host boundary.
- Python `compileall`: đạt cho `src`, `mcw_core` và `test`.
- Môi trường build không thể chạy RLCraft/Forge GUI thực tế, nên cần smoke test Windows cuối với instance đã tạo lỗi trước đó.

---

## English

MCW Launcher **v1.1.1-beta.2** is a hotfix for older Forge modpacks that use **LibLoader** to obtain dependencies during startup. It includes the complete ATLauncher Beta 1 integration and does not change the public MCW Core contract.

### Root cause

The captured log shows Forge 1.12.2 resolving the intended instance directory and scanning its `mods` folder successfully. Startup fails later when the LibLoader coremod requests dependencies formerly hosted on JCenter. Those artifacts are no longer served there, and several are absent from Maven Central, causing a `FileNotFoundException` that aborts FML startup.

The failure is therefore unrelated to parentheses, a `(2)` suffix, or `--gameDir` quoting.

### Legacy LibLoader recovery

- Scans Forge mod JAR manifests before Minecraft starts.
- Reads the `LibLoader-*` manifest contract and mirrors LibLoader's expected `libraries/` layout.
- Uses MCW Launcher's bounded artifact download pipeline with size limits and partial-file cleanup.
- Tries an allowed original URL, normalized Maven Central hosts, and a narrowly scoped fallback for six known JCenter-only dependencies.
- Requires the downloaded or embedded bytes to match the mod-declared **SHA-512** value.
- Supports embedded dependencies and recursively discovers dependencies from recovered libraries, with an eight-round safety bound.
- Does not automatically trust arbitrary custom hosts; unknown remote sources remain under the mod's original behavior.

### User-facing behavior

- Adds translated progress states for checking and recovering legacy Forge mod libraries.
- Reports a summary warning when files were recovered.
- Reuses a valid SHA-512-verified local file without downloading it again.
- Skips the feature entirely for non-Forge instances.

### Version metadata

- Launcher runtime: `v1.1.1-beta.2`
- Update channel: `beta`
- Python distribution metadata: `1.1.1b2`
- No separate MCW Core wheel/source is published for this beta. The bundled implementation will be synchronized to Core at the stable 1.1.1 milestone.

### Validation

- Full launcher test suite: `1356 passed, 86 skipped, 2 warnings`.
- Related Forge/Minecraft/network/config tests: `458 passed`.
- New regression coverage includes JCenter fallback, Maven path normalization, verified cache reuse, embedded dependencies, snapshot paths, non-Forge bypass, and custom-host boundaries.
- Python `compileall`: passed for `src`, `mcw_core`, and `test`.
- The build environment cannot run a live RLCraft/Forge Windows GUI session, so the previously failing instance still requires a final smoke test.
