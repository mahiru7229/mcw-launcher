# MCW Launcher v1.1.1-beta.5 — Forge JNA cache hotfix v5

## Mục tiêu

Bản vá này sửa lỗi Forge cache refresh báo:

```text
Could not resolve legacy Forge native library 'net.java.dev.jna:jna-platform:5.10.0' (natives-windows).
```

## Nguyên nhân

Hotfix v4 dùng điều kiện quá rộng: mọi Maven artifact có tên kết thúc bằng `-platform` đều bị xem là thư viện native cổ. Điều đó đúng với một số artifact Minecraft cũ như `lwjgl-platform` và `jinput-platform`, nhưng sai với `jna-platform`, vốn là JAR Java thông thường.

Cache được v4 ghi trước đó có thể đã chứa metadata sai:

```json
{
  "name": "net.java.dev.jna:jna-platform:5.10.0",
  "natives": {"windows": "natives-windows"}
}
```

Launcher sau đó cố tải một classifier không tồn tại và dừng trước khi launch.

## Thay đổi

- Chỉ tự suy luận `natives-windows` cho danh sách Maven coordinate native cổ đã biết.
- Không còn dùng quy tắc chung `artifact.endswith("-platform")`.
- Phát hiện cache v4 đã bị gắn nhầm native metadata cho `jna-platform`.
- Tự loại bỏ metadata sai và giữ nguyên regular artifact `jna-platform-5.10.0.jar`.
- Tái sử dụng Forge profile đã cài; không chạy lại Forge installer.
- Vẫn giữ hỗ trợ native classifier cho LWJGL, JInput và Twitch platform cũ.

## Phạm vi

Đây là ZIP tích lũy, bao gồm toàn bộ hotfix v1-v4 trước đó:

- dependency version do modpack ghim;
- provider bridge CurseForge/Modrinth;
- Forge JarJar identity;
- embedded/provided dependency như Flywheel trong Create;
- Forge cache reuse;
- JNA platform cache migration.

Có thể áp dụng lên Beta 5 gốc hoặc chồng lên hotfix v4.

## Cách áp dụng

1. Đóng MCW Launcher.
2. Giải nén ZIP vào thư mục root của source `v1.1.1-beta.5`.
3. Cho phép ghi đè file.
4. Mở launcher và launch instance lại.

Không cần xóa instance, Forge profile, modpack registry hay thư mục libraries. Lần launch đầu tiên có thể hiện `Refreshing cached Minecraft Forge ... metadata...`; quá trình này chỉ sửa JSON cache tại chỗ và không chạy installer.

## Xác thực

```text
1394 passed
88 skipped
2 expected warnings
compileall passed
ZIP integrity passed
```
