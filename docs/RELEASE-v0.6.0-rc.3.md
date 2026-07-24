# MCW Launcher v0.6.0 RC 3

> RC3 is the final visual-compatibility candidate for the 0.6 line. It keeps the RC2 stability fixes and forces a consistent dark appearance across the launcher and all Qt dialogs.

---

## Tiếng Việt

### Giao diện tối bắt buộc

- Launcher luôn sử dụng dark theme, không phụ thuộc Light/Dark mode của Windows.
- Toàn bộ chữ trong launcher, dialog, menu, input, button, tooltip và trạng thái disabled được ép thành màu trắng.
- Qt sử dụng Fusion style để giảm khác biệt giao diện giữa các máy Windows.
- Native Qt dialogs bị tắt để file dialog và các hộp thoại khác tiếp tục nhận dark palette của launcher.
- QMessageBox được áp palette và stylesheet trực tiếp, tránh lỗi nền trắng/chữ trắng hoặc theme hệ điều hành ghi đè một phần.
- Splash screen, detailed text, placeholder và progress text đều giữ nền tối/chữ trắng.

### Giữ lại các bản sửa từ RC2

- Sửa cảnh báo giả **“Select an instance first.”** sau khi cài mod thành công.
- Mod Manager được gắn đúng instance đích trước khi cài và chỉ refresh sau khi task hoàn tất.
- Startup worker, timeout theo stage và `logs/startup-error.log` tiếp tục được giữ nguyên.
- Splash screen không che dialog lỗi startup.

### Phiên bản

```text
VERSION = v0.6.0 RC 3
VERSION_ID = 0.6.0-rc.3
UPDATE_CHANNEL = beta
```

### Kiểm thử

```text
750 passed
46 skipped
0 failed
0 errors
```

Các test bị skip là nhóm GUI/PySide6 không khả dụng trong môi trường regression.

---

## English

### Forced dark appearance

- The launcher always uses a dark appearance, independent of the Windows Light/Dark setting.
- Text across the launcher, dialogs, menus, inputs, buttons, tooltips and disabled states is forced to white.
- Qt uses Fusion style to reduce visual differences across Windows systems.
- Native Qt dialogs are disabled so file dialogs and other dialogs inherit the launcher dark palette.
- QMessageBox receives a direct palette and stylesheet to prevent white-background/white-text failures or partial OS-theme overrides.
- The startup splash, detailed text, placeholders and progress text retain a dark background with white text.

### RC2 fixes retained

- Keeps the fix for the false **“Select an instance first.”** warning after successful mod installation.
- Mod Manager is bound to the correct target instance before installation and refreshes only after the task completes.
- Keeps the startup worker, stage timeout and `logs/startup-error.log` reporting.
- The splash screen no longer hides startup error dialogs.

### Version

```text
VERSION = v0.6.0 RC 3
VERSION_ID = 0.6.0-rc.3
UPDATE_CHANNEL = beta
```

### Tests

```text
750 passed
46 skipped
0 failed
0 errors
```

Skipped tests are GUI/PySide6-dependent tests unavailable in the regression environment.
