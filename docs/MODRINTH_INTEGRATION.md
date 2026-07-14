# Modrinth integration

## Tiếng Việt

MCW Launcher hỗ trợ duyệt và cài nội dung Fabric trực tiếp từ Modrinth.

### Mod

Mở một instance Fabric, chọn **Manage mods**, sau đó chọn **Browse Modrinth**.

Launcher sẽ:

- Chỉ tìm các mod hỗ trợ đúng phiên bản Minecraft và Fabric.
- Hiển thị các version tương thích của dự án.
- Tự cài các dependency `required` có thể tải từ Modrinth.
- Kiểm tra SHA-1 và SHA-512 trước khi thêm file vào instance.
- Lưu nguồn gốc project/version tại `.mcw/modrinth.json` để lần cập nhật sau thay đúng file cũ.

### Modpack

Trong trang **Instances**, chọn **Browse Modrinth modpacks**.

Launcher sẽ tải file `.mrpack`, kiểm tra manifest và tự:

- Chọn Minecraft version được pack yêu cầu.
- Cài đúng Fabric Loader version.
- Tải các file dành cho client.
- Áp dụng `overrides`, sau đó `client-overrides`.
- Tạo instance mới chỉ sau khi toàn bộ file đã được chuẩn bị thành công.

Hiện tại chỉ modpack Fabric được hỗ trợ. Pack Forge, NeoForge và Quilt sẽ bị từ chối rõ ràng.

### An toàn

- Không cho đường dẫn trong `.mrpack` thoát khỏi folder instance.
- Chặn file override ghi đè `instance.json`, `settings.json` và metadata `.mcw`.
- Chỉ chấp nhận URL HTTPS từ danh sách host được định dạng `.mrpack` cho phép.
- Không giải nén symbolic link.
- Có giới hạn số file, tổng dung lượng, kích thước override và độ dài đường dẫn.

## English

MCW Launcher can browse and install Fabric content directly from Modrinth.

### Mods

Open a Fabric instance, choose **Manage mods**, then **Browse Modrinth**.

The launcher filters projects by Minecraft version and Fabric, installs required Modrinth dependencies, verifies SHA-1/SHA-512, and stores project provenance for safe updates.

### Modpacks

On the **Instances** page, choose **Browse Modrinth modpacks**. The launcher downloads the `.mrpack`, installs its declared Minecraft and Fabric Loader versions, downloads client files, applies `overrides` and `client-overrides`, then creates a new instance.

Only Fabric modpacks are supported in this release.
