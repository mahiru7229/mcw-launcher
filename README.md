# MCW Launcher

<p align="center">
  <img src="assets/icons/mcw_launcher.png" alt="MCW Launcher" width="112">
</p>

<p align="center">
  <strong>Minecraft launcher mã nguồn mở theo hướng instance-first.</strong><br>
  Quản lý game, mod loader, nội dung và runtime Java của từng instance với kiến trúc tách biệt 100% giữa MCW Core và giao diện GUI.
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml"><img src="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/version-v1.8.0-blue" alt="v1.8.0">
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB" alt="Python 3.12+">
</p>

> [!NOTE]
> `v1.8.0` là bản phát hành cột mốc **tách biệt 100% giữa MCW Core Engine (`mcw_core`) và tầng Giao diện (`src/gui`)**: bổ sung giao thức chuẩn **JSON-RPC 2.0** đa kênh (`mcw_core.rpc` — hỗ trợ Direct, Stdio Sidecar `--stdio` và Local HTTP + SSE `--http`), mở rộng `mcw_core/api/` & `mcw_core/api/models/` để GUI hoàn toàn không phụ thuộc vào `src.core` hay `src.models`, đồng thời tích hợp sẵn toàn bộ các cải tiến từ Hotfix `v1.7.1.1` (Hardware GPU Caching & hiển thị phiên bản Hotfix trực quan).

