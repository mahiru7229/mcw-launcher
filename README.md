# MCW Launcher

<p align="center">
  <strong>Trình khởi chạy Minecraft theo từng instance, được viết bằng Python và PySide6.</strong><br>
  <em>An instance-first Minecraft launcher built with Python and PySide6.</em>
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/releases">
    <img src="https://img.shields.io/badge/Stable-v0.9.0-brightgreen" alt="Current stable version">
  </a>
  <a href="https://github.com/mahiru7229/mcw-launcher/releases">
    <img src="https://img.shields.io/badge/Beta-v0.10.0--beta.1-orange" alt="Current opt-in beta version">
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
  <a href="docs/RELEASE-v0.9.0.md">v0.9.0 release notes</a> ·
  <a href="docs/RELEASE-v0.10.0-beta.1.md">v0.10.0 Beta 1 notes</a> ·
  <a href="docs/UPDATE_PACKAGES.md">Updater packages</a>
</p>

> [!NOTE]
> `v0.9.0` là bản Stable hiện tại. `v0.10.0-beta.1` là bản thử nghiệm opt-in; Stable vẫn là kênh mặc định.

---

## Tiếng Việt

### MCW Launcher là gì?

MCW Launcher là launcher Minecraft mã nguồn mở, ưu tiên **instance độc lập**, tiến trình tải rõ ràng, khả năng sửa chữa an toàn và kiến trúc tách biệt giữa GUI với launcher core.

Mỗi instance có thư mục game, phiên bản Minecraft, mod loader, mods, saves, cấu hình Java, RAM và trạng thái runtime riêng. Launcher hiện tập trung cho Windows 10/11 64-bit.

### Điểm nổi bật của `v0.9.0`

- Thêm **Repair Center** cho từng instance với **Quick Check** và **Full Verification**.
- Kiểm tra Minecraft client, libraries, natives, assets, Java, mod loader, file modpack được quản lý, LAN Agent và metadata của instance.
- Lập repair plan trước khi sửa, hiển thị số vấn đề cùng dung lượng tải dự kiến và cho phép sửa mục đã chọn hoặc toàn bộ mục có thể tự động sửa.
- Tạo recovery point trước khi sửa thành phần thuộc instance và tự động rollback nếu một bước sửa thất bại; world, save và file không do launcher quản lý không bị thay thế.
- Hợp nhất tải file qua **Download Engine 2** với kết nối dùng chung, giới hạn đồng thời toàn cục/theo host và bandwidth limit dùng chung.
- Tải vào file `.part`, xác minh size/checksum rồi atomic replace; hỗ trợ HTTP Range và khôi phục phần tải hợp lệ sau khi launcher khởi động lại.
- Phân loại lỗi retry, tôn trọng `Retry-After`, hỗ trợ nguồn dự phòng và lưu download journal đã lọc dữ liệu nhạy cảm.
- Có **Pause / Resume** và **Cancel** riêng. Việc hủy an toàn giữ lại file `.part` hợp lệ để lần tải sau có thể tiếp tục.
- Hiển thị bản xem trước chính xác trước khi cập nhật modpack Modrinth: thêm, thay thế, xóa, giữ file người dùng, file không đổi và dung lượng tải dự kiến.
- Tạo backup đầy đủ trước khi áp dụng update modpack, phát hiện xung đột trước khi xác nhận và vẫn xác minh lại file khi thực thi.
- Xuất diagnostics ZIP có giới hạn dung lượng, lọc token/thông tin nhạy cảm và không chứa account database, world hoặc nội dung mod JAR.
- Sửa chuỗi tác vụ preview → update bị báo nhầm đang có tác vụ khác, đồng thời thêm fallback an toàn khi Windows chặn đổi tên thư mục staging như `.fabric` lúc restore backup.

### Thử nghiệm trong `v0.10.0-beta.1`

