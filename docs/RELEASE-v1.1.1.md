# MCW Launcher v1.1.1

## Tiếng Việt

MCW Launcher **v1.1.1** là bản stable tập trung vào độ tin cậy của modpack, dependency resolver và khả năng tương thích Forge legacy. Bản phát hành này tổng hợp toàn bộ thay đổi của nhánh Beta 1–6 cùng các hotfix cuối được xác nhận khi thử nghiệm modpack thực tế.

### Dependency resolver và modpack

- Hoàn thiện dependency bắt buộc cho modpack Modrinth, CurseForge và ATLauncher trước khi tạo process Minecraft.
- Giữ nguyên file/version được tác giả modpack ghim; dependency bổ sung được theo dõi bằng `requiredBy` và `selectionReason`.
- Giải quyết dependency nhiều tầng bằng vòng hoàn thiện có giới hạn: audit, resolve, tải tự động hoặc manual, rồi audit lại cho tới khi hội tụ.
- Tách trạng thái file khỏi trạng thái dependency: file tồn tại và khớp size/hash không còn bị tải lại chỉ vì parser không đọc được mod ID.
- Provider bridge có thể khôi phục dependency từ metadata của provider khác khi cùng file được xác minh bằng hash.
- Optional hoặc embedded dependency không bị tự động cài như dependency bắt buộc.

### Forge JarJar và identity đáng tin cậy

- Đọc `META-INF/jarjar/metadata.json` và nested JAR để nhận các mod ID được JAR cha cung cấp.
- Không yêu cầu standalone Flywheel khi bản Create tương ứng đã cung cấp dependency nội bộ.
- CurseForge pack registry lưu `projectName`, `projectSlug` và `expectedModIds`.
- File do modpack quản lý, đúng path/size/SHA-1 có thể cung cấp identity provider cho dependency audit khi parser Forge legacy không đọc được metadata tầng ngoài.
- Identity provider không ghi đè một mod ID thật đã được parser xác định; file sai hash, không thuộc registry hoặc không có identity đáng tin cậy vẫn bị từ chối.

### Forge legacy

- Quét cả `mods/*.jar` và đúng một thư mục legacy `mods/<minecraft-version>/*.jar` cho Forge/NeoForge.
- Hỗ trợ `mcmod.info` chứa nhiều mod entry và đưa các ID phụ vào `provided_mods`.
- Sửa dependency pack-pinned trong các pack Forge cũ như RLCraft.
- Không chạy lại Forge installer khi profile/cache hiện tại vẫn dùng được; metadata cache bị ô nhiễm có thể được sửa tại chỗ.
- Sửa phân loại native legacy để không coi `jna-platform` là native chỉ vì tên artifact kết thúc bằng `-platform`.
- Sửa so sánh Maven/Forge range có dotted letter qualifier: `0.6.10` khớp `[0.6.8.a,0.7)`.

### ATLauncher và OptiFine

- Thêm browser và installer ATLauncher với metadata/manifest fallback, file tùy chọn, retry giới hạn, checksum và Configs.zip staging an toàn.
- OptiFine dùng luồng nhập JAR gốc trực tiếp; launcher nhận diện version/build, kiểm tra file và cài theo ngữ cảnh Vanilla hoặc Forge.

### Manual download và repair

- File CurseForge yêu cầu tải thủ công được ghi nhận bền vững sau import.
- Manual file đã xác minh không bị đưa lại vào download queue ở lần launch sau.
- Repair và launch dùng cùng dependency completion flow.
- Dependency thật sự thiếu vẫn được tự tải hoặc mở bảng manual; chỉ báo thiếu sau khi resolver không còn tiến triển.

### Xác thực thực tế

- SkyFactory 3 — Forge 1.10.2: launch thành công.
- RLCraft — Forge 1.12.2: dependency legacy/manual và launch thành công.
- Kết quả pytest và kiểm tra package được ghi trong `TEST-RESULTS.txt` của gói phát hành.

### Metadata phát hành

- Launcher runtime: `v1.1.1`
- Update channel: `stable`
- Python distribution: `mcw-core 1.1.1`
- Public MCW Core contracts hiện có không bị cố ý xóa hoặc đổi tên.