> [!IMPORTANT]
> **If you are looking for related components / Các dự án liên quan:**
> 1. **Core**: [MCW Launcher Core · Download & Docs](https://mahiru7229.github.io/mcw_core/index.html) — Thư viện core headless độc lập (`mcw_core-1.8.0-py3-none-any.whl`), máy chủ JSON-RPC 2.0 và tài liệu API.
> 2. **CurseForge Gateway**: [mahiru7229/mcw-curseforge-gateway](https://github.com/mahiru7229/mcw-curseforge-gateway) — Mã nguồn gateway để người dùng tự build/deploy riêng. Launcher không tích hợp sẵn endpoint gateway công khai do tác giả không có kinh phí duy trì server gánh lượng lớn request cho cộng đồng (link gateway cá nhân chỉ tạo dùng nội bộ nhóm nhỏ và dự án không có dự định mở API công khai cho ứng dụng).

## Tổng quan

MCW Launcher tách mỗi cấu hình chơi thành một **instance** độc lập. Mỗi instance có phiên bản Minecraft, mod loader, mods, resource packs, shader packs, saves, Java, RAM và JVM arguments riêng. Thiết kế này giúp việc thử modpack, sửa lỗi hoặc sao lưu không ảnh hưởng đến các instance khác.

Các nhóm tính năng chính:

- **Tách biệt 100% Core & GUI (`mcw_core.rpc` & `mcw_core.api`)**: Giao tiếp chuẩn hóa qua JSON-RPC 2.0 (In-process Direct, Stdio Sidecar Process `--stdio`, hoặc Local HTTP + SSE `--http` trên `127.0.0.1`), sẵn sàng cho cả GUI PySide6 hiện tại lẫn GUI đa ngôn ngữ (Tauri v2 / TypeScript + React / C#).
- Quản lý nhiều instance Vanilla, Fabric, Quilt, Forge và NeoForge.
- Tìm và cài nội dung từ Modrinth; tích hợp CurseForge qua gateway do người dùng cấu hình.
- Nhập modpack từ Modrinth, CurseForge, FTB và ATLauncher.
- Tự động chọn/provision Java phù hợp, kiểm tra checksum và hỗ trợ repair.
- Tài khoản Microsoft và chế độ offline; access token ngắn hạn chỉ giữ trong bộ nhớ.
- Backup, diagnostics, theme/language pack, cập nhật launcher, hệ thống Hotfix CDN tự động và chơi LAN.

## Trạng thái nền tảng

| Nền tảng | Trạng thái v1.8.0 | Ghi chú |
| --- | --- | --- |
| Windows 10/11 x64 | Đang hỗ trợ | Phân phối dạng tệp thực thi duy nhất (`MCW Launcher.exe`). |
| Linux x64 | Đang hỗ trợ | Phân phối dạng tệp thực thi duy nhất (`mcw-launcher`). Automatic update và desktop opener đã được kiểm thử trên Lubuntu. |
| Linux ARM64 | Nền tảng ban đầu | Nhận diện và metadata Java đúng; chưa có cam kết launch game. |
| macOS | Chưa hỗ trợ | Chưa nằm trong phạm vi v1.8. |

## Yêu cầu

- Python 3.12 trở lên.
- Git và kết nối Internet cho lần tải metadata/game content đầu tiên; instance đã cache đầy đủ vẫn có thể launch offline.
- Windows 10/11 hoặc một bản phân phối Linux x64 để thử nghiệm.
- Java không bắt buộc cài sẵn cho mọi trường hợp; launcher có cơ chế quản lý runtime, nhưng luồng Linux vẫn đang được hoàn thiện.

## Chạy từ source

Clone repository và tạo virtual environment:

```bash
git clone https://github.com/mahiru7229/mcw-launcher.git
cd mcw-launcher
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,build]"
python launcher.py
```

Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,build]'
python launcher.py
```

Chạy riêng MCW Core ở chế độ JSON-RPC 2.0 Sidecar hoặc HTTP Server:

```bash
python -m mcw_core.rpc.cli --stdio
python -m mcw_core.rpc.cli --http --host 127.0.0.1 --port 45180
```

## Phát triển

Chạy test:

```bash
python -m pytest test -v
```

Chạy kiểm tra trước release:

```bash
python -m tools.release_preflight
```

Trên Lubuntu, chạy preflight riêng trước khi mở GUI:

```bash
python tools/linux_preflight.py
```

Build Windows hiện tại:

```powershell
.\build_release.ps1
```

GitHub Release Actions chỉ build ZIP native Windows/Linux sau khi test cả hai nền tảng đạt. MCW Launcher không cung cấp AppImage hoặc `.deb`; updater Linux hoạt động với ZIP `linux-x64` đặt trong thư mục người dùng có quyền ghi.

## Kiến trúc repository

```text
mcw-launcher/
├── launcher.py          # entry point và startup lifecycle
├── updater.py           # updater v2 entry point
├── mcw_core/            # public facade, mcw_core.api.*, mcw_core.api.models.* và mcw_core.rpc (JSON-RPC 2.0)
├── src/core/            # implementation nghiệp vụ nội bộ của Core
├── src/gui/             # giao diện PySide6 (giao tiếp 100% qua mcw_core, không import src.core/src.models)
├── src/models/          # model/domain objects nội bộ
├── test/                # test suite & AST boundary verification
├── assets/ lang/ themes/
├── runtime/             # MCW LAN Agent
├── tools/               # preflight, build và validation tools
└── docs/                # tài liệu kỹ thuật
```

GUI chỉ gọi nghiệp vụ qua `mcw_core.rpc`, `mcw_core.api.*`, `mcw_core.api.models.*` hoặc public facade, **tuyệt đối không import trực tiếp `src.core` hay `src.models`**. Quy tắc ranh giới này được kiểm tra tự động bằng AST trong `test/test_v18_gui_core_decoupling.py` và `tools/release_preflight.py`. Xem [kiến trúc chi tiết](docs/ARCHITECTURE.md).

## Tài liệu & Dự án liên quan

- [MCW Launcher Core · Download & Docs](https://mahiru7229.github.io/mcw_core/index.html)
- [MCW CurseForge Gateway](https://github.com/mahiru7229/mcw-curseforge-gateway)
- [Quickstart](docs/QUICKSTART.md)
- [Kiểm thử trên Lubuntu](docs/LINUX_TESTING.md)
- [Kiến trúc](docs/ARCHITECTURE.md)
- [Instance system](docs/INSTANCE_SYSTEM.md)
- [MCW Core API & JSON-RPC 2.0](docs/MCW_CORE_LIBRARY.md)
- [Hệ thống Hotfix CDN](docs/HOTFIX_SYSTEM.md)
- [Cứu hộ Update Bridge](docs/UPDATE_BRIDGE_RECOVERY.md)
- [Language packs](docs/LANGUAGE_PACKS.md)
- [Theme authoring](docs/THEME_CREATION_GUIDE.md)
- [Release notes v1.8.0](docs/releases/v1.8.0.md)
- [Release notes v1.7.1](docs/releases/v1.7.1.md)
- [Release notes Update Bridge v1.7.1](docs/releases/update-bridge-v1.7.1.md)
- [Release notes v1.7.0](docs/releases/v1.7.0.md)
- [Release notes v1.6.1](docs/releases/v1.6.1.md)
- [Release notes v1.6.0](docs/releases/v1.6.0.md)
- [Changelog](CHANGELOG.md)

## Đóng góp và bảo mật

Đọc [CONTRIBUTING.md](CONTRIBUTING.md) trước khi mở pull request. Không commit access token, API key, account database, log hoặc diagnostics bundle có dữ liệu cá nhân. Nếu phát hiện lỗ hổng, làm theo [SECURITY.md](SECURITY.md) thay vì đăng chi tiết khai thác trong public issue.

## License

MCW Launcher được phát hành theo [MIT License](LICENSE). Minecraft là sản phẩm của Mojang Studios; dự án này không liên kết hoặc được Mojang/Microsoft chứng thực.
