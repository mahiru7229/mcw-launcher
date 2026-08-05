# MCW Launcher v1.1.0-beta.6 — Forge 1.6.4 LaunchWrapper hotfix

Áp dụng patch này lên **v1.1.0-beta.6** đã cài trước đó.

## Cách áp dụng

1. Đóng MCW Launcher.
2. Giải nén ZIP vào thư mục gốc repository launcher.
3. Cho phép ghi đè các file trùng tên.
4. Chạy lại launcher rồi Launch instance Forge 1.6.4.

Launcher sẽ tự bỏ cache Forge legacy chưa đầy đủ và dựng lại profile. Không cần xóa instance hoặc xóa toàn bộ cache thủ công.

## Phạm vi

- Tải và tạo metadata SHA-1 cho dependency Forge legacy thiếu `downloads.artifact`.
- Đưa `net.minecraft:launchwrapper:1.8` vào classpath.
- Dùng `os.pathsep` để giữ dấu phân cách classpath đúng nền tảng (`;` trên Windows).
- Chỉ vô hiệu hóa cache LaunchWrapper legacy chưa đầy đủ; Forge hiện đại không bị cài lại.
- Không chứa package `mcw_core/`, wheel hoặc Core source archive.
