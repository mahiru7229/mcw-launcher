# MCW Launcher v1.2.0-beta.3

## Tiếng Việt

MCW Launcher **v1.2.0-beta.3** tiếp tục Instance Manager 2.0 với trọng tâm **Component/Runtime UX**. Beta này đưa thông tin Minecraft, mod loader và Java requirement vào cùng Instance Editor, đồng thời cho phép chọn Java runtime theo từng instance mà không phá ranh giới Core/GUI.

### Instance components

- Version & Loader hiển thị riêng Minecraft, mod loader/version và Java requirement thay vì chỉ có một chuỗi summary.
- Nút **Manage Loader Version** mở workflow loader hiện có; **Repair Mod Loader** được đưa trực tiếp vào Instance Editor.
- Minecraft version trong Beta 3 vẫn là read-only. Việc đổi game version trực tiếp được hoãn để tránh làm hỏng curated modpack hoặc instance có mods không tương thích.

### Java runtime per instance

- Thêm trang **Java Runtime** trong Instance Editor.
- Hiển thị Java major mà Minecraft yêu cầu và managed-Java target của MCW.
- Cho phép chọn **Automatic (recommended)** hoặc một Java runtime tương thích đã scan được.
- Có thể scan runtime và cài managed Java phù hợp ngay trong Instance Editor.
- Custom Java được validate tại Core: file phải tồn tại, xác định được major version và thỏa Java requirement của Minecraft.
- Không cho đổi Java runtime khi Minecraft của instance đang chạy.

### Core API

- Thêm public `InstanceRuntimeProfile`.
- `InstanceService.runtime_profile()` cung cấp runtime/component metadata cho GUI/CLI mà không buộc frontend đọc internal files.
- `InstanceService.set_java_runtime()` lưu Auto/custom runtime qua SettingsManager và thực hiện compatibility validation ở Core.

### Scope

Beta này không thêm mod/modpack update, rollback, Crash Center hay thay đổi dependency/loader install pipeline đã ổn định.

### Version

- Launcher runtime: `v1.2.0-beta.3`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0b3`

---

## English

MCW Launcher **v1.2.0-beta.3** continues Instance Manager 2.0 with a **Component/Runtime UX** pass. Minecraft, loader, and Java requirements are now visible together in the Instance Editor, while per-instance Java selection is exposed through the public Core API.

### Instance components

- Version & Loader now shows Minecraft, loader/version, and Java requirement as separate components.
- **Manage Loader Version** opens the existing loader workflow and **Repair Mod Loader** is available directly in the Instance Editor.
- Minecraft version remains read-only in Beta 3 to avoid unsafe changes to curated modpacks or incompatible mod sets.

### Java runtime per instance

- New **Java Runtime** page in the Instance Editor.
- Shows the Minecraft-required Java major and MCW managed-runtime target.
- Select **Automatic (recommended)** or a compatible scanned Java runtime.
- Scan Java installations or install the compatible managed Java without leaving the Instance Editor.
- Custom Java selection is validated in Core for path, detectable major version, and Minecraft compatibility.
- Runtime changes are blocked while the instance is running.

### Core API

- Adds public `InstanceRuntimeProfile`.
- `InstanceService.runtime_profile()` exposes component/runtime metadata without frontend access to internal files.
- `InstanceService.set_java_runtime()` persists Auto/custom selection through SettingsManager with Core-side compatibility validation.

### Scope

This beta does not add mod/modpack update, rollback, Crash Center, or modify the stabilized dependency/loader installation pipelines.

### Version

- Launcher runtime: `v1.2.0-beta.3`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0b3`
