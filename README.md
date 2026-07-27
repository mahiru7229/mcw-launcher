# MCW Launcher

<p align="center">
  <strong>Trình khởi chạy Minecraft theo từng instance, được viết bằng Python và PySide6.</strong><br>
  <em>An instance-first Minecraft launcher built with Python and PySide6.</em>
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/releases">
    <img src="https://img.shields.io/badge/Stable-v0.8.1-brightgreen" alt="Current stable version">
  </a>
  <a href="https://github.com/mahiru7229/mcw-launcher/releases">
    <img src="https://img.shields.io/badge/Beta-none-lightgrey" alt="Current beta version">
  </a>
  <a href="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml">
    <img src="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml/badge.svg" alt="Tests">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  </a>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D4" alt="Windows">
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52" alt="PySide6">
</p>

<p align="center">
  <a href="#tiếng-việt">Tiếng Việt</a> ·
  <a href="#english">English</a> ·
  <a href="docs/RELEASE-v0.8.1.md">v0.8.1 release notes</a> ·
  <a href="docs/RELEASE-v0.8.0.md">v0.8.0 release notes</a>
</p>

> [!NOTE]
> `v0.8.1` là Stable hiện tại. Đây là hotfix cho CurseForge, mod/modpack đa loader và launch lock của managed modpack.

---

## Tiếng Việt

### MCW Launcher là gì?

MCW Launcher là launcher Minecraft mã nguồn mở, ưu tiên **instance độc lập**, tiến trình tải rõ ràng, khả năng sửa chữa an toàn và kiến trúc tách biệt giữa GUI với launcher core.

Mỗi instance có thư mục game, phiên bản Minecraft, mod loader, mods, saves, cấu hình Java, RAM và trạng thái runtime riêng. Launcher hiện tập trung cho Windows 10/11 64-bit.

### Bản sửa `v0.8.1`

- Dùng MCW CurseForge Gateway công khai làm endpoint mặc định; API key vẫn chỉ tồn tại phía gateway.
- Không còn coi nhãn Fabric/Forge từ CurseForge là kết luận tuyệt đối: file khớp loader được xếp trước, file khác nhãn vẫn có thể được tải để kiểm tra JAR thật.
- Nhận diện JAR chứa đồng thời `fabric.mod.json` và `META-INF/mods.toml` là mod dùng chung Fabric/Forge.
- Chọn đúng metadata theo loader của instance khi thêm mod.
- Sửa modpack CurseForge bị chặn bởi dependency đa loader gắn nhãn sai.
- Thêm **Mở trong trình duyệt** cho project CurseForge, chỉ chấp nhận liên kết HTTPS thuộc CurseForge.
- Sửa managed modpack không thể thay đổi mod trong chính giai đoạn chuẩn bị launch.

### Điểm nổi bật của `v0.8.0`

