# MCW Launcher

<p align="center">
  <strong>Minecraft launcher theo hướng instance-first, viết bằng Python và PySide6.</strong><br>
  Quản lý Minecraft, mod loader, mod, modpack và nội dung của từng instance trong một giao diện thống nhất.
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/releases">
    <img src="https://img.shields.io/badge/Stable-v1.0.2-brightgreen" alt="Stable version">
  </a>
  <a href="https://github.com/mahiru7229/mcw-launcher/actions">
    <img src="https://img.shields.io/badge/Tests-passing-success" alt="Tests">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  </a>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D4" alt="Windows">
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52" alt="PySide6">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB" alt="Python 3.12+">
</p>

<p align="center">
  <a href="#giới-thiệu">Giới thiệu</a> ·
  <a href="#tính-năng-nổi-bật">Tính năng</a> ·
  <a href="#tải-và-cài-đặt">Tải xuống</a> ·
  <a href="#chạy-từ-source">Chạy source</a> ·
  <a href="#mcw-core">MCW Core</a>
</p>

---

## Giới thiệu

**MCW Launcher** là một Minecraft launcher mã nguồn mở dành cho Windows, được xây dựng xoay quanh mô hình **instance độc lập**.

Mỗi instance có riêng:

- Phiên bản Minecraft và mod loader.
- Mods, resource packs, shader packs và saves.
- Java runtime, RAM, JVM arguments và cấu hình cửa sổ.
- Trạng thái runtime, lịch sử launch, backup và dữ liệu repair.
- Metadata nguồn cho mod/modpack từ Modrinth, CurseForge hoặc FTB.

Mục tiêu của dự án là tạo ra một launcher dễ kiểm soát, minh bạch khi tải file, an toàn khi sửa chữa và đủ linh hoạt cho cả người chơi Vanilla lẫn người dùng modpack.
---
Hỗ trợ nâng cấp trực tiếp: MCW Launcher v1.0.2 hỗ trợ nâng cấp trực tiếp từ v0.5.1 và tất cả các phiên bản phát hành sau đó.

---

## Có gì mới trong v1.0.2

**v1.0.2** là hotfix dành cho cơ chế khởi động lại launcher sau khi đổi ngôn ngữ. Bản EXE one-file giờ tạo một tiến trình PyInstaller độc lập thay vì tái sử dụng thư mục giải nén tạm của tiến trình cũ. Điều này ngăn lỗi khởi động lại thiếu module PySide6 sau khi launcher hiện thông báo đổi ngôn ngữ.

- Khởi động lại đúng chính file `MCW Launcher.exe` ở bản đóng gói.
- Thiết lập `PYINSTALLER_RESET_ENVIRONMENT=1` chỉ cho tiến trình thay thế.
- Không làm thay đổi môi trường của launcher đang chạy.
- Chạy source vẫn dùng Python hiện tại cùng `launcher.py`.
- Có regression test cho frozen mode, command, environment và lỗi spawn.
- Không thay đổi dữ liệu instance, tài khoản, theme, language pack hoặc provider.

Xem chi tiết tại [`docs/RELEASE-v1.0.2.md`](docs/RELEASE-v1.0.2.md).

## Có gì mới trong v1.0.1

**v1.0.1** là bản bảo trì đầu tiên sau mốc stable 1.0.0, tập trung vào độ chính xác của nội dung, trải nghiệm thiết lập ban đầu và tính nhất quán của giao diện:

- Sửa đường dẫn resource pack và shader pack về đúng thư mục gốc của instance, kèm migration an toàn cho dữ liệu được tạo bởi v1.0.0.
- Cho phép cài thêm resource pack/shader pack khi game đang chạy, nhưng vẫn chặn thao tác thay thế, vô hiệu hóa hoặc xóa nội dung đang có.
- Sắp xếp phiên bản FTB từ mới nhất đến cũ nhất.
- Mở rộng First Run Setup với quét Java, chọn runtime mặc định, gợi ý RAM, download concurrency và tóm tắt cấu hình.
- Thêm chính sách xác nhận lỗi tương thích theo từng instance: Kế thừa, Hỏi, Chặn hoặc Cho phép.
- Khôi phục icon modpack từ archive hoặc provider theo cơ chế best-effort.
- Thêm màu chữ tùy chỉnh cho Launcher Settings và theme contract, có preview, reset và kiểm tra độ tương phản.
- Làm gọn card GPU rời, hoàn thiện bản dịch, dùng file picker native trên Windows và gia cố repaint khi cuộn.
- Sửa live language reload sau First Run Setup, thêm nút chạy lại wizard và dịch toàn bộ progress động theo ngôn ngữ launcher.