- Cài mod **Fabric trực tiếp từ CurseForge** trong catalog Mods hiện có; vẫn hỗ trợ Forge bằng cùng một luồng.
- Cài **modpack Fabric từ CurseForge**: chọn Fabric/Forge trong trình duyệt, đọc loader và phiên bản chính xác từ `manifest.json`, rồi tạo instance tương ứng.
- Giữ mọi file trong release channel đã bật, ưu tiên loader cùng nhãn Minecraft chính xác/gần nhất rồi cài dependency bắt buộc; nhãn phiên bản không còn chặn cài đặt.
- Dùng gateway công khai cho metadata; CurseForge API key vẫn chỉ nằm phía server và file mod được tải trực tiếp bằng Download Engine của launcher.
- Kiểm tra metadata thật trong JAR trước khi thay đổi instance. Nhãn Minecraft và Fabric/Forge của CurseForge chỉ được dùng để ưu tiên kết quả.
- Chuẩn bị toàn bộ file tự động trước khi cài và rollback mod cùng registry nếu một bước ghi thất bại.
- Giữ fallback tải thủ công có xác minh size/SHA-1 khi tác giả tắt phân phối bên thứ ba.

### Nền tảng hiện có

- Tạo và chạy instance **Vanilla, Fabric hoặc Forge**; cài đặt, thay đổi và repair Fabric Loader/Minecraft Forge.
- Tài khoản Offline và Microsoft OAuth PKCE, hỗ trợ nhiều tài khoản Microsoft và bảo vệ refresh token bằng Windows DPAPI.
- Tìm, cài và cập nhật mod từ **Modrinth**; nhãn Minecraft chỉ để ưu tiên, còn manifest `.mrpack` quyết định phiên bản của modpack.
- Tìm và cài mod/modpack **CurseForge** qua gateway công khai, có cache, failover và luồng tải thủ công được xác minh khi tác giả hạn chế phân phối.
- Backup/restore `.mcwbackup`, import/export `.mcwpack`, runtime lock, theo dõi tiến trình Minecraft, game log và crash report.
- **MCW LAN Agent** cùng LAN hosting profiles cho chế độ Microsoft-only hoặc bạn bè Microsoft + Offline trên các cấu hình được hỗ trợ.
- Giao diện PySide6 responsive, progress thống nhất, ngôn ngữ Việt/Anh và theme PNG ngoài EXE.

### Tải và chạy

Bản đóng gói dành cho Windows được phát hành tại trang **Releases**:

