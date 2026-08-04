# MCW Launcher v1.0.2

> Hotfix ổn định cho cơ chế khởi động lại launcher trong bản PyInstaller one-file.

---

# Tiếng Việt

## Tổng quan

MCW Launcher v1.0.2 sửa lỗi launcher không thể mở lại sau khi người dùng đổi ngôn ngữ và chọn **Khởi động lại ngay**.

Trong bản EXE one-file, tiến trình mới trước đây được tạo bằng chính executable hiện tại nhưng vẫn kế thừa trạng thái nội bộ của PyInstaller. Tiến trình con có thể tái sử dụng thư mục giải nén tạm của tiến trình cũ; khi tiến trình cũ thoát và dọn thư mục này, lần khởi động mới có thể thiếu các module đã đóng gói, ví dụ `PySide6.QtWidgets`.

## Thay đổi

- Khởi động lại bản frozen bằng chính `sys.executable`.
- Truyền `PYINSTALLER_RESET_ENVIRONMENT=1` cho tiến trình thay thế.
- Không sửa trực tiếp `os.environ` của launcher đang chạy.
- Dùng `subprocess.Popen` với command, working directory và environment tách biệt.
- Chạy source vẫn khởi động lại bằng Python hiện tại và `launcher.py`.
- Trả về lỗi an toàn nếu không thể tạo tiến trình thay thế.
- Thêm regression test cho source mode, frozen mode, PyInstaller environment và spawn failure.

## Phạm vi ảnh hưởng

Hotfix không thay đổi:

- Instance hoặc dữ liệu Minecraft.
- Tài khoản Microsoft/offline.
- Theme và language pack.
- Mod, modpack hoặc provider.
- CurseForge gateway configuration.
- Public API của MCW Core.

MCW Core được đánh số lại thành `1.0.2` để đồng bộ metadata phát hành; public API và hành vi core không thay đổi.

## Kiểm tra thủ công trên Windows

```text
Mở MCW Launcher.exe
→ Cài đặt launcher
→ đổi ngôn ngữ
→ Lưu
→ Khởi động lại ngay
→ launcher đóng
→ cùng file EXE mở lại
→ giao diện dùng ngôn ngữ mới
```

Kiểm tra thêm cả hai chiều:

```text
English → Vietnamese
Vietnamese → English
```

---

# English

## Overview

MCW Launcher v1.0.2 fixes a frozen-build restart failure that could occur after changing the launcher language and selecting **Restart now**.

The replacement one-file executable previously inherited PyInstaller's parent-process state and could reuse the current temporary extraction directory. Once the old process exited and cleaned that directory, the replacement process could fail to import bundled modules such as `PySide6.QtWidgets`.

## Changes

- Restart frozen builds through the current `sys.executable`.
- Pass `PYINSTALLER_RESET_ENVIRONMENT=1` only to the replacement process.
- Do not mutate the running launcher's global environment.
- Spawn the replacement with an explicit command, working directory, and environment.
- Preserve the Python plus `launcher.py` restart path for source checkouts.
- Fail safely when the replacement process cannot be created.
- Add regression coverage for source mode, frozen mode, environment reset, and spawn failure.

## Scope

No instance, account, content, provider, theme, language-pack, or public core API behavior is changed. MCW Core is version-aligned to `1.0.2` for release metadata only.
