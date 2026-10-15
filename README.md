# MCW Launcher

<p align="center">
  <img src="assets/icons/mcw_launcher.png" alt="MCW Launcher" width="112">
</p>

<p align="center">
  <strong>Minecraft launcher mã nguồn mở theo kiến trúc instance-first hiện đại.</strong><br>
  Quản lý độc lập game, mod loader, modpack và Java runtime với kiến trúc tách biệt 100% giữa MCW Core Engine và GUI.
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml"><img src="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/version-v1.8.2--beta.1-blue" alt="v1.8.2-beta.1">
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB" alt="Python 3.12+">
</p>

> [!NOTE]
> **Phiên bản mới nhất (v1.8.2-beta.1)**:
> - **Mở rộng hỗ trợ MCW LAN Agent xuống Minecraft 1.14+**: Tự động nhận diện bytecode target Forge SRG (`func_71229_d`), Fabric Intermediary (`method_3864`/`method_3782`), và Mojang Official Mappings (`d`), khắc phục triệt để lỗi `"Invalid session"` khi người chơi kết nối qua IP/Port vào world host LAN chế độ offline.
> - **Tự động đồng bộ và nạp Hotfix khi khởi động**: Cơ chế pre-bootstrap auto-sync nhanh (fail-open 2.0s) nạp các bản vá nóng trước khi import module UI, tự động thu hồi module cũ trong RAM (`sys.modules`) và hiển thị Toast nhắc khởi động lại.
> - **Tài khoản Offline gán model Steve / Alex cục bộ**: Tự động xác định biến thể Steve (`classic`) hoặc Alex (`slim`) theo thuật toán băm UUID chuẩn của Minecraft Java (`DefaultPlayerSkin`), hoàn toàn không truy vấn skin ngoài Internet.
> - **Múi giờ hệ thống cho thời gian lần cuối chơi**: Chuyển đổi timestamp UTC sang múi giờ địa phương (như UTC+7) giúp hiển thị chính xác ngày giờ người dùng chơi game.
> - **Kiến trúc tách biệt Core & GUI 100%**: Giao thức chuẩn JSON-RPC 2.0 đa kênh (`mcw_core.rpc` — Direct, Stdio Sidecar `--stdio`, Local HTTP + SSE `--http`).

