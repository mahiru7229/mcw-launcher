# MCW Launcher v0.6.0 Beta 3

> Beta 3 focuses on Forge compatibility, transactional version switching, rollback, pre-launch validation, and diagnostics.

---

## Tiếng Việt

### Đổi phiên bản Forge an toàn

- Chuẩn bị phiên bản Forge mới trước khi thay đổi metadata instance.
- Tải và kiểm tra các library bắt buộc của phiên bản đích.
- Chỉ cập nhật instance sau khi toàn bộ bước chuẩn bị thành công.
- Nếu cài đặt hoặc kiểm tra thất bại, instance tiếp tục dùng loader hiện tại.
- Ghi lại một restore point để có thể **Khôi phục loader trước đó**.
- Khi khôi phục thành công, restore point được đảo chiều để có thể quay lại bản vừa dùng.
- Không thay đổi `mods/`, `config/`, `saves/`, `resourcepacks/`, screenshots hoặc settings.

### Kiểm tra trước khi Launch

Forge instance được kiểm tra trước khi Minecraft chạy:

- Forge profile và runtime metadata;
- mod sai loader;
- mod ID trùng;
- dependency bắt buộc bị thiếu hoặc đang disable;
- dependency sai phiên bản;
- version range của Forge/Minecraft;
- library bắt buộc còn thiếu hoặc sai hash sau khi downloader hoàn tất.

Lỗi mức `ERROR` chặn Launch. Cảnh báo mức `WARNING` vẫn cho Launch và xuất hiện trong danh sách cảnh báo.

### Forge Diagnostics

Thêm các thao tác:

```text
Restore previous loader
Open Forge logs
Export Forge diagnostics
```

Gói diagnostics ZIP có thể chứa:

- Forge profile;
- log cài đặt, repair và đổi loader;
- `instance.json` và `settings.json` đã che dữ liệu nhạy cảm;
- danh sách mod và metadata;
- kết quả pre-launch check;
- `latest.log` được giới hạn dung lượng và che token.

Gói không chứa account database, access/refresh token, password, world/save hoặc nội dung mod JAR.

### Cải thiện Full Instance Repair

Full Repair giờ repair cả Forge loader, thay vì chỉ kiểm tra Vanilla client và libraries của instance Forge.

### Version

```python
VERSION = "v0.6.0 Beta 3"
VERSION_ID = "0.6.0-beta.3"
UPDATE_CHANNEL = "beta"
```

---

## English

### Transactional Forge version switching

- Prepare the target Forge version before changing instance metadata.
- Download and verify the target runtime libraries.
- Commit the loader change only after validation succeeds.
- Keep the current loader when installation or verification fails.
- Record a one-step restore point for **Restore previous loader**.
- Reverse the restore point after a successful restore, allowing a one-step undo.
- Preserve mods, configuration, saves, resource packs, screenshots, and instance settings.

### Forge pre-launch validation

Forge instances are checked for:

- invalid Forge profile/runtime metadata;
- loader-mismatched mods;
- duplicate enabled mod IDs;
- missing or disabled required dependencies;
- incompatible dependency versions;
- Forge and Minecraft version ranges;
- required libraries still missing or invalid after download.

Errors block Launch. Warnings remain non-blocking and are returned with normal launch warnings.

### Forge diagnostics

New actions:

```text
Restore previous loader
Open Forge logs
Export Forge diagnostics
```

The diagnostics ZIP may include sanitized instance metadata/settings, Forge profiles and logs, mod metadata, pre-launch results, and size-limited Minecraft logs. It excludes account databases, credentials, worlds/saves, and mod JAR contents.

### Full instance repair

Full Repair now repairs Forge loader installations instead of falling back to a Vanilla-only verification path.

---

## GitHub Release

```text
Tag: v0.6.0-beta.3
Title: MCW Launcher v0.6.0 Beta 3
Pre-release: enabled
```

Upload only:

```text
MCW-Launcher-v0.6.0-beta.3-windows-x64.zip
MCW-Launcher-v0.6.0-beta.3-windows-x64.zip.sha256
```
