# MCW Launcher v1.1.1-beta.5 — Final dependency and Forge cache hotfix v4

## Tiếng Việt

Đây là hotfix **tích lũy** cho MCW Launcher `v1.1.1-beta.5`. Bản vá bao gồm toàn bộ sửa lỗi dependency từ v1–v3 và bổ sung hai sửa lỗi cuối.

### 1. Dependency đã được mod khác tích hợp

- Launcher nhận diện các mod ID mà một JAR khác cung cấp qua metadata Forge/NeoForge/Fabric/Quilt và Forge JarJar.
- Resolver không tải thêm dependency standalone nếu instance đã cung cấp cùng mod ID.
- Áp dụng tổng quát cho Modrinth và CurseForge bằng identity project chính xác, không hardcode riêng `flywheel`.
- Nếu launcher từng tự thêm một dependency standalone với `selectionReason: required_dependency`, nhưng một JAR khác đã cung cấp cùng mod ID, file standalone dư thừa được dọn khỏi thư mục `mods` và các registry liên quan.
- File do tác giả modpack ghim bằng `selectionReason: pack_manifest` không bị tự xóa.

Trường hợp đã xác nhận:

```text
Create provides flywheel 0.6.10-20
+ flywheel-forge-1.19.2-0.6.8.a.jar was auto-added
→ remove the old standalone Flywheel file
→ keep Create's integrated Flywheel
```

### 2. Không chạy lại Forge installer khi cache đã tồn tại

- Forge profile cache hợp lệ được dùng lại ngay.
- Cache cũ thiếu metadata download/native được chuẩn hóa tại chỗ từ profile và thư viện hiện có.
- Không chạy lại Forge installer chỉ vì metadata cache cần bổ sung.
- Cache được tạo mới sẽ được normalize hoàn chỉnh trước khi lưu, tránh lặp lại ở lần launch kế tiếp.
- Installer chỉ chạy khi không còn profile cache có cấu trúc hợp lệ hoặc khi người dùng chủ động Repair/force refresh.

### Áp dụng

1. Đóng MCW Launcher.
2. Giải nén ZIP vào thư mục root của source `v1.1.1-beta.5`.
3. Cho phép ghi đè file.
4. Mở launcher và launch lại instance.

Không cần cài lại modpack. Với file Flywheel cũ do resolver tự thêm, launcher sẽ dọn ở lần dependency preflight tiếp theo.

### Xác thực

```text
1391 passed
88 skipped
2 expected warnings
compileall passed
```

Hai warning đến từ fixture ZIP bảo mật cố ý chứa entry trùng.

---

## English

This is a **cumulative** hotfix for MCW Launcher `v1.1.1-beta.5`. It includes dependency fixes v1–v3 and the final two corrections.

### Embedded dependency providers

- Installed JARs can satisfy dependency mod IDs through Forge/NeoForge/Fabric/Quilt metadata and Forge JarJar.
- Modrinth and CurseForge resolution skips a standalone dependency when the same mod ID is already provided by another installed JAR.
- Previously auto-added standalone files are removed only when provenance marks them as `selectionReason: required_dependency`.
- Pack-author-pinned files using `selectionReason: pack_manifest` are never automatically removed.

### Forge cache reuse

- Existing Forge profiles are reused without rerunning the installer.
- Older caches with incomplete library/native download metadata are refreshed in place.
- Newly installed profiles are fully normalized before being cached.
- The installer remains reserved for missing/invalid profiles and explicit repair or force-refresh operations.

### Validation

```text
1391 passed
88 skipped
2 expected warnings
compileall passed
```