> [!IMPORTANT]
> **Dự án liên quan & Nguồn tham khảo:**
> 1. **Core**: [MCW Launcher Core · Download & Docs](https://mahiru7229.github.io/mcw_core/index.html) — Thư viện core headless độc lập (`mcw_core`), máy chủ JSON-RPC 2.0 và tài liệu API.
> 2. **CurseForge Gateway**: [mahiru7229/mcw-curseforge-gateway](https://github.com/mahiru7229/mcw-curseforge-gateway) — Mã nguồn gateway để người dùng tự host/triển khai riêng (launcher không tích hợp sẵn gateway công khai).
> 3. **Tham khảo**: Dự án có tham khảo cách xử lý lỗi và cơ chế khởi chạy từ [Prism Launcher](https://github.com/PrismLauncher/PrismLauncher).

---

## Tính năng nổi bật

- **Quản lý Instance độc lập**: Mỗi phiên bản chơi là một không gian riêng biệt (Vanilla, Fabric, Quilt, Forge, NeoForge) với mods, saves, configs, Java và JVM flags riêng.
- **Tải & Cài đặt Modpack đa nền tảng**: Hỗ trợ nhập và duyệt modpack từ Modrinth, CurseForge, FTB và ATLauncher.
- **Hỗ trợ tải thủ công thông minh**: Mở đồng thời toàn bộ liên kết tải đếm ngược và tự động nhận diện file tải về trong thư mục `~/Downloads` để nạp ngay vào game.
- **Quản lý Java tự động**: Tự động phát hiện, cài đặt và phân bổ runtime Java tối ưu cho từng phiên bản Minecraft.
- **Tài khoản an toàn**: Hỗ trợ tài khoản Microsoft (OAuth thiết bị) và Offline; access token ngắn hạn chỉ lưu trong bộ nhớ.
- **Sao lưu & Tiện ích**: Tích hợp sao lưu instance, chẩn đoán lỗi, quản lý thế giới/ảnh chụp màn hình/nhật ký trực tiếp, theme tùy biến và cập nhật tự động qua CDN.

---

## Hỗ trợ nền tảng

| Nền tảng | Trạng thái (v1.8.2-beta.1) | Ghi chú |
| --- | --- | --- |
| **Windows 10/11 x64** | Hỗ trợ chính thức | Bản build portable một file thực thi duy nhất (`MCW Launcher.exe`). |
| **Linux x64** | Hỗ trợ chính thức | Bản build portable một file thực thi (`mcw-launcher`). Đã kiểm thử trên Lubuntu/Ubuntu. |
| **Linux ARM64** | Thử nghiệm ban đầu | Hỗ trợ nhận diện Java và metadata; chưa cam kết khởi chạy game. |
| **macOS** | Chưa hỗ trợ | Đang trong kế hoạch lộ trình tương lai. |

---

## Hướng dẫn cài đặt & Chạy từ mã nguồn

### Yêu cầu môi trường
- Python 3.12 trở lên.
- Git và kết nối Internet.

### Khởi chạy GUI
```bash
# Clone repository và chuẩn bị môi trường ảo
git clone https://github.com/mahiru7229/mcw-launcher.git
cd mcw-launcher
python -m venv .venv

# Kích hoạt môi trường ảo:
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux:
source .venv/bin/activate

# Cài đặt dependencies và khởi chạy
python -m pip install --upgrade pip
python -m pip install -e ".[dev,build]"
python launcher.py
```

### Chạy chế độ Headless / JSON-RPC 2.0
MCW Core có thể chạy độc lập không cần GUI PySide6 (sẵn sàng tích hợp Tauri, Web, C# hoặc CLI):
```bash
# Chế độ Stdio Sidecar (giao tiếp qua stdin/stdout)
python -m mcw_core.rpc.cli --stdio

# Chế độ Local HTTP Server + Server-Sent Events (SSE)
python -m mcw_core.rpc.cli --http --host 127.0.0.1 --port 45180
```

---

## Kiểm thử & Đóng gói

```bash
# Chạy bộ kiểm thử tự động
python -m pytest test -v

# Kiểm tra quy chuẩn trước khi phát hành (Preflight)
python tools/release_preflight.py

# Đóng gói bản cài đặt Windows (Release build)
.\build_release.ps1
```

---

## Cấu trúc thư mục

```text
mcw-launcher/
├── launcher.py          # Điểm khởi chạy chính và quản lý vòng đời ứng dụng
├── updater.py           # Bộ cập nhật tự động (Updater v2)
├── mcw_core/            # Lớp API công khai và bộ điều phối JSON-RPC 2.0 (mcw_core.rpc)
├── src/core/            # Tầng xử lý nghiệp vụ nội bộ của Core
├── src/gui/             # Giao diện PySide6 (giao tiếp 100% qua mcw_core)
├── src/models/          # Mô hình dữ liệu nội bộ
├── test/                # Bộ kiểm thử hồi quy & ranh giới phân tách AST (> 2.100 test)
├── assets/ lang/ themes/ # Tài nguyên đồ họa, gói ngôn ngữ và giao diện
├── tools/               # Công cụ kiểm tra preflight, đóng gói và dịch thuật
└── docs/                # Tài liệu kỹ thuật chi tiết
```

---

## Tài liệu tham khảo

- [Kiến trúc phân tách Core & GUI](docs/ARCHITECTURE.md)
- [MCW Core API & Giao thức JSON-RPC 2.0](docs/MCW_CORE_LIBRARY.md)
- [Hệ thống Instance](docs/INSTANCE_SYSTEM.md)
- [Hệ thống Hotfix CDN](docs/HOTFIX_SYSTEM.md)
- [Hướng dẫn tạo Theme tùy chỉnh](docs/THEME_CREATION_GUIDE.md)
- [Lịch sử thay đổi chi tiết (Changelog)](CHANGELOG.md)
- [Ghi chú bản phát hành v1.8.1](docs/releases/v1.8.1.md)

---

## Giấy phép & Bản quyền

Phát hành theo [Giấy phép MIT](LICENSE). Minecraft là thương hiệu thuộc sở hữu của Mojang Studios / Microsoft. Dự án này là phần mềm cộng đồng độc lập, không liên kết hoặc được Mojang/Microsoft tài trợ.