- [Mở trang phát hành](https://github.com/mahiru7229/mcw-launcher/releases)
- `v0.9.0` là bản Stable hiện tại dành cho người dùng thông thường.
- `v0.10.0-beta.1` chỉ dành cho người chủ động tham gia tester program.
- Stable là kênh mặc định. Để nhận bản thử nghiệm, người dùng phải chủ động bật:

```text
Launcher Settings
└── Launcher updates
    └── Tham gia chương trình tester và nhận bản cập nhật thử nghiệm
```

Tắt tùy chọn này sẽ đưa launcher trở lại kênh Stable. Bản thử nghiệm có thể chứa lỗi hoặc vấn đề tương thích; hãy backup instance và world quan trọng trước khi tham gia.

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
python -m tools.build_release_zip --exe ".\dist\MCW Launcher.exe" --version "0.10.0-beta.1"
```

Kết quả updater package:

```text
MCW-Launcher-v0.10.0-beta.1-windows-x64.zip
MCW-Launcher-v0.10.0-beta.1-windows-x64.zip.sha256
```

Xem thêm [`docs/UPDATE_PACKAGES.md`](docs/UPDATE_PACKAGES.md).

---

## English

### What is MCW Launcher?

MCW Launcher is an open-source Minecraft launcher centered around **isolated instances**, visible download progress, safe repair workflows, and a GUI that remains separate from launcher logic.

Each instance owns its game directory, Minecraft version, mod loader, mods, saves, Java configuration, memory allocation, and runtime state. The project currently targets 64-bit Windows 10 and Windows 11.

### `v0.9.0` highlights

- Add a per-instance **Repair Center** with **Quick Check** and **Full Verification**.
- Check the Minecraft client, libraries, natives, assets, Java, mod loader, managed modpack files, LAN Agent, and instance metadata.
- Build a repair plan before applying changes, including issue totals and estimated download size, with selective and repair-all actions.
- Create a recovery point before instance-scoped repairs and roll back automatically when a repair step fails; worlds, saves, and unmanaged files are not replaced.
- Route file transfers through **Download Engine 2** with shared connections, global/per-host concurrency, and a shared bandwidth limit.
- Download into `.part` files, verify size/checksums, then replace atomically; support HTTP Range and recover valid partial data after a launcher restart.
- Classify retryable failures, respect `Retry-After`, support verified fallback sources, and keep a sanitized persistent download journal.
- Provide separate **Pause / Resume** and **Cancel** controls. Safe cancellation keeps valid `.part` data available for a later resume.
- Preview exact Modrinth modpack update changes before confirmation: add, replace, remove, preserve, unchanged, and estimated download totals.
- Create a full backup before applying a modpack update, detect conflicts during preview, and revalidate files during the real operation.
- Export bounded, privacy-filtered diagnostic ZIP bundles without account databases, worlds, or mod JAR contents.
- Fix preview → update task chains being rejected as already busy, and add a safe fallback when Windows blocks renaming staged folders such as `.fabric` during backup restore.

### Experimental in `v0.10.0-beta.1`

- Install **Fabric mods directly from CurseForge** in the existing Mods catalog while retaining the same Forge workflow.
- Install **Fabric CurseForge modpacks** by selecting Fabric/Forge in the browser, validating the exact loader and version from `manifest.json`, and creating the matching instance.
- Keep every file in the enabled release channels, rank selected-loader and exact/nearby Minecraft labels first, then resolve required dependencies; version labels no longer block installation.
- Fetch metadata through the public gateway, keep the CurseForge API key server-side, and download mod files directly with the launcher's Download Engine.
- Validate real JAR metadata before changing an instance. CurseForge Minecraft and Fabric/Forge labels are ranking hints rather than the final authority.
- Prepare every automatic file before installation and roll back both mods and registry data if an apply step fails.
- Preserve the size/SHA-1-verified manual fallback when an author disables third-party distribution.

### Existing foundation

- Create and launch **Vanilla, Fabric, and Forge** instances; install, change, and repair Fabric Loader/Minecraft Forge.
- Use Offline or Microsoft OAuth PKCE accounts, including multiple Microsoft accounts and Windows DPAPI protection for refresh tokens.
- Search, install, and update **Modrinth** mods; Minecraft labels only affect ranking, while each `.mrpack` manifest determines its modpack version.
- Search and install **CurseForge** mods/modpacks through the public gateway, with caching, failover, and verified manual downloads for restricted files.
- Backup/restore `.mcwbackup`, import/export `.mcwpack`, enforce runtime locks, and track the Minecraft process, game logs, and crash reports.
- Use **MCW LAN Agent** and LAN hosting profiles for Microsoft-only or Microsoft + Offline friends on supported configurations.
- Use a responsive PySide6 interface with unified progress, English/Vietnamese language packs, and external PNG themes.

### Download and run

Packaged Windows builds are published on the **Releases** page:

- [Open releases](https://github.com/mahiru7229/mcw-launcher/releases)
- `v0.9.0` is the current Stable release for regular users.
- `v0.10.0-beta.1` is available only to users who explicitly join the tester program.
- Stable is the default channel. Experimental builds require explicitly enabling:

```text
Launcher Settings
└── Launcher updates
    └── Join tester program and receive experimental updates
```

Disabling this option returns the launcher to Stable. Experimental builds may contain bugs or compatibility issues; back up important instances and worlds before joining.

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
python -m tools.build_release_zip --exe ".\dist\MCW Launcher.exe" --version "0.10.0-beta.1"
```

Expected updater assets:

```text
MCW-Launcher-v0.10.0-beta.1-windows-x64.zip
MCW-Launcher-v0.10.0-beta.1-windows-x64.zip.sha256
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

### Downloads and recovery

- Shared HTTP client with connection pooling and configurable simultaneous downloads.
- Global/per-host concurrency limits plus one bandwidth limit shared across active transfers.
- Verified `.part` files, HTTP Range resume, atomic replacement, and recovery after restart.
- Bounded retries for temporary failures, `Retry-After` support, and verified fallback URLs.
- Persistent sanitized journal with best-effort startup reconciliation.

### Mods and modpacks

- Fabric and Forge mod metadata parsing.
- Enable/disable, drag-and-drop, dependency analysis, duplicate-ID detection, and loader mismatch checks.
- Modrinth dependency installation, advisory Minecraft-version ranking, update checks, update locks, retry/resume, and fallback URLs.
- CurseForge Gateway search, advisory loader/Minecraft ranking, dependency installation, automatic/manual distribution handling, local JSON caching, refresh cooldown, and stale fallback.
- Managed modpack registry with update preview, repair, conflict preservation, backup, rollback, and verification cache.

### Repair, backup, and diagnostics

- Quick Check and Full Verification with persistent verification cache.
- Component health reports, repair plans, estimated download size, and selective repair.
- Recovery points for instance-scoped repairs with automatic rollback on failure.
- Transactional `.mcwbackup` restore, including a Windows-safe staged-folder fallback.
- Bounded diagnostic ZIP bundles with safe paths, integrity validation, hashes, and privacy filtering.

### Accounts and privacy

- Offline and Microsoft accounts.
- Microsoft PKCE/Xbox/XSTS/Minecraft Services flow.
- Windows DPAPI protection for persisted refresh tokens.
- Access tokens kept in memory only.
- Credential and bearer-token redaction in logs and diagnostics.

### Interface

- PySide6 GUI with full and compact display profiles.
- Unified progress for launcher updates, Minecraft files, Java, mods, modpacks, imports, exports, and repairs.
- Separate Pause/Resume and Cancel controls for supported active operations.
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
│   │   ├── diagnostics/
│   │   ├── instance/
│   │   ├── java/
│   │   ├── lan/
│   │   ├── minecraft/
│   │   ├── mod/
│   │   ├── modloader/
│   │   ├── modrinth/
│   │   ├── curseforge/
│   │   ├── network/
│   │   ├── progress/
│   │   ├── repair/
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
| [`docs/RELEASE-v0.10.0-beta.1.md`](docs/RELEASE-v0.10.0-beta.1.md) | v0.10.0 Beta 1 CurseForge/Fabric test notes |
| [`docs/RELEASE-v0.9.0.md`](docs/RELEASE-v0.9.0.md) | Complete v0.9.0 Stable release notes |
| [`docs/RELEASE-v0.8.1.md`](docs/RELEASE-v0.8.1.md) | v0.8.1 CurseForge and managed-modpack hotfix notes |
| [`docs/RELEASE-v0.8.0.md`](docs/RELEASE-v0.8.0.md) | Complete v0.8.0 Stable release notes |
| [`docs/RELEASE-v0.7.2.md`](docs/RELEASE-v0.7.2.md) | Complete v0.7.2 Stable maintenance release notes |
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

| Component | Status in v0.10.0-beta.1 |
|---|---|
| Vanilla instances | Available |
| Fabric Loader and mods | Available |
| Forge Loader and mods | Available |
| Modrinth mods and `.mrpack` modpacks | Available — preview, update, repair, backup and rollback supported |
| Download resume and recovery | Available — verified `.part` files and persistent journal |
| Repair Center | Available — Quick Check, Full Verification and recovery points |
| Diagnostic ZIP export | Available — bounded and privacy-filtered |
| Microsoft accounts | Available |
| Offline accounts | Available |
| English / Vietnamese | Available |
| PNG themes | Available |
| NeoForge / Quilt | Not supported |
| CurseForge Gateway mods | Beta — Fabric/Forge install, required dependencies, transactional apply, public gateway, cache and manual fallback |
| CurseForge modpacks | Experimental — Fabric/Forge manifest-driven install with universal dependency support |

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
