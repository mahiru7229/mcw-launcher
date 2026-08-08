# MCW Launcher v1.3.0-beta.3

## Tiếng Việt

MCW Launcher **v1.3.0-beta.3** tiếp tục tối ưu storage theo hướng bảo thủ: chỉ xóa **Minecraft version JAR không còn được dùng**, không xóa cả thư mục version.

### Unused Minecraft version JAR cleanup

- Storage Review nhận diện file `cache/versions/<version>/<version>.jar` đã qua retention và không còn instance/loader nào reference.
- Version đang được Vanilla, Forge, NeoForge, Fabric hoặc Quilt sử dụng luôn được bảo vệ.
- Launcher tiếp tục lần theo `inheritsFrom` để giữ base Minecraft JAR mà loader cần.
- Sửa reference mapping Fabric/Quilt theo đúng profile cache thực tế: `fabric-loader-<loader>-<game>` và `quilt-loader-<loader>-<game>`.
- Version JSON/profile metadata và các file khác trong cùng thư mục được giữ lại. Nếu người dùng cần version đó trong tương lai, launcher vẫn có metadata để tải client JAR lại.
- Cleanup preview tiếp tục hiển thị từng JAR, path, reason, dung lượng có thể giải phóng, subtotal theo category và tổng dung lượng trước khi xác nhận.
- Trước khi xóa thật, Core scan/revalidate lại; nếu version vừa trở thành active/reference thì item bị skip.

### Không thay đổi

- Provider API Cache không bị xóa hoặc đổi lifecycle.
- Shared ContentStore/loader staging behavior của Beta 1 giữ nguyên.
- Fix xóa sạch instance của Beta 2 giữ nguyên.
- Không đụng saves, configs, worlds, Java runtimes, Minecraft assets hoặc shared libraries.

### Version metadata

- Launcher runtime: `v1.3.0-beta.3`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.3.0b3`

## English

MCW Launcher **v1.3.0-beta.3** narrows cached-version cleanup to unused canonical Minecraft version JARs. Version directories and JSON/profile metadata are retained, active loader inheritance chains are protected, and cleanup is revalidated immediately before deletion. Fabric and Quilt profile references now match their real cached directory names. Provider API cache and the validated Beta 1/Beta 2 storage behavior remain unchanged.
