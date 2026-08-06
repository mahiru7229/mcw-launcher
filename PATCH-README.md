# MCW Launcher v1.1.1-beta.4 — OptiFine import-only patch

## Áp dụng

1. Dùng source **v1.1.1-beta.3** làm baseline.
2. Đóng launcher và Minecraft.
3. Giải nén ZIP này vào thư mục gốc repository, cho phép ghi đè file.
4. Chạy `python -m pytest -q` rồi smoke test trên Windows bằng một JAR OptiFine thật.

Patch không xóa file nào và không chứa MCW Core source archive hoặc wheel riêng. Các file dưới `mcw_core/` là public facade được bundle trong repository launcher.

## Thay đổi

- Bỏ OptiFine version browser, preview filter, refresh và metadata request khỏi runtime UI/API.
- Chỉ nhập JAR OptiFine chính thức; MCW nhận diện Minecraft version từ tên file và xác minh lại trong Core.
- Vanilla tạo standalone component/profile.
- Forge instance hoặc Forge modpack cài OptiFine dưới dạng mod được quản lý.
- Chặn JAR sai Minecraft version trước khi commit.
- Giữ Repair, Uninstall, rollback giao dịch, provenance và manual-only export.

## Validation

- `1368 passed, 87 skipped, 2 warnings`
- `compileall` đạt cho `src`, `mcw_core` và `test`.
- GUI tests mới được thu thập nhưng skip trong môi trường không có PySide6.

---

## English

Apply this patch over **v1.1.1-beta.3** by extracting it at the repository root. It replaces the online OptiFine catalog with an import-only JAR workflow for Vanilla standalone components and Forge instances/modpacks.
