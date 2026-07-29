# MCW Launcher v0.11.0-alpha.3

## Tiếng Việt

### Startup compatibility hotfix

Bản Alpha 3 sửa lỗi launcher không thể mở giao diện sau khi nâng từ Alpha 2:

```text
AttributeError: type object 'SettingsManager' has no attribute 'default_dict'
```

Thay đổi chính:

- Thêm API `default_instance_settings()` ổn định cho dữ liệu cài đặt instance mặc định.
- Khôi phục `SettingsManager.default_dict()` dưới dạng API tương thích ngược.
- Launcher Settings, GUI settings controller và LauncherSettingsManager không còn phụ thuộc trực tiếp vào class method cũ.
- Mỗi lần lấy defaults đều trả về bản sao độc lập, tránh sửa nhầm cấu hình mặc định dùng chung.
- Giữ nguyên Theme Animation Engine và Theme Custom Font từ Alpha 1/Alpha 2.

## English

### Startup compatibility hotfix

Alpha 3 fixes a startup crash that could occur after applying Alpha 2:

```text
AttributeError: type object 'SettingsManager' has no attribute 'default_dict'
```

Main changes:

- Adds a stable `default_instance_settings()` API.
- Restores `SettingsManager.default_dict()` as a backward-compatible API.
- Removes direct dependency on the legacy class factory from launcher settings UI and controllers.
- Returns an independent copy for every defaults request.
- Keeps all Theme Animation Engine and Theme Custom Font features.

## Release metadata

- Version: `v0.11.0-alpha.3`
- Version ID: `0.11.0-alpha.3`
- Update channel: `beta`
