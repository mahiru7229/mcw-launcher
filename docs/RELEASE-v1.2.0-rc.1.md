# MCW Launcher v1.2.0-rc.1

## Tiếng Việt

MCW Launcher **v1.2.0-rc.1** là release candidate đầu tiên của nhánh v1.2. Bản này **feature-freeze** toàn bộ tính năng đã được xác nhận trong Beta 1–3 và được dùng để kiểm thử bản Windows `.exe` trước khi lên v1.2.0 stable.

### Phạm vi RC.1

- Không thêm feature mới so với v1.2.0-beta.3.
- Giữ nguyên Instance Library organization: Favorite, Group, Tags, search/filter/sort.
- Giữ nguyên Unified Content Management: local import/drag-drop, ownership/pinned filters và managed-content protection.
- Giữ nguyên Version & Loader / Java Runtime UX của Instance Editor.
- Giữ nguyên dependency, modpack, manual recovery và modloader installation pipeline đã ổn định từ v1.1.2.
- Update channel vẫn là `beta` vì RC là prerelease; bản stable mới chuyển về `stable`.

### Windows EXE validation checklist

RC.1 được dành cho smoke test bản đóng gói bằng `mcw_launcher.spec`. Khi build `.exe`, nên kiểm tra tối thiểu:

1. Launcher mở không hiện console và không thiếu PySide6/certifi/win32crypt.
2. Language/theme bundled hoạt động khi chạy one-file EXE.
3. Microsoft login và account persistence hoạt động sau restart.
4. Tạo, clone, rename, delete và mở lại instance sau restart launcher.
5. Launch Vanilla, Forge legacy/modern, NeoForge, Fabric và Quilt trên các instance đã cài.
6. Test lại ATM9, SkyFactory 5 và RLCraft để kiểm tra dependency/JarJar/manual recovery regression.
7. Mở Instance Editor, đổi Auto/custom Java, scan/install runtime và repair loader.
8. Mở Installed Content Library trên modpack lớn, thử filter, drag/drop local content và managed-content protection.
9. Pause/cancel download và manual dependency pause → import → resume trong cùng launch session.
10. Thoát launcher trong lúc Minecraft chạy rồi mở lại để kiểm tra process/session recovery.

### Build

```powershell
python -m tools.release_preflight
.\build_release.ps1
```

Nếu chỉ muốn build `.exe` để smoke test local mà working tree chưa commit:

```powershell
.\build_release.ps1 -AllowDirty
```

### Validation

- Full regression suite: `1474 passed, 89 skipped`.
- Release preflight: passed.
- Language parity: `2047 / 2047`.
- Python compileall: passed.
- Hai warning còn lại là fixture ZIP duplicate có chủ đích trong security tests.

### Validation

- Full regression suite: `1474 passed, 89 skipped`.
- Release preflight: passed.
- Language parity: `2047 / 2047`.
- Python compileall: passed.
- The remaining two warnings are intentional duplicate-ZIP fixtures in security tests.

### Version

- Launcher runtime: `v1.2.0-rc.1`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0rc1`

---

## English

MCW Launcher **v1.2.0-rc.1** is the first release candidate for the v1.2 line. It **feature-freezes** the functionality validated in Beta 1–3 and is intended for Windows `.exe` testing before v1.2.0 stable.

### RC.1 scope

- No new feature is added compared with v1.2.0-beta.3.
- Keeps Instance Library organization: Favorite, Group, Tags, search/filter/sort.
- Keeps Unified Content Management: local import/drag-and-drop, ownership/pinned filters, and managed-content protection.
- Keeps the Instance Editor Version & Loader / Java Runtime UX.
- Keeps the stabilized dependency, modpack, manual-recovery, and modloader-installation pipelines from v1.1.2.
- The update channel remains `beta` because RC builds are prereleases; stable switches back to `stable`.

### Windows EXE validation checklist

RC.1 is intended for smoke-testing the package produced by `mcw_launcher.spec`. At minimum verify:

1. The launcher starts windowed without a console and without missing PySide6/certifi/win32crypt dependencies.
2. Bundled language/theme resources work from the one-file executable.
3. Microsoft login and account persistence survive launcher restart.
4. Instance create/clone/rename/delete and persistence after restart.
5. Vanilla, legacy/modern Forge, NeoForge, Fabric, and Quilt launch from installed instances.
6. ATM9, SkyFactory 5, and RLCraft still pass their real-world dependency/JarJar/manual-recovery flows.
7. Instance Editor Auto/custom Java, runtime scan/install, and loader repair work.
8. Installed Content Library remains responsive on large packs and local drag/drop respects managed-content protection.
9. Download pause/cancel and manual dependency pause → import → resume remain in the same launch session.
10. Process/session recovery works after closing and reopening the launcher while Minecraft is running.

### Build

```powershell
python -m tools.release_preflight
.\build_release.ps1
```

For a local smoke-test `.exe` before committing the working tree:

```powershell
.\build_release.ps1 -AllowDirty
```

### Version

- Launcher runtime: `v1.2.0-rc.1`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0rc1`
