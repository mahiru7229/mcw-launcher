# MCW Launcher v1.0.0-beta.6

## Tiếng Việt

Beta 6 hoàn thiện luồng **nhập/xuất modpack theo nguồn gốc provider** và định dạng **Portable MCWPack**, đồng thời làm rõ nút ẩn/hiện thanh điều hướng.

### Import modpack từ gói local

- Add Instance tách rõ hai hướng: duyệt modpack trực tuyến hoặc nhập package đã tải từ provider.
- Nhận dạng định dạng bằng nội dung archive, không chỉ dựa vào phần mở rộng.
- Hỗ trợ Modrinth `.mrpack`, CurseForge ZIP có `manifest.json`, MCW Provider Profile và Portable MCWPack.
- Đọc manifest trực tiếp từ package local; CurseForge API chỉ còn được dùng khi cần resolve `projectID/fileID` thành file tải ở lần Launch đầu.
- Giữ nguyên provenance, project/version/file ID, hash, overrides và package gốc.
- Luôn cho người dùng kiểm tra Instance Settings trước khi tạo instance.
- Giữ deferred download: import chỉ tạo instance và lưu manifest; mod được tải khi nhấn Launch.

### Hai lựa chọn export

- **Provider Profile:** giữ package native hoặc provider reference, thêm MCW instance settings bằng sidecar và không nhận MCW là tác giả modpack.
- **Portable MCWPack:** Smart mode tham chiếu provider và chuyển file không thể tải thành manual/embedded theo metadata; Full mode đóng gói các mod hiện có cho chuyển riêng tư/offline.
- Cả hai định dạng đều ghi nguồn gốc, checksum, cài đặt portable đã loại đường dẫn Java tuyệt đối và thông báo trách nhiệm phân phối.
- Portable import xác minh hash/kích thước, bảo vệ đường dẫn archive, áp dụng overrides và dựng lại registry provider để lần Launch đầu tiếp tục tải.

### Sidebar

- Thay nút mũi tên giống “Back” bằng nút menu `☰` có nhãn **Ẩn thanh bên**.
- Khi sidebar đã thu gọn, nút vẫn dùng biểu tượng menu và tooltip **Hiện thanh bên**.
- Bổ sung accessible name/description để hành vi rõ ràng với công cụ trợ năng.

## English

Beta 6 completes **provider-preserving modpack import/export** and the **Portable MCWPack** format, while making the sidebar control unambiguous.

### Local provider-package import

- Add Instance clearly separates online browsing from importing a package downloaded from a provider.
- Detect package formats from archive contents rather than trusting file extensions alone.
- Support Modrinth `.mrpack`, CurseForge ZIP with `manifest.json`, MCW Provider Profile, and Portable MCWPack.
- Parse local manifests directly; the CurseForge API is only needed later to resolve `projectID/fileID` entries during first-launch download.
- Preserve provenance, provider IDs, hashes, overrides, and the original package.
- Always review Instance Settings before instance creation.
- Preserve deferred downloads: import stores the manifest and creates the instance; managed mods download on Launch.

### Two export choices

- **Provider Profile:** preserve the native package/provider reference and add MCW settings as a sidecar without claiming authorship.
- **Portable MCWPack:** Smart mode references provider files and classifies unavailable content; Full mode embeds available mods for private/offline transfer.
- Both formats record origin/checksums, strip machine-specific Java paths, and include a distribution-responsibility notice.
- Portable import verifies hashes/sizes, guards archive paths, applies overrides, and reconstructs provider registries for first-launch download.

### Sidebar

- Replace the back-like arrow with a `☰` menu control labelled **Hide sidebar**.
- The collapsed state keeps the menu symbol and uses a **Show sidebar** tooltip.
- Add accessible naming and description for assistive technology.