Xem chi tiết tại [`docs/RELEASE-v1.0.1.md`](docs/RELEASE-v1.0.1.md).

## Tính năng nổi bật

### Quản lý instance

- Tạo, đổi tên, clone, xóa, import và export instance.
- Hỗ trợ **Vanilla, Fabric, Quilt, Forge và NeoForge**.
- Thư viện instance dạng icon với tìm kiếm, trạng thái runtime và thao tác nhanh.
- Mỗi instance có Java, RAM, độ phân giải, fullscreen, JVM arguments và game arguments riêng.
- Run lock ngăn khởi chạy trùng cùng một instance.

### Tài khoản và khởi chạy

- Tài khoản Offline và Microsoft OAuth PKCE.
- Hỗ trợ nhiều tài khoản Microsoft.
- Bảo vệ dữ liệu nhạy cảm bằng Windows DPAPI.
- Theo dõi process Minecraft, exit code, crash state và game log.
- Pause, resume và cancel trong các bước tải được hỗ trợ.

### Mod và modpack

- Duyệt và cài mod/modpack từ **Modrinth** và **CurseForge**.
- Duyệt và cài modpack từ **FTB**.
- Trang chi tiết project có icon, mô tả, metadata, gallery, phiên bản và link web.
- Chọn Minecraft version, loader và release channel trước khi cài.
- Deferred download: cài modpack chỉ lưu manifest; mod được tải ở lần Launch đầu tiên.
- Giữ provenance của từng mod: provider, project ID, version/file ID, hash và modpack sở hữu.
- Manual-download fallback cho file không thể tải tự động.

### Import và export modpack

MCW Launcher hỗ trợ hai hướng import:

- **Duyệt trực tuyến** từ provider.
- **Import package native** như Modrinth `.mrpack`, CurseForge `.zip`, Provider Profile hoặc Portable MCWPack.

Hai chế độ export chính:

- **Provider Profile** — giữ nguyên package/reference của provider và chỉ thêm instance settings của MCW.
- **Portable MCWPack** — manifest portable với nguồn tải, hash, embedded file được phép và manual-download fallback.

Full/offline export vẫn có thể dùng cho backup hoặc chia sẻ riêng tư, kèm cảnh báo về giấy phép và chính sách phân phối.

### Resource pack và shader pack

- Duyệt từ Modrinth hoặc CurseForge.
- Cài, import file local, bật/tắt, gỡ và mở thư mục.
- Kiểm tra ZIP, `pack.mcmeta`, cấu trúc shader và archive security.
- Lưu metadata provider để phục vụ update và export sau này.

### Installed Content Library

- Xem modpack, mod, resource pack và shader pack trong một thư viện chung.
- Lọc theo loại, provider và trạng thái.
- Hiển thị `Ready`, `Disabled`, `Pending`, `Missing` hoặc `Broken`.
- Hỗ trợ thao tác hàng loạt, pin version và ignore update.
- Bảo vệ mod được quản lý bởi modpack khỏi việc xóa nhầm.

### Repair, backup và diagnostics

- Fast scan và full repair cho instance.
- Backup/restore `.mcwbackup`.
- Diagnostic bundle có redaction dữ liệu nhạy cảm.
- Cleanup file `.part`, stale session và trạng thái runtime cũ.
- Xác minh hash, size và rollback khi thao tác thất bại.

### Giao diện và trải nghiệm

