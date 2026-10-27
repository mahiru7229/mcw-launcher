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
  <img src="https://img.shields.io/badge/version-v1.8.5-brightgreen" alt="v1.8.5">
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB" alt="Python 3.12+">
</p>

> [!NOTE]
> **Phiên bản mới nhất (v1.8.5)**:
> - **Tích hợp trực tiếp CurseForge Core API v1 chính thức**: Duyệt, tìm kiếm và cài đặt Mod / Modpack trực tiếp từ CurseForge ngay trên bản phát hành chính thức mà không cần tự thiết lập Gateway trung gian; tinh gọn phần cài đặt thành 1 ô nhập Khóa API cá nhân (tùy chọn).
> - **Duyệt danh sách Mod & Modpack phổ biến tức thì**: Tự động nạp danh sách các dự án nổi bật ngay khi mở trình duyệt CurseForge hoặc đổi bộ lọc Mod Loader mà không bắt buộc phải gõ từ khóa tìm kiếm.
> - **Sửa lỗi giao diện & Tối ưu hiệu năng Timer nền**: Khắc phục lỗi hiển thị nhãn bộ lọc Loader (`Quilt` / `Forge`) trên `ModsPage` và tối ưu hóa `_cooldown_timer` chỉ kích hoạt khi có thời gian chờ làm mới.
> - **Tối ưu hóa tốc độ tải mạng (~80ms / 12.5 Hz) & [Thử nghiệm] Cầu nối cập nhật (Legacy Update Bridge)**: Cập nhật tốc độ tải thực theo thời gian thực, hỗ trợ nguồn cập nhật kép Cloudflare CDN / GitHub kèm cơ chế thử nghiệm nâng cấp tự động cho các bản Launcher cũ.

> [!IMPORTANT]
> **Dự án liên quan & Nguồn tham khảo:**
> 1. **Core**: [MCW Launcher Core · Download & Docs](https://mahiru7229.github.io/mcw_core/index.html) — Thư viện core headless độc lập (`mcw_core`), máy chủ JSON-RPC 2.0 và tài liệu API.
> 2. **Tham khảo**: Dự án có tham khảo cách xử lý lỗi và cơ chế khởi chạy từ [Prism Launcher](https://github.com/PrismLauncher/PrismLauncher).

---

## Tính năng nổi bật

- **Quản lý Instance độc lập**: Mỗi phiên bản chơi là một không gian riêng biệt (Vanilla, Fabric, Quilt, Forge, NeoForge) với mods, saves, configs, Java và JVM flags riêng.
- **Tải & Cài đặt Modpack đa nền tảng**: Hỗ trợ nhập và duyệt trực tiếp Mod / Modpack từ Modrinth, CurseForge, FTB và ATLauncher.
- **Hỗ trợ tải thủ công thông minh**: Mở đồng thời toàn bộ liên kết tải đếm ngược đối với các mod tắt phân phối bên thứ ba và tự động nhận diện file tải về trong thư mục `~/Downloads` để nạp ngay vào game.
- **Quản lý Java tự động**: Tự động phát hiện, cài đặt và phân bổ runtime Java tối ưu cho từng phiên bản Minecraft.
- **Tài khoản an toàn**: Hỗ trợ tài khoản Microsoft (OAuth thiết bị) và Offline; access token ngắn hạn chỉ lưu trong bộ nhớ.
- **Sao lưu & Tiện ích**: Tích hợp sao lưu instance, chẩn đoán lỗi, quản lý thế giới/ảnh chụp màn hình/nhật ký trực tiếp, theme tùy biến và cập nhật tự động qua Cloudflare Edge CDN & GitHub.

---

## Hỗ trợ nền tảng

| Nền tảng | Trạng thái (v1.8.5) | Ghi chú |
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
- [Ghi chú bản phát hành v1.8.5](docs/releases/v1.8.5.md)

---

## Giấy phép, Bản quyền & Quy định khi Fork

Phát hành theo [Giấy phép MIT](LICENSE) kèm điều khoản bổ sung về Khóa API và Định danh dự án:

- **Khóa API Dịch vụ bên thứ ba & Định danh Dự án**:
  - Khóa **CurseForge Core API** (do Overwolf/CurseForge cấp riêng cho MCW Launcher), mã định danh **Microsoft Client ID** (`MICROSOFT_CLIENT_ID`), tên gọi **"MCW Launcher"**, biểu tượng và chuỗi định danh `User-Agent` (`mahiru7229/mcw-launcher`) thuộc quyền sử dụng định danh riêng của dự án MCW Launcher chính thức và **không thuộc phạm vi cấp phép tái phân phối của giấy phép MIT**.
  - Nếu bạn **fork, sửa đổi hoặc phân phối lại** phần mềm này (dưới dạng mã nguồn hoặc bản thực thi), bạn **bắt buộc phải**:
    1. Tự đăng ký và cung cấp **CurseForge API Key** riêng tại [Overwolf Developer Console](https://console.curseforge.com/) cũng như **Microsoft Client ID** riêng.
    2. **Không được** trích xuất, tái sử dụng hoặc phân phối lại bất kỳ khóa API nào từ các bản phát hành nhị phân chính thức của MCW Launcher.
    3. Thay đổi tên ứng dụng, biểu tượng và chuỗi định danh `User-Agent` trong `src/config.py` để không mạo danh MCW Launcher khi giao tiếp với CurseForge, Modrinth, FTB, ATLauncher và Microsoft.

Minecraft là thương hiệu thuộc sở hữu của Mojang Studios / Microsoft. Dự án này là phần mềm cộng đồng độc lập, không liên kết hoặc được Mojang/Microsoft tài trợ.
