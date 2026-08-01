# MCW Launcher v0.12.0-beta.2

## Tiếng Việt

### NeoForge

- Thêm NeoForge như một mod loader độc lập, không alias thành Forge.
- Hỗ trợ catalog NeoForge chính thức cho cả nhánh legacy Minecraft 1.20.1 và artifact NeoForge hiện đại.
- Hỗ trợ tạo instance, cài loader, đổi phiên bản, launch, repair và rollback profile NeoForge.
- Tích hợp NeoForge với Manage Mods, Modrinth, CurseForge, import/update modpack, diagnostics và progress.
- Đọc cả `META-INF/neoforge.mods.toml` hiện đại và `META-INF/mods.toml` legacy trong instance NeoForge.
- Cập nhật MCW LAN Agent để nhận biết loader NeoForge, đọc NeoForm mapping và thử target SRG NeoForge trước các target fallback an toàn.
- Build lại và pin SHA-256 mới của `runtime/mcw-lan-agent.jar`.
- Cập nhật giao diện, bộ lọc loader, bản dịch và tên gói diagnostics cho NeoForge.
- Cập nhật metadata sang `v0.12.0-beta.2`, kênh `beta`.

### Giới hạn xác minh

- Installer/profile/runtime được kiểm tra bằng test tự động và metadata chính thức của NeoForged.
- Java smoke test của MCW LAN Agent đã chạy thành công.
- Môi trường phát triển không có DNS cho tiến trình Python, nên chưa thực hiện live install và live Minecraft launch trong lần build này.

## English

### NeoForge

- Added NeoForge as a distinct mod loader instead of aliasing it to Forge.
- Added the official NeoForge catalog for both the legacy Minecraft 1.20.1 line and modern NeoForge artifacts.
- Added instance creation, loader installation, version switching, launch, repair, and profile rollback for NeoForge.
- Integrated NeoForge with Manage Mods, Modrinth, CurseForge, modpack import/update, diagnostics, and progress reporting.
- Added support for modern `META-INF/neoforge.mods.toml` and legacy `META-INF/mods.toml` metadata in NeoForge instances.
- Updated the MCW LAN Agent to identify NeoForge, resolve NeoForm mappings, and try the NeoForge SRG target before safe fallback targets.
- Rebuilt and pinned the new SHA-256 for `runtime/mcw-lan-agent.jar`.
- Updated loader filters, UI labels, translations, and NeoForge diagnostics archive naming.
- Updated release metadata to `v0.12.0-beta.2` on the `beta` channel.

### Validation limitation

- Installer/profile/runtime behavior is covered by automated tests and official NeoForged metadata.
- The MCW LAN Agent Java smoke test completed successfully.
- The development environment did not provide DNS to the Python process, so a live installer run and live Minecraft launch were not performed for this build.