- Thêm **MCW LAN Agent** cho Private LAN Offline Mode, giữ nguyên Mojang Authlib và resolve mapping runtime cho Fabric intermediary và Forge SRG.
- Xác nhận luồng host Microsoft + khách Offline hoạt động trên Fabric và Forge 1.20.1; chế độ Microsoft-only không bị thay đổi.
- Nhóm lại Launcher Settings và Instance Settings thành các section rõ ràng, có bố cục compact cho màn hình 1366×768.
- Chuẩn hóa progress theo vòng đời `RUNNING → SUCCEEDED / FAILED / CANCELLED`, bao gồm Java scan, mod/modpack update, repair, import/export, LAN hosting và launcher update.
- Sửa lỗi chọn instance có thể gây `LaunchControlWidget._launch_active` chưa được khởi tạo.
- Sửa bố cục Cửa sổ game để nhãn Chiều rộng/Chiều cao nằm trực tiếp phía trên ô nhập tương ứng.
- Thêm **LAN hosting profiles** trong Instance Settings: chọn `Microsoft only` hoặc `Friends (Microsoft + Offline)` độc lập với `Manual connection` hoặc `e4mc tunnel`. Launcher cài LAN Properties/e4mc theo loader và Minecraft version khi người dùng nhấn Prepare.
- Tích hợp **CurseForge Gateway** công khai mặc định mà không đóng gói API key trong source/release. Có thể cấu hình tối đa năm liên kết HTTPS tùy chỉnh, được che trong giao diện, mã hóa bằng Windows DPAPI và tự động failover theo thứ tự.
- Tìm kiếm, chọn phiên bản và cài **CurseForge mods** cho Fabric/Forge từ Manage Mods hoặc trang Mods độc lập.
- Tự tải file khi tác giả cho phép phân phối qua bên thứ ba; nếu không, launcher hướng dẫn tải thủ công rồi xác minh size/SHA-1 trước khi import.
- Cache JSON CurseForge tối đa **10 MB**, dọn theo LRU, hỗ trợ dữ liệu stale khi gateway tạm lỗi.
- Hiển thị **lần cập nhật gần nhất**, dung lượng cache, nguồn dữ liệu và lỗi refresh gần nhất.
- Cooldown refresh, backoff sau lỗi và request deduplication để hạn chế gọi API trùng hoặc spam gateway.
- Tạo và chạy instance **Vanilla, Fabric hoặc Forge**.
- Sửa luồng Offline trên Forge: tài khoản Offline không còn gọi Microsoft Auth hoặc chèn các auth host giả gây `Auth currently unreachable`.
- Cài đặt, thay đổi và repair Fabric Loader hoặc Minecraft Forge.
- Tìm, cài và cập nhật mod từ **Modrinth** với bộ lọc loader/version/channel.
- Trang **Cài mod** độc lập chỉ hiển thị instance khớp chính xác Minecraft version và loader trước khi cài.
- Cài modpack `.mrpack`, kiểm tra update và **repair file modpack bị thiếu hoặc bị sửa**.
- Backup an toàn trước update/repair và rollback khi thao tác thất bại.
- Cache kết quả xác minh để không hash lại file modpack không đổi ở mỗi lần launch.
- Quản lý RAM bằng **slider + ô nhập MB chính xác**, với ràng buộc `Min ≤ Max ≤ RAM vật lý`.
- Hiển thị màn hình khởi động với tiến trình rõ ràng trong khi launcher chuẩn bị settings, database, tài khoản và giao diện.
- Tự chọn bố cục theo màn hình:
  - `1920×1080` trở lên → cửa sổ `1600×900`.
  - `1366×768` → cửa sổ gọn `1280×720`.
  - Màn hình nhỏ hơn → profile an toàn theo vùng hiển thị khả dụng.
- Launcher và toàn bộ Qt dialog luôn dùng nền tối cùng chữ trắng, không phụ thuộc Light/Dark mode của Windows.
- Sau khi cài hoặc repair loader, progress chuyển rõ ràng sang `100% / READY` thay vì mắc ở trạng thái đang tải.
- Khi launch thất bại, progress chỉ hiện thông báo ngắn; lỗi kỹ thuật đầy đủ nằm trong **Logs**.
- Microsoft OAuth PKCE, nhiều tài khoản Microsoft, SQLite và bảo vệ refresh token bằng Windows DPAPI.
- Theo dõi process Minecraft, thời gian chơi, exit code, game log và crash report.
- Hỗ trợ ngôn ngữ Việt/Anh và theme PNG ngoài EXE; chữ tĩnh đè lên PNG mặc định tắt để artwork của theme hiển thị đúng.

### Tải và chạy

Bản đóng gói dành cho Windows được phát hành tại trang **Releases**:

