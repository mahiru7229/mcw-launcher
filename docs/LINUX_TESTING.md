# Kiểm thử MCW Launcher trên Lubuntu

Tài liệu này áp dụng cho `v1.5.0-beta.2`. Có thể chạy từ source để regression, nhưng automatic updater chỉ bật trong ZIP Linux x64 native do GitHub Release build.

## 1. Chuẩn bị hệ thống

Trên Lubuntu/Ubuntu mới, cài Python virtual environment và các thư viện Qt phổ biến:

```bash
sudo apt update
sudo apt install -y python3 python3-venv libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0
```

Không chạy launcher bằng `sudo` vì tài khoản, config và runtime sẽ bị tạo dưới user root.

## 2. Cài môi trường source

```bash
cd mcw-launcher-v1.5.0-beta.2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## 3. Chạy Linux preflight

```bash
python tools/linux_preflight.py
```

Preflight kiểm tra Qt, display session, manifest Mojang, metadata Java Linux từ Adoptium và các Java đã cài. Nếu `qt.ok` là `false`, lỗi thường chỉ rõ thư viện `.so` còn thiếu.

## 4. Chạy launcher

```bash
python launcher.py
```

## 5. Kiểm tra migration và XDG

Trên Linux, Alpha 3 lưu dữ liệu theo XDG:

- Config: `~/.config/mcw-launcher`
- Instance, account, backup, theme và runtime: `~/.local/share/mcw-launcher`
- Cache: `~/.cache/mcw-launcher`
- Log: `~/.local/state/mcw-launcher/logs`

Lần chạy đầu, launcher copy dữ liệu portable nằm cạnh source vào các vị trí trên. Dữ liệu Alpha 2 được giữ nguyên và file đích có nội dung khác không bị ghi đè. Nếu Alpha 2 và Alpha 3 nằm ở hai thư mục khác nhau, chỉ định thư mục cũ ở lần chạy đầu:

```bash
MCW_LEGACY_ROOT="$HOME/mcw-launcher-v1.5.0-alpha.2" python launcher.py
```

Để chủ động giữ layout portable, dùng `MCW_PORTABLE=1`. Không xóa thư mục Alpha 2 trước khi xác nhận instance và account xuất hiện đúng trong Alpha 3.

## 6. Checklist Beta 2

1. Launcher mở được và không báo lỗi startup/account security.
2. Danh sách version Minecraft xuất hiện.
3. Các combobox co giãn theo mục được chọn nhưng không làm cửa sổ đổi kích thước.
4. Tạo một tài khoản offline và Vanilla instance.
5. Để Java ở chế độ automatic rồi launch game.
6. Xác nhận managed Java nằm dưới `~/.local/share/mcw-launcher/runtimes` và `bin/java` có quyền execute.
7. Vào menu chính Minecraft, thoát game và kiểm tra process state trở về stopped.
8. Tạo và launch một instance Fabric, sau đó một instance Quilt.
9. Đăng nhập Microsoft, xác nhận trình duyệt mở và quay lại launcher thành công.
10. Mở trang Account Security và xác nhận backend là `Linux Secret Service`. Nếu launcher báo fallback local, kiểm tra keyring/Secret Service của desktop.
11. Tắt mạng, xác nhận badge chuyển sang Offline và instance đã cache vẫn launch nhanh.
12. Dùng Stop/Kill với một game đang chạy và xác nhận không còn tiến trình Java con của phiên đó.
13. Xuất diagnostics nếu có lỗi và ghi kèm output của `linux_preflight.py`.
14. Tạo Forge instance cho Minecraft 1.20.1, để Java Automatic, launch tới menu chính rồi thoát bình thường.
15. Tạo NeoForge instance cho Minecraft 1.21.1, launch, Stop/Kill và xác nhận không còn Java process con.
16. Mở Add Instance, First Run và Instance Settings ở kích thước màn hình nhỏ; widget không bị ép co hoặc chồng chữ, thanh cuộn dọc xuất hiện khi cần.
17. Khởi động lại launcher rồi launch lại Forge/NeoForge để xác nhận profile, libraries và managed Java cache được dùng lại.
18. Thu nhỏ OptiFine và Instance Info; nội dung phải cuộn dọc, không cắt chữ hoặc đẩy action button ra ngoài màn hình.
19. Thử Open Folder từ instance, mod manager, logs, diagnostics và theme; file manager của Lubuntu phải mở đúng đường dẫn.

## 7. Test cập nhật thật Beta 1 → Beta 2

Chạy gói Beta 1 Linux x64 đã phát hành, chọn cập nhật Beta 2 và xác nhận download cache, SHA-256, manifest Linux, staging, atomic replacement, mode `0755`, restart và rollback.

Khi kiểm tra GUI Beta 2, xác nhận:

1. Bản chạy từ source báo updater chỉ dành cho packaged release.
2. Gói `linux-x64.zip` chạy được và nhận đúng kênh Beta.
3. Gói cài đặt nằm trong Home, không dùng `sudo` và không đặt trong thư mục chỉ đọc.
4. Account, instance, world và setting XDG không thay đổi khi chạy test updater Core.

## 8. Giới hạn Beta 2

- Beta 1 → Beta 2 là gate cập nhật thật đầu tiên trên Linux; vẫn giữ bản Beta 1 ZIP để rollback thủ công nếu môi trường desktop có lỗi ngoài dự kiến.
- Updater không gọi `sudo`. Thư mục cài đặt không ghi được sẽ yêu cầu update thủ công.
- GPU preference integration chỉ hỗ trợ Windows; Linux trả trạng thái unsupported và không chặn launch.
- Linux ARM64 có nhận diện/metadata đúng nhưng chưa được xác nhận bằng launch thực tế.
