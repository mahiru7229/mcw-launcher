# MCW Launcher v0.7.0 Stable

> The first official release of the 0.7 line brings CurseForge gateway support, provider caching, modern Forge command hardening, and the final stability fixes from v0.6.0.

---

## Tiếng Việt

### Bản Stable đầu tiên của dòng 0.7

`v0.7.0` là bản phát hành chính thức đầu tiên của dòng 0.7. Phiên bản này dùng kênh cập nhật `stable`; các bước tối ưu tiếp theo sẽ được phát triển ở dòng `0.7.1`.

```text
VERSION = v0.7.0
VERSION_ID = 0.7.0
UPDATE_CHANNEL = stable
```

### Gateway CurseForge riêng tư

- Source, EXE và updater ZIP **không chứa sẵn link gateway riêng tư**.
- Có thể cấu hình tối đa **5 liên kết HTTPS** trong Launcher Settings.
- Launcher thử các liên kết theo đúng thứ tự và tự chuyển sang link tiếp theo khi gateway trước lỗi mạng, trả JSON không hợp lệ hoặc gặp lỗi HTTP tạm thời.
- Các liên kết được lưu ngoài `launcher_settings.json` tại `config/private/curseforge_endpoints.json`.
- Giá trị được mã hóa bằng **Windows DPAPI** cho tài khoản Windows hiện tại.
- Cả 5 ô luôn bị che mặc định bằng chế độ password.
- Khi bật xem liên kết, launcher hiển thị MessageBox cảnh báo theo ngôn ngữ hiện tại; nút xác nhận bị khóa trong **5 giây**.
- Không ghi các liên kết riêng tư vào log, diagnostic hoặc release package.

> Che trên giao diện và DPAPI giúp giảm lộ ngoài ý muốn, nhưng một ứng dụng desktop không thể giấu tuyệt đối endpoint khỏi người kiểm soát cùng tài khoản Windows hoặc có khả năng quan sát traffic mạng.

### CurseForge mods và modpack

- Tìm kiếm CurseForge theo Fabric/Forge ngay trong trang Mods.
- Chọn file tương thích theo Minecraft version, loader và release channel.
- Cài dependency bắt buộc và dùng batch request để giảm lưu lượng.
- Tải tự động khi tác giả cho phép phân phối qua bên thứ ba.
- Khi không có `downloadUrl`, launcher mở trang chính thức, nhận file người dùng đã tải và xác minh size/SHA-1 trước khi import.
- Cache JSON tối đa `10 MiB`, LRU cleanup, stale fallback, cooldown refresh và failure backoff.
- Luồng modpack CurseForge vẫn nên được dùng thận trọng trên bản sao instance.

### Forge và launcher core

- Sửa cách dựng command Forge hiện đại.
- Giữ Minecraft client JAR trong classpath và không để nó bị resolve thành module Java trùng.
- Bổ sung module-path bootstrap chính xác và `ignoreList` phù hợp.
- Giữ toàn bộ tiến trình tải trên progress thống nhất.
- Đồng bộ forced dark theme, chữ trắng và static text trên PNG mặc định tắt từ v0.6.0.

### Bảo mật và quyền riêng tư

- Microsoft refresh token tiếp tục được bảo vệ bằng Windows DPAPI.
- Microsoft access token chỉ tồn tại trong bộ nhớ.
- Gateway URL riêng tư được bảo vệ riêng theo từng slot DPAPI.
- Log và diagnostic tiếp tục che token/bearer data.
- File cấu hình gateway riêng tư bị loại khỏi Git và updater ZIP.

### Build và kiểm thử

Chạy toàn bộ release flow trên Windows:

```powershell
.\build_release.ps1
```

Script thực hiện preflight, compile, toàn bộ pytest, xóa output cũ, build one-file windowed EXE, tạo updater ZIP và SHA-256. Thời gian cập nhật API JSON vẫn do maintainer tự chỉnh.

Kết quả regression cuối:

```text
789 passed
48 skipped
0 failed
0 errors
```

---

## English

### First official 0.7 release

`v0.7.0` is the first official release of the 0.7 line. It uses the `stable` update channel; subsequent optimization work is planned for the `0.7.1` line.

```text
VERSION = v0.7.0
VERSION_ID = 0.7.0
UPDATE_CHANNEL = stable
```

### Private CurseForge gateways

- The source, EXE, and updater ZIP contain **no bundled private gateway URL**.
- Up to **five HTTPS endpoints** can be configured in Launcher Settings.
- Requests try endpoints in order and move to the next endpoint after network failures, invalid JSON, or transient HTTP failures.
- Links are stored outside `launcher_settings.json` in `config/private/curseforge_endpoints.json`.
- Values are protected with **Windows DPAPI** for the current Windows account.
- All five fields use password masking by default.
- Revealing the links opens a localized warning MessageBox whose confirmation button remains locked for **five seconds**.
- Private links are not written to logs, diagnostics, or release packages.

> Interface masking and DPAPI reduce accidental disclosure, but a desktop application cannot make an endpoint absolutely secret from someone controlling the same Windows account or inspecting its network traffic.

### CurseForge mods and modpacks

- Browse CurseForge Fabric/Forge projects from the Mods page.
- Select compatible files by Minecraft version, loader, and release channel.
- Install required dependencies and use batch requests to reduce traffic.
- Download automatically when third-party distribution is permitted.
- When no `downloadUrl` is available, open the official page and verify the user-selected file by size and SHA-1 before import.
- Keep a `10 MiB` JSON cache with LRU cleanup, stale fallback, refresh cooldown, and failure backoff.
- CurseForge modpack handling should still be used carefully on copied instances.

### Forge and launcher core

- Harden modern Forge command construction.
- Keep the Minecraft client JAR on the classpath instead of allowing it to resolve as a duplicate Java module.
- Build the bootstrap module path and Forge `ignoreList` correctly.
- Preserve unified progress for all downloads.
- Carry forward the forced dark palette, white text, and static text over PNG controls being disabled by default from v0.6.0.

### Security and privacy

- Microsoft refresh tokens remain protected by Windows DPAPI.
- Microsoft access tokens remain memory-only.
- Each private gateway slot is protected with separate DPAPI context.
- Logs and diagnostics continue to redact token/bearer data.
- Private gateway config is excluded from Git and updater ZIPs.

### Build and tests

Run the complete Windows release flow with:

```powershell
.\build_release.ps1
```

The script runs preflight, compilation, the complete pytest suite, cleans old output, builds the one-file windowed EXE, and creates the updater ZIP plus SHA-256. The API JSON publication/update time remains a maintainer-controlled setting.

Final regression result:

```text
789 passed
48 skipped
0 failed
0 errors
```