- GUI PySide6 responsive, hỗ trợ DPI Windows.
- First Run Setup cho ngôn ngữ, cập nhật, Java, RAM và phần cứng.
- Tùy chọn ưu tiên dedicated GPU khi máy có GPU rời.
- Hỗ trợ tiếng Việt và English.
- Theme ngoài EXE, animation, custom font, accent color và text color.
- Navigation Back/Forward riêng, sidebar có thể thu gọn.

### LAN và multiplayer offline

- MCW LAN Agent cho các cấu hình được hỗ trợ.
- Profile Microsoft-only hoặc Microsoft + Offline friends.
- Tích hợp workflow e4mc/LAN theo từng instance.

---

## Tải và cài đặt

Tải bản Windows mới nhất tại:

**[GitHub Releases](https://github.com/mahiru7229/mcw-launcher/releases)**

Thông thường release sẽ có:

```text
MCW Launcher.exe
MCW-Launcher-v1.0.1-windows-x64.zip
MCW-Launcher-v1.0.1-windows-x64.zip.sha256
```

### Yêu cầu hệ thống

- Windows 10 hoặc Windows 11 64-bit.
- Kết nối Internet cho lần tải Minecraft, Java, loader, mod hoặc modpack đầu tiên.
- Dung lượng trống phù hợp với số instance, assets, mods và backups.

Java tương thích có thể được launcher tự phát hiện hoặc cài đặt.

---

## Bắt đầu sử dụng

1. Mở `MCW Launcher.exe`.
2. Hoàn thành **First Run Setup**.
3. Thêm tài khoản Offline hoặc Microsoft.
4. Nhấn **Thêm instance**.
5. Chọn tạo instance thường hoặc cài/import modpack.
6. Kiểm tra Java, RAM và setting của instance.
7. Nhấn **Launch**.

Ở lần chạy đầu tiên, launcher sẽ tải những file Minecraft hoặc mod còn thiếu rồi mới khởi chạy game.

---

## Chạy từ source

Python `3.12` trở lên được khuyến nghị.

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

---

## Kiểm thử

Chạy toàn bộ test suite:

```powershell
python -m pytest -q
```

Chạy release preflight:

```powershell
python -m tools.release_preflight
```

Một bản release chỉ nên được đóng gói khi:

- Không có test thất bại.
- Không có lỗi collection/runtime.
- Hai language pack có đủ key.
- Không còn merge marker.
- Metadata version và update channel chính xác.

---

## Build bản Windows

Chạy quy trình release tự động:

```powershell
.\build_release.ps1
```

Hoặc build EXE thủ công:

```powershell
python -m PyInstaller --clean --noconfirm mcw_launcher.spec
```

EXE được tạo tại:

```text
dist/MCW Launcher.exe
```

---

## MCW Core

Từ phiên bản 1.0.0, launcher có một core headless riêng dưới package:

```python
import mcw_core
```

MCW Core cung cấp API cho:

- Instance lifecycle.
- Launch lifecycle.
- Java management.
- Mod loader và modpack.
- Modrinth, CurseForge và FTB.
- Repair, backup và diagnostics.
- Progress, pause, resume và cancel.
- Portable package import/export.

Cài wheel:

```powershell
python -m pip install mcw-core==1.0.0
```

Tài liệu core nằm trong repository/package riêng:

- `README.md`
- `docs/QUICKSTART.md`
- `docs/API_OVERVIEW.md`
- `docs/USAGE.md`
- `docs/MIGRATION.md`
- `docs/CORE_ARCHITECTURE.md`

---

## Kiến trúc

MCW Launcher giữ GUI ở phía ngoài và chỉ giao tiếp qua public core API:

```text
PySide6 GUI
    ↓
mcw_core / mcw_core.api
    ↓
Domain services
    ↓
Filesystem · Network · Providers · Minecraft Runtime
```

GUI không nên trực tiếp:

- Truy cập database nội bộ.
- Tải file riêng ngoài Download Engine.
- Gọi private implementation của core.
- Xử lý authentication hoặc manifest provider một cách độc lập.

---

## Ngôn ngữ và theme

Language packs mặc định:

```text
lang/en-US.json
lang/vi-VN.json
```

Theme hỗ trợ:

- Palette và accent color.
- Text color tùy chỉnh.
- PNG assets và spritesheet animation.
- Custom font `.ttf` / `.otf`.
- Full, Reduced hoặc Off motion mode.
- Live reload và theme authoring tools.

Tài liệu theme:

- `docs/THEME_CREATION_GUIDE.md`
- `docs/THEME_ASSET_GUIDE.md`
- `docs/THEME_ANIMATION_GUIDE.md`
- `docs/THEME_MOTION_GUIDE.md`

---

## Cảnh báo phân phối modpack

> Người dùng có trách nhiệm bảo đảm việc chia sẻ, xuất bản hoặc lưu trữ modpack tuân thủ giấy phép của từng mod, quyền của tác giả và chính sách của provider. MCW Launcher không xác nhận hoặc khuyến khích việc phân phối lại trái phép.

Khi export công khai, nên ưu tiên:

- Provider Profile.
- Manifest/reference chính thức.
- File có license cho phép redistribution rõ ràng.
- Manual-download flow nếu quyền phân phối không rõ.

---

## Cấu hình CurseForge

MCW Launcher không còn đóng gói sẵn đường dẫn CurseForge gateway mặc định. Để sử dụng các tính năng CurseForge, hãy cấu hình gateway HTTPS riêng trong **Cài đặt launcher** hoặc qua biến môi trường được hỗ trợ. API key vẫn phải được giữ ở phía gateway và không được đưa vào launcher, source hoặc diagnostic bundle.

---

## Bảo mật

Vui lòng không đưa vào issue công khai:

- Microsoft access/refresh token.
- CurseForge API key.
- Cookie hoặc credential.
- Diagnostic bundle chưa kiểm tra.
- Đường dẫn hoặc dữ liệu cá nhân không cần thiết.

Khi báo lỗi, hãy dùng diagnostic bundle đã được launcher redaction và kiểm tra lại trước khi upload.

---

## Đóng góp

Issue và pull request đều được chào đón.

Trước khi gửi PR:

```powershell
python -m pytest -q
python -m tools.release_preflight
```

Nên giữ:

- GUI phụ thuộc public `mcw_core` API.
- Progress thống nhất cho mọi tác vụ dài.
- en-US và vi-VN đầy đủ key.
- Test hồi quy cho bug được sửa.
- Không commit token, cache, instance cá nhân hoặc build output.

---

## Giấy phép

MCW Launcher được phát hành theo giấy phép **MIT**.

Minecraft, Microsoft, Mojang, Modrinth, CurseForge, FTB và các thương hiệu liên quan thuộc về chủ sở hữu tương ứng. MCW Launcher là dự án độc lập và không phải sản phẩm chính thức của các bên này.

---

## CurseForge configuration

MCW Launcher no longer bundles a default CurseForge gateway URL. CurseForge features require a user- or deployment-provided HTTPS gateway configured through Launcher Settings or the supported environment variables. API credentials must remain server-side and must not be embedded in the launcher.

---

## English summary

MCW Launcher is an open-source, Windows-focused, instance-first Minecraft launcher built with Python and PySide6. It supports Vanilla, Fabric, Quilt, Forge and NeoForge instances; Offline and Microsoft accounts; Modrinth, CurseForge and FTB modpacks; resource/shader packs; repair, backup, diagnostics, provider-native import, portable export, theming and a public headless `mcw_core` package.

Download the latest build from **[GitHub Releases](https://github.com/mahiru7229/mcw-launcher/releases)**.

### Language and theme authoring

Primary navigation and new UI surfaces use semantic translation keys. Changing the launcher language now prompts for a clean restart, preventing partially translated pages and dialogs. The machine-readable contract for future translation/theme tools is documented in `docs/LANGUAGE_THEME_EDITOR_CONTRACT.md`.


## Pytest test-module isolation

The launcher test suite uses pytest importlib mode. This prevents `import file mismatch`
errors when launcher and standalone core tests contain the same filename in different
directories. Core distribution tests also use a unique basename in the corrected 1.0.1
source package.
