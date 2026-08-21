# Kiểm thử MCW Launcher trên Lubuntu

Tài liệu này áp dụng cho `v1.5.0-alpha.2`. Alpha 2 chạy từ source; chưa có AppImage hoặc `.deb`.

## 1. Chuẩn bị hệ thống

Trên Lubuntu/Ubuntu mới, cài Python virtual environment và các thư viện Qt phổ biến:

```bash
sudo apt update
sudo apt install -y python3 python3-venv libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0
```

Không chạy launcher bằng `sudo` vì tài khoản, config và runtime sẽ bị tạo dưới user root.

## 2. Cài môi trường source

```bash
cd mcw-launcher-v1.5.0-alpha.2
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

Checklist Alpha 2:

1. Launcher mở được và không báo lỗi startup/account security.
2. Danh sách version Minecraft xuất hiện.
3. Các combobox co giãn theo mục được chọn nhưng không làm cửa sổ đổi kích thước.
4. Tạo một tài khoản offline và Vanilla instance.
5. Để Java ở chế độ automatic rồi launch game.
6. Xác nhận managed Java nằm tại `runtimes/java-<major>/bin/java` và có quyền execute.
7. Vào menu chính Minecraft, thoát game và kiểm tra process state trở về stopped.
8. Xuất diagnostics nếu có lỗi và ghi kèm output của `linux_preflight.py`.

## Giới hạn Alpha 2

- Automatic updater chỉ hỗ trợ Windows packaged build.
- GPU preference integration chỉ hỗ trợ Windows; Linux trả trạng thái unsupported và không chặn launch.
- Forge/NeoForge và Microsoft login trên Linux chưa phải release gate của Alpha 2.
- Linux ARM64 có nhận diện/metadata đúng nhưng chưa được xác nhận bằng launch thực tế.
