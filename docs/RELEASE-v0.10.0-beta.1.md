# MCW Launcher v0.10.0 Beta 1

> Opt-in test build for installing Fabric mods from CurseForge. `v0.9.0` remains the default Stable release.

---

## Tiếng Việt

### Nội dung chính

- Catalog Mods hỗ trợ chọn **CurseForge + Fabric**, tìm project, chọn file và cài vào instance Fabric tương thích.
- Có thể chọn instance sẵn có hoặc tạo instance Fabric mới trước khi cài.
- Dependency bắt buộc được giải quyết theo Minecraft version, loader ưu tiên và các kênh Release/Beta/Alpha đã bật.
- Metadata CurseForge đi qua public gateway; API key không được nhúng trong launcher.
- File JAR tải trực tiếp qua Download Engine, có progress, retry, resume, giới hạn mạng và xác minh SHA-1/size.

### An toàn khi cài

- Loader do CurseForge khai báo chỉ là dữ liệu gợi ý vì một số JAR universal bị gắn nhãn chưa đầy đủ.
- Launcher tải và đọc metadata thật (`fabric.mod.json` hoặc metadata Forge) trước khi sửa instance.
- Quyền chấp nhận một file chưa xác minh chỉ áp dụng cho file người dùng đã chọn, không tự động áp dụng cho dependency.
- Tất cả file tự động được chuẩn bị trước; mod và registry được áp dụng theo transaction.
- Nếu ghi file hoặc registry thất bại, launcher khôi phục các mod bị thay thế và registry cũ.
- Khi không có URL phân phối công khai, luồng tải thủ công tiếp tục yêu cầu đúng phần mở rộng, size và SHA-1.

### Phiên bản

```text
VERSION = v0.10.0 Beta 1
VERSION_ID = 0.10.0-beta.1
UPDATE_CHANNEL = beta
```

### Checklist cho tester

1. Bật tester program; xác nhận Stable vẫn là kênh mặc định khi tắt tùy chọn.
2. Thử một mod Fabric không có dependency.
3. Thử một mod Fabric cần Fabric API hoặc dependency bắt buộc khác.
4. Thử đổi Release/Beta/Alpha và chọn Minecraft version khác.
5. Thử file bị hạn chế phân phối và kiểm tra luồng nhập thủ công.
6. Backup instance/world quan trọng trước khi thử Beta.

Chạy regression:

```powershell
python -m pytest test -q
python -m tools.release_preflight
```

Kết quả source Beta 1: `1026 passed`, `0 failed`, `0 errors`.

---

## English

### Highlights

- The Mods catalog supports **CurseForge + Fabric** project search, exact file selection, and installation into a compatible Fabric instance.
- Users may select an existing instance or create a new Fabric instance before installation.
- Required dependencies are resolved using the Minecraft version, preferred loader, and enabled Release/Beta/Alpha channels.
- CurseForge metadata uses the public gateway; no API key is bundled in the launcher.
- JAR files download directly through the Download Engine with progress, retry, resume, shared network limits, and SHA-1/size verification.

### Installation safety

- CurseForge loader labels are advisory because some universal JARs have incomplete labels.
- The launcher downloads and inspects real JAR metadata (`fabric.mod.json` or Forge metadata) before changing the instance.
- Approval for an unverified selected file is scoped to that root file and is not inherited by dependencies.
- Every automatic file is prepared first, then mods and registry state are applied transactionally.
- A file or registry write failure restores replaced mods and the previous registry.
- Restricted-distribution files keep the manual import flow with extension, size, and SHA-1 verification.

### Version

```text
VERSION = v0.10.0 Beta 1
VERSION_ID = 0.10.0-beta.1
UPDATE_CHANNEL = beta
```

### Tester checklist

1. Join the tester program and confirm Stable remains the default after opting out.
2. Test a Fabric mod without dependencies.
3. Test a Fabric mod requiring Fabric API or another required dependency.
4. Test Release/Beta/Alpha choices and a different Minecraft version.
5. Test a restricted-distribution file and the verified manual import flow.
6. Back up important instances and worlds before testing the Beta.

Regression commands:

```powershell
python -m pytest test -q
python -m tools.release_preflight
```

Beta 1 source result: `1026 passed`, `0 failed`, `0 errors`.
