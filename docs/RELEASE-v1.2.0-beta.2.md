# MCW Launcher v1.2.0-beta.2

## Tiếng Việt

MCW Launcher **v1.2.0-beta.2** tiếp tục nhánh feature v1.2 với trọng tâm **Unified Content Management** cho mod, resource pack và shader pack. Beta này mở rộng thư viện nội dung đã cài mà không thay đổi dependency resolver, modpack lifecycle hoặc loader pipeline ổn định từ v1.1.2.

### Unified local content import

- Thư viện nội dung có nút **Add local files** để thêm trực tiếp `.jar` và `.zip` vào instance đang chọn.
- Hỗ trợ kéo-thả nhiều file vào thư viện; khi đang ở `All types`, launcher tự nhận diện mod, resource pack hoặc shader pack.
- `.jar` được xử lý bằng `ModManager`; `.zip` phải vượt qua validation hiện có của resource/shader pack trước khi commit.
- Local mod import xóa tracking Modrinth/CurseForge cũ theo filename để file thay thế không tiếp tục bị hiển thị như artifact của provider trước đó.
- Public `InstalledContentLibraryManager` có API local import dùng chung để GUI không phải tự triển khai business logic.

### Content library UX

- Thêm filter **User-added / Modpack-managed** và **Pinned only** để quản lý instance lớn dễ hơn.
- Hiển thị số item đang thấy so với tổng số item sau khi search/filter.
- Có thể mở manager hoặc thư mục theo content type đang filter ngay cả khi type đó chưa có item nào.
- Bổ sung ATLauncher vào provider filter.
- Bổ sung project URL cho mod/modpack CurseForge khi registry chỉ còn project ID, giúp **Open on web** hoạt động ổn định hơn.

### Safety and compatibility

- Managed modpack files vẫn được bảo vệ khỏi thao tác remove trong unified library.
- Local import dùng các validator và instance run-lock hiện có; beta này không tạo đường ghi file riêng bypass core policy.
- Không thêm mod/modpack update, snapshot/rollback hoặc Crash Center trong beta này.

### Release metadata

- Launcher runtime: `v1.2.0-beta.2`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0b2`

---

## English

MCW Launcher **v1.2.0-beta.2** continues the v1.2 feature line with **Unified Content Management** improvements for mods, resource packs, and shader packs. This beta expands the installed-content workflow without changing the dependency resolver, modpack lifecycle, or loader pipelines stabilized in v1.1.2.

### Unified local content import

- The Installed Content Library now has an **Add local files** action for adding `.jar` and `.zip` files directly to the selected instance.
- Multiple files can be drag-dropped into the library; in `All types`, the launcher detects mods, resource packs, and shader packs automatically.
- `.jar` files go through `ModManager`; `.zip` files must pass the existing resource/shader archive validation before being committed.
- Local mod imports clear stale Modrinth/CurseForge filename tracking so replacement files are not still presented as artifacts from the previous provider.
- The public `InstalledContentLibraryManager` exposes the shared local-import API, keeping business logic out of the GUI.

### Content library UX

- Adds **User-added / Modpack-managed** ownership filtering and a **Pinned only** view for large instances.
- Shows the number of visible items after search/filtering relative to the full library.
- Managers and content folders can be opened from the selected type filter even when that content type currently has no rows.
- Adds ATLauncher to the provider filter.
- Adds fallback CurseForge project URLs for mod and modpack entries when only a project ID is available, improving **Open on web** behavior.

### Safety and compatibility

- Modpack-managed files remain protected from removal through the unified library.
- Local import reuses existing validators and instance run locks; no GUI-only file-write path bypasses core policy.
- Mod/modpack updates, snapshot/rollback, and Crash Center remain outside this beta's scope.

### Release metadata

- Launcher runtime: `v1.2.0-beta.2`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0b2`