- [Mở trang phát hành](https://github.com/mahiru7229/mcw-launcher/releases)
- `v0.8.1` là bản Stable hiện tại dành cho người dùng thông thường.
- Các bản thử nghiệm tương lai vẫn chỉ xuất hiện khi người dùng chủ động tham gia tester program.

Yêu cầu cơ bản:

- Windows 10 hoặc Windows 11, 64-bit.
- Kết nối Internet khi tải phiên bản Minecraft, Java, mod loader, mods hoặc modpack lần đầu.
- Đủ dung lượng trống cho assets, libraries, Java runtimes, instances, backups và mods.

Java tương thích có thể được launcher tự phát hiện hoặc tải khi cần.

### Chạy từ source

Python `3.12` được khuyến nghị.

```powershell
git clone https://github.com/mahiru7229/mcw-launcher.git
cd mcw-launcher
git switch main

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python launcher.py
```

### Kiểm thử

```powershell
python -m pytest test -q
```

Quy tắc release của dự án: chỉ build khi test không có `failed` hoặc `error`.

### Build EXE và gói updater

Từ working tree sạch, có thể chạy toàn bộ preflight, test, build và đóng gói bằng một lệnh:

```powershell
.\build_release.ps1
```

Hoặc chạy thủ công:

```powershell
python -m tools.release_preflight
python -m pytest test -q
python -m PyInstaller --clean --noconfirm mcw_launcher.spec
python -m tools.build_release_zip --exe ".\dist\MCW Launcher.exe" --version "0.8.1"
```

Kết quả updater package:

```text
MCW-Launcher-v0.8.1-windows-x64.zip
MCW-Launcher-v0.8.1-windows-x64.zip.sha256
```

Xem thêm [`docs/UPDATE_PACKAGES.md`](docs/UPDATE_PACKAGES.md).

---

## English

### What is MCW Launcher?

MCW Launcher is an open-source Minecraft launcher centered around **isolated instances**, visible download progress, safe repair workflows, and a GUI that remains separate from launcher logic.

Each instance owns its game directory, Minecraft version, mod loader, mods, saves, Java configuration, memory allocation, and runtime state. The project currently targets 64-bit Windows 10 and Windows 11.

### `v0.8.1` hotfix

- Use the public MCW CurseForge Gateway as the default endpoint while keeping the API key on the gateway only.
- Treat CurseForge Fabric/Forge labels as advisory: likely matches are ranked first, while differently labelled files may still be downloaded for real JAR validation.
- Recognize JARs containing both `fabric.mod.json` and `META-INF/mods.toml` as Fabric/Forge universal mods.
- Select metadata matching the target instance loader when adding a mod.
- Fix CurseForge modpacks blocked by incorrectly labelled universal dependencies.
- Add **Open in browser** for CurseForge projects and only accept HTTPS CurseForge links.
- Fix managed modpacks being unable to modify their own files during launch preparation.

### `v0.8.0` highlights

- Add the **MCW LAN Agent** for Private LAN Offline Mode while preserving Mojang Authlib and resolving Fabric intermediary and Forge SRG runtime mappings.
- Verify Microsoft host + Offline guest connections on Fabric and Forge 1.20.1 without changing Microsoft-only mode.
- Group Launcher Settings and Instance Settings into clear sections with a compact layout for 1366×768 displays.
- Standardize progress around `RUNNING → SUCCEEDED / FAILED / CANCELLED` for Java scans, mod/modpack updates, repair, import/export, LAN hosting, and launcher updates.
- Fix instance selection crashing when `LaunchControlWidget._launch_active` had not been initialized.
- Keep the Game window Width/Height labels directly above their matching input fields.
- Add **LAN hosting profiles** under Instance Settings: choose `Microsoft only` or `Friends (Microsoft + Offline)` independently from `Manual connection` or `e4mc tunnel`. The launcher installs compatible LAN Properties/e4mc builds only after the user clicks Prepare.
- Integrate the public **MCW CurseForge Gateway** by default without bundling a CurseForge API key. Up to five custom HTTPS endpoints can be configured, masked in the interface, protected with Windows DPAPI, and tried in order for failover.
- Search, select versions, and install **CurseForge mods** for Fabric/Forge from Manage Mods or the standalone Mods page.
- Download automatically when third-party distribution is allowed; otherwise guide the user through a manual download verified by size and SHA-1.
- Keep a local CurseForge JSON cache capped at **10 MB**, with LRU eviction and stale-data fallback during gateway outages.
- Display the **last successful refresh**, cache size, data source, cooldown, and latest refresh error.
- Coalesce identical requests and apply refresh cooldown/backoff to reduce unnecessary API traffic.
- Create and launch **Vanilla, Fabric, and Forge** instances.
- Restore Offline launches on Forge: Offline accounts no longer call Microsoft Auth or inject invalid auth hosts that cause `Auth currently unreachable`.
- Install, change, and repair Fabric Loader or Minecraft Forge.
- Search, install, and update **Modrinth** mods with loader, version, and release-channel filtering.
- A standalone **Install Mods** page only offers instances matching the selected Minecraft version and loader.
- Install `.mrpack` modpacks, check for updates, and **repair missing or locally modified managed files**.
- Create safety backups before update/repair operations and roll back failed changes.
- Cache successful file verification so unchanged pack files are not hashed on every launch.
- Configure Java memory with a **slider and exact MB input**, enforcing `Min ≤ Max ≤ detected physical RAM`.
- Show a startup screen with clear progress while settings, databases, accounts, and the main interface are prepared.
- Select a responsive display profile automatically:
  - `1920×1080` or larger → `1600×900` window.
  - `1366×768` → compact `1280×720` window.
  - Smaller displays → a safe size based on available screen geometry.
- Force the launcher and Qt dialogs to use a dark palette with white text, independent of the Windows appearance setting.
- Keep launch-progress failures short while preserving complete technical details in **Logs**.
- Support Microsoft OAuth PKCE, multiple Microsoft accounts, SQLite storage, and Windows DPAPI protection for refresh tokens.
- Track the Minecraft process, play time, exit status, latest game log, and detected crash reports.
- Support English/Vietnamese language packs and external PNG themes; static text over themed PNG controls is disabled by default.

### Download and run

Packaged Windows builds are published on the **Releases** page:

- [Open releases](https://github.com/mahiru7229/mcw-launcher/releases)
- `v0.8.1` is the current Stable release for regular users.
- Future experimental builds remain available only after explicitly joining the tester program.

Requirements:

- 64-bit Windows 10 or Windows 11.
- Internet access for first-time Minecraft, Java, loader, mod, and modpack downloads.
- Enough storage for assets, libraries, runtimes, instances, backups, and mods.

A compatible Java runtime can be detected or provisioned automatically.

### Run from source

Python `3.12` is recommended.

```powershell
git clone https://github.com/mahiru7229/mcw-launcher.git
cd mcw-launcher
git switch main

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python launcher.py
```

### Test

```powershell
python -m pytest test -q
```

The release flow requires zero failed tests and zero collection/runtime errors before packaging.

### Build the EXE and updater package

From a clean working tree, run the complete preflight, tests, build, and packaging flow with one command:

```powershell
.\build_release.ps1
```

Or run each step manually:

```powershell
python -m tools.release_preflight
python -m pytest test -q
python -m PyInstaller --clean --noconfirm mcw_launcher.spec
python -m tools.build_release_zip --exe ".\dist\MCW Launcher.exe" --version "0.8.1"
```

Expected updater assets:

```text
MCW-Launcher-v0.8.1-windows-x64.zip
MCW-Launcher-v0.8.1-windows-x64.zip.sha256
```

See [`docs/UPDATE_PACKAGES.md`](docs/UPDATE_PACKAGES.md).

---

## Core capabilities

### Instances and runtime

- Per-instance metadata and settings.
- Create, rename, clone, delete, import, and export.
- `.mcwpack` packages and `.mcwbackup` backups.
- Runtime locks that prevent duplicate launches.
- Transactional restore and full-instance repair without deleting personal content.
- Configurable resolution, fullscreen, JVM/game arguments, Java path, and memory.

### Minecraft and Java

- Modern and legacy Minecraft argument formats.
- Client, library, asset, native, and logging downloads with checksum verification.
- Java scanning through `JAVA_HOME`, PATH, Program Files, Windows Registry, and managed runtimes.
- Compatible Java selection based on Minecraft metadata.
- Automatic runtime provisioning for supported Java majors.

### Mods and modpacks

- Fabric and Forge mod metadata parsing.
- Enable/disable, drag-and-drop, dependency analysis, duplicate-ID detection, and loader mismatch checks.
- Modrinth dependency installation, update checks, update locks, retry/resume, and fallback URLs.
- CurseForge Gateway search, compatible file selection, dependency installation, automatic/manual distribution handling, local JSON caching, refresh cooldown, and stale fallback.
- Managed modpack registry with update, repair, conflict preservation, backup, rollback, and verification cache.

### Accounts and privacy

- Offline and Microsoft accounts.
- Microsoft PKCE/Xbox/XSTS/Minecraft Services flow.
- Windows DPAPI protection for persisted refresh tokens.
- Access tokens kept in memory only.
- Credential and bearer-token redaction in logs and diagnostics.

### Interface

- PySide6 GUI with full and compact display profiles.
- Unified progress for launcher updates, Minecraft files, Java, mods, modpacks, imports, exports, and repairs.
- English and Vietnamese language packs.
- External PNG theme system with per-asset fallback.

---

## Project structure

```text
mcw-launcher/
├── launcher.py
├── mcw_launcher.spec
├── config/
├── docs/
├── lang/
├── src/
│   ├── core/
│   │   ├── account/
│   │   ├── auth/
│   │   ├── backup/
│   │   ├── instance/
│   │   ├── java/
│   │   ├── minecraft/
│   │   ├── mod/
│   │   ├── modloader/
│   │   ├── modrinth/
│   │   ├── curseforge/
│   │   ├── network/
│   │   ├── progress/
│   │   ├── runtime/
│   │   ├── security/
│   │   ├── system/
│   │   ├── theme/
│   │   └── update/
│   ├── gui/
│   └── models/
├── test/
├── themes/
└── tools/
```

The GUI calls public core services instead of implementing Minecraft behavior directly.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/RELEASE-v0.8.1.md`](docs/RELEASE-v0.8.1.md) | v0.8.1 CurseForge and managed-modpack hotfix notes |
| [`docs/RELEASE-v0.8.0.md`](docs/RELEASE-v0.8.0.md) | Complete v0.8.0 Stable release notes |
| [`docs/RELEASE-v0.8.0-beta.3.md`](docs/RELEASE-v0.8.0-beta.3.md) | v0.8.0 Beta 3 GUI and progress stabilization notes |
| [`docs/RELEASE-v0.7.2.md`](docs/RELEASE-v0.7.2.md) | Complete v0.7.2 Stable maintenance release notes |
| [`docs/RELEASE-v0.7.0.md`](docs/RELEASE-v0.7.0.md) | Original v0.7.0 Stable release notes |
| [`docs/RELEASE-v0.6.0.md`](docs/RELEASE-v0.6.0.md) | Complete v0.6.0 Stable release notes |
| [`docs/FORGE_CURSEFORGE.md`](docs/FORGE_CURSEFORGE.md) | CurseForge Gateway, cache and manual fallback |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Core architecture |
| [`docs/INSTANCE_SYSTEM.md`](docs/INSTANCE_SYSTEM.md) | Instance metadata and lifecycle |
| [`docs/MODRINTH_INTEGRATION.md`](docs/MODRINTH_INTEGRATION.md) | Modrinth integration |
| [`docs/FORGE_MODRINTH.md`](docs/FORGE_MODRINTH.md) | Forge and Modrinth behavior |
| [`docs/PACKAGE_FORMAT.md`](docs/PACKAGE_FORMAT.md) | `.mcwpack` format |
| [`docs/UPDATE_PACKAGES.md`](docs/UPDATE_PACKAGES.md) | Updater-compatible release ZIPs |
| [`docs/LANGUAGE_PACKS.md`](docs/LANGUAGE_PACKS.md) | Language pack format |
| [`docs/THEME_ASSET_GUIDE.md`](docs/THEME_ASSET_GUIDE.md) | PNG theme assets and sizes |
| [`docs/gui-api.en.md`](docs/gui-api.en.md) / [`docs/gui-api.vi.md`](docs/gui-api.vi.md) | GUI integration API |

## Support status

| Component | Status in v0.8.1 |
|---|---|
| Vanilla instances | Available |
| Fabric Loader and mods | Available |
| Forge Loader and mods | Available |
| Modrinth mods and `.mrpack` modpacks | Available — update and repair supported |
| Microsoft accounts | Available |
| Offline accounts | Available |
| English / Vietnamese | Available |
| PNG themes | Available |
| NeoForge / Quilt | Not supported |
| CurseForge Gateway mods | Available — public default gateway, universal Fabric/Forge JAR validation, cache and manual fallback |
| CurseForge modpacks | Experimental — Forge flow with universal dependency support |

## Contributing and bug reports

Focused issues and pull requests are welcome. A useful bug report includes:

- MCW Launcher version.
- Windows and screen resolution/DPI.
- Minecraft, Java, and mod-loader versions.
- Reproduction steps.
- Relevant launcher/game logs and screenshots.

Never publish account databases, access/refresh tokens, private worlds, or other personal runtime data.

## License

MCW Launcher is released under the [MIT License](LICENSE).

Copyright © mahiru7229.
