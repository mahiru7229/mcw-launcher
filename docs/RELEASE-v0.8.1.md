# MCW Launcher v0.8.1

`v0.8.1` là bản Stable hotfix cho luồng CurseForge mods/modpacks và quản lý mod khi launcher đang chuẩn bị instance.

## Tiếng Việt

### Sửa lỗi CurseForge và mod đa loader

- Dùng gateway công khai `https://mcw-curseforge-gateway.vercel.app/api/curseforge` làm endpoint mặc định trên cài đặt mới; gateway tùy chỉnh và biến môi trường vẫn được ưu tiên.
- Không còn lọc cứng file CurseForge chỉ theo nhãn Fabric/Forge từ API.
- Sắp xếp file khớp loader lên trước, nhưng vẫn hiển thị và cho phép thử cài file bị gắn nhãn loader khác.
- Sau khi tải, launcher kiểm tra metadata thật bên trong JAR trước khi thêm vào instance.
- JAR chứa đồng thời `fabric.mod.json` và `META-INF/mods.toml` được nhận diện là file dùng chung Fabric/Forge.
- Khi cài vào instance Forge, launcher đọc metadata Forge; khi cài vào instance Fabric, launcher đọc metadata Fabric.
- Modpack CurseForge có file dùng chung nhưng bị API gắn nhãn một loader sẽ không còn bị chặn trước khi tải.
- File loader khác do modpack khai báo vẫn được giữ lại dưới trạng thái **chưa xác minh** thay vì bị tải lại vô hạn.
- Khi cài mod riêng lẻ bị gắn nhãn loader khác hoặc không rõ loader, launcher hiện cảnh báo và cho phép người dùng chọn **vẫn cài**.
- Nhận diện Forge `LANGPROVIDER`, `LIBRARY` và `GAMELIBRARY` thông qua `FMLModType` trong `META-INF/MANIFEST.MF`; sửa trường hợp như Kotlin for Forge bị nhận nhầm là file không hợp lệ.
- File thiếu metadata Minecraft version từ API được phép đi tiếp tới bước kiểm tra JAR, trong khi mismatch phiên bản đã biết vẫn bị chặn.
- Thêm nút **Mở trong trình duyệt** trong trình duyệt CurseForge và trang Mods.
- Chỉ mở liên kết HTTPS thuộc miền CurseForge; liên kết không an toàn từ gateway sẽ bị bỏ qua và thay bằng URL CurseForge được tạo từ slug.

### Tải xuống và xử lý lỗi

- Ưu tiên metadata và `downloadUrl` đã lưu trong registry, tránh gọi lại gateway không cần thiết trong mỗi lần launch.
- Khi gateway không lấy được URL, launcher thử tìm **bản mirror có SHA-1 trùng tuyệt đối trên Modrinth**; file vẫn phải vượt qua kiểm tra SHA-1 và kích thước trước khi cài.
- Không đoán URL CDN CurseForge và không bỏ qua checksum.
- Phân loại lỗi retry được và lỗi cố định. Lỗi thiếu credential, phân phối bên thứ ba bị tắt và yêu cầu tải thủ công không còn bị thử lại đủ ba vòng.
- Các lỗi gateway giống nhau được gom thành một nhóm thay vì in hàng chục Request ID riêng biệt.
- Progress cuối luồng hiển thị số file đã tải và số file được chấp nhận với cảnh báo tương thích.
- Khi không tìm thấy mirror chính xác, launcher chuyển sang tải thủ công và giữ nút **Mở trong trình duyệt**.

### Sửa lỗi launch lock

- Managed modpack có thể tải và thay đổi mod khi lock thuộc đúng lần launch đang ở trạng thái preparing.
- Instance đã chạy thật, token sai hoặc thao tác từ process khác vẫn bị chặn.

### Phiên bản

```text
VERSION = v0.8.1
VERSION_ID = 0.8.1
UPDATE_CHANNEL = stable
```

---

## English

### CurseForge and multi-loader mod fixes

- Use `https://mcw-curseforge-gateway.vercel.app/api/curseforge` as the default public gateway on fresh installations while preserving custom gateway and environment-variable priority.
- Stop treating CurseForge Fabric/Forge labels as strict installation authority.
- Rank likely loader matches first while still showing and allowing an install attempt for files labelled for another loader.
- Validate the actual downloaded JAR metadata before adding the file to an instance.
- Recognize JARs containing both `fabric.mod.json` and `META-INF/mods.toml` as Fabric/Forge universal files.
- Read Forge metadata for Forge instances and Fabric metadata for Fabric instances.
- CurseForge modpacks are no longer blocked before download when a universal dependency is labelled as only one loader.
- Loader-mismatched files declared by a modpack are preserved as **unverified** instead of being downloaded repeatedly.
- Installing a standalone mod with unknown or mismatched loader metadata now shows a warning and offers an explicit **install anyway** choice.
- Recognize Forge `LANGPROVIDER`, `LIBRARY`, and `GAMELIBRARY` JARs through `FMLModType` in `META-INF/MANIFEST.MF`, including Kotlin-for-Forge style language providers.
- Allow files with missing Minecraft-version metadata to continue to JAR validation while keeping known version mismatches blocked.
- Add an **Open in browser** action to the CurseForge browser and Mods page.
- Only open HTTPS CurseForge domains; unsafe gateway-provided URLs are ignored and replaced with a slug-based CurseForge URL.

### Downloads and failure handling

- Reuse file metadata and `downloadUrl` stored in the registry instead of contacting the gateway again during every launch.
- If the gateway cannot resolve a URL, try an **exact SHA-1 mirror on Modrinth**; the downloaded file must still pass SHA-1 and size verification.
- Do not guess CurseForge CDN URLs and never bypass checksum validation.
- Separate retryable failures from permanent failures. Missing gateway credentials, disabled third-party distribution, and manual-download requirements no longer consume all three rounds.
- Group repeated gateway failures instead of printing many near-identical Request IDs.
- Report how many files were downloaded and how many were accepted with compatibility warnings.
- Fall back to the manual-download browser flow when no exact mirror exists.

### Launch-lock fix

- Managed modpacks may modify mods when the lock belongs to the same launch while it is still preparing.
- Running instances, incorrect tokens, and external operations remain blocked.

### Version

```text
VERSION = v0.8.1
VERSION_ID = 0.8.1
UPDATE_CHANNEL = stable
```