### Giới hạn đã biết

Một số JAR hoặc project hiện đại có metadata cho nhiều loader hoặc nested component. Trong một số modpack NeoForge rất lớn, dependency từ metadata Fabric có thể bị nâng nhầm thành top-level dependency. Việc sửa loader-scoped dependency parsing đã được chuyển sang **v1.1.2-beta.1** để tránh đưa thay đổi kiến trúc mới vào bản stable này.

---

## English

MCW Launcher **v1.1.1** is a stable release focused on modpack reliability, dependency resolution, and legacy Forge compatibility. It consolidates the complete Beta 1–6 branch and the final hotfixes validated against real modpacks.

### Dependency resolver and modpacks

- Completes required dependency resolution for Modrinth, CurseForge, and ATLauncher modpacks before Minecraft is spawned.
- Preserves files and versions pinned by pack authors; added dependencies retain `requiredBy` and `selectionReason` provenance.
- Resolves transitive dependencies through a bounded convergence loop: audit, resolve, automatic/manual download, then re-audit until no further progress is possible.
- Separates file completeness from dependency identity, so a size/hash-valid file is not downloaded again only because a parser cannot read its mod ID.
- Uses a hash-verified cross-provider bridge when the same dependency artifact is available from another provider.
- Optional and embedded relations are not promoted to required standalone downloads.

### Forge JarJar and trusted identities

- Reads `META-INF/jarjar/metadata.json` and nested JARs to discover mod IDs supplied by a parent artifact.
- Does not require standalone Flywheel when the matching Create artifact already provides it internally.
- Persists `projectName`, `projectSlug`, and `expectedModIds` in the CurseForge pack registry.
- A pack-managed file with a verified path, size, and SHA-1 may supply its trusted provider identity when a legacy Forge parser cannot read outer metadata.
- Provider identities never overwrite a real parsed mod ID; wrong-hash, unregistered, or untrusted files remain rejected.

### Legacy Forge

- Scans both `mods/*.jar` and exactly one valid legacy directory, `mods/<minecraft-version>/*.jar`, for Forge/NeoForge instances.
- Supports multi-entry `mcmod.info` and exposes secondary IDs through `provided_mods`.
- Repairs pack-pinned dependencies in old Forge packs such as RLCraft.
- Reuses a valid Forge profile/cache instead of rerunning the installer; polluted cache metadata can be repaired in place.
- Avoids treating `jna-platform` as a native artifact merely because its name ends in `-platform`.
- Supports Maven/Forge version ranges with dotted letter qualifiers, so `0.6.10` matches `[0.6.8.a,0.7)`.

### ATLauncher and OptiFine

- Adds the ATLauncher browser and installer with metadata/manifest fallbacks, optional files, bounded retry, checksum validation, and safe Configs.zip staging.
- OptiFine uses a direct original-JAR import flow with version/build detection and context-aware Vanilla or Forge installation.

### Manual download and repair

- CurseForge manual-download imports are persisted across launcher restarts.
- A verified manual file is not returned to the download queue on the next launch.
- Repair and launch share the same dependency-completion flow.
- Truly missing dependencies still trigger automatic or manual download; a blocking missing error is raised only after the resolver can no longer make progress.

### Real-world validation

- SkyFactory 3 — Forge 1.10.2: launched successfully.
- RLCraft — Forge 1.12.2: legacy/manual dependencies and launch validated successfully.
- Pytest and package validation results are recorded in the release `TEST-RESULTS.txt`.

### Release metadata

- Launcher runtime: `v1.1.1`
- Update channel: `stable`
- Python distribution: `mcw-core 1.1.1`
- Existing public MCW Core contracts are not intentionally removed or renamed.

### Known limitation

Some modern projects or artifacts contain metadata for multiple loaders or nested components. In very large NeoForge modpacks, Fabric-side metadata may still be incorrectly promoted to top-level dependencies. Loader-scoped dependency parsing is scheduled for **v1.1.2-beta.1** rather than introducing that architectural change into this stable release.
