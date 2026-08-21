# MCW Launcher

<p align="center">
  <img src="assets/icons/mcw_launcher.png" alt="MCW Launcher" width="112">
</p>

<p align="center">
  <strong>Minecraft launcher mã nguồn mở theo hướng instance-first.</strong><br>
  Quản lý game, mod loader, nội dung và runtime Java của từng instance trong một giao diện PySide6 thống nhất.
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml"><img src="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/version-v1.5.0--alpha.1-orange" alt="v1.5.0-alpha.1">
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB" alt="Python 3.12+">
</p>

> [!WARNING]
> `v1.5.0-alpha.1` là bản phát triển để tái cấu trúc code và đặt nền móng cho Linux. Hãy sao lưu thư mục instance trước khi thử nghiệm. Bản Windows vẫn là nền tảng chính; Linux chưa được xem là hoàn thiện ở Alpha 1.

## Tổng quan

MCW Launcher tách mỗi cấu hình chơi thành một **instance** độc lập. Mỗi instance có phiên bản Minecraft, mod loader, mods, resource packs, shader packs, saves, Java, RAM và JVM arguments riêng. Thiết kế này giúp việc thử modpack, sửa lỗi hoặc sao lưu không ảnh hưởng đến các instance khác.

Các nhóm tính năng chính:

- Quản lý nhiều instance Vanilla, Fabric, Quilt, Forge và NeoForge.
- Tìm và cài nội dung từ Modrinth; tích hợp CurseForge qua gateway do người dùng cấu hình.
- Nhập modpack từ Modrinth, CurseForge, FTB và ATLauncher.
- Tự động chọn/provision Java phù hợp, kiểm tra checksum và hỗ trợ repair.
- Tài khoản Microsoft và chế độ offline; access token ngắn hạn chỉ giữ trong bộ nhớ.
- Backup, diagnostics, theme/language pack, cập nhật launcher và chơi LAN.
- API `mcw_core` nằm cùng repository để GUI dùng qua một biên public ổn định.

## Trạng thái nền tảng

| Nền tảng | Trạng thái Alpha 1 | Ghi chú |
| --- | --- | --- |
| Windows 10/11 x64 | Đang hỗ trợ | Luồng chính và bản đóng gói PyInstaller hiện tại. |
| Linux x64 | Đang thử nghiệm | Đã có nhận diện rule/native và CI; Java provisioning, packaging và một số tích hợp hệ thống còn cần hoàn thiện. |
| Linux ARM64 | Nền tảng ban đầu | Nhận diện đúng kiến trúc; chưa có cam kết tương thích runtime/game. |
| macOS | Chưa hỗ trợ | Chưa nằm trong phạm vi v1.5. |

## Yêu cầu

- Python 3.12 trở lên.
- Git và kết nối Internet để tải metadata/game content.
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

Một số bản phân phối Linux cần cài thêm thư viện hệ thống cho Qt/xcb. Tên package khác nhau theo distro; hãy xem lỗi plugin Qt của môi trường đang dùng trước khi cài thêm.

## Phát triển

Chạy test:

```bash
python -m pytest test -v
```

Chạy kiểm tra trước release:

```bash
python -m tools.release_preflight
```

Build Windows hiện tại:

```powershell
.\build_release.ps1
```

Build Linux chưa phải deliverable của Alpha 1. Không nên dùng script Windows hoặc đổi đuôi artifact để giả lập một bản Linux release.

## Kiến trúc repository

```text
mcw-launcher/
├── launcher.py          # entry point và startup lifecycle
├── mcw_core/            # public facade/API dùng bởi GUI và consumer headless
├── src/core/            # implementation nghiệp vụ
├── src/gui/             # giao diện PySide6
├── src/models/          # model/domain objects
├── test/                # test suite
├── assets/ lang/ themes/
├── runtime/             # MCW LAN Agent
├── tools/               # preflight, build và validation tools
└── docs/                # tài liệu kỹ thuật
```

GUI chỉ nên gọi nghiệp vụ qua `mcw_core.api` hoặc public facade, không import trực tiếp `src.core`. Metadata tải về phải được kiểm tra identifier, đường dẫn và checksum trước khi ghi vào workspace. Xem [kiến trúc chi tiết](docs/ARCHITECTURE.md).

## Tài liệu

- [Quickstart](docs/QUICKSTART.md)
- [Kiến trúc](docs/ARCHITECTURE.md)
- [Instance system](docs/INSTANCE_SYSTEM.md)
- [MCW Core API](docs/MCW_CORE_LIBRARY.md)
- [Language packs](docs/LANGUAGE_PACKS.md)
- [Theme authoring](docs/THEME_CREATION_GUIDE.md)
- [Release notes v1.5.0-alpha.1](docs/releases/v1.5.0-alpha.1.md)
- [Changelog](CHANGELOG.md)

## Đóng góp và bảo mật

Đọc [CONTRIBUTING.md](CONTRIBUTING.md) trước khi mở pull request. Không commit access token, API key, account database, log hoặc diagnostics bundle có dữ liệu cá nhân. Nếu phát hiện lỗ hổng, làm theo [SECURITY.md](SECURITY.md) thay vì đăng chi tiết khai thác trong public issue.

## License

MCW Launcher được phát hành theo [MIT License](LICENSE). Minecraft là sản phẩm của Mojang Studios; dự án này không liên kết hoặc được Mojang/Microsoft chứng thực.
