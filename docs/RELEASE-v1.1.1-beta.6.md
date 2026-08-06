# MCW Launcher v1.1.1-beta.6

## Tiếng Việt

MCW Launcher **v1.1.1-beta.6** sửa lỗi dependency cuối được phát hiện khi cài và launch các modpack Forge legacy như **RLCraft 2.9.3**. Một dependency có thể đã được chính manifest của pack ghim, nhưng bước audit cuối vẫn kết luận thiếu mod ID và chặn launch.

### Legacy Forge mod discovery

- `ModManager` tiếp tục quét `mods/*.jar` như trước.
- Với Forge và NeoForge, scanner còn quét đúng một thư mục legacy khớp Minecraft version: `mods/<minecraft-version>/*.jar`.
- Không quét đệ quy toàn bộ cây thư mục, tránh nhận nhầm cache, backup hoặc JAR không thuộc runtime.
- Enable, disable và remove mod được phép hoạt động an toàn trong cả thư mục `mods/` và thư mục version hợp lệ.
- Legacy `mcmod.info` có nhiều mod entry giữ entry đầu làm mod chính và ghi các entry còn lại vào `provided_mods`.

### Reconcile dependency do modpack ghim

Khi audit báo thiếu dependency, resolver thực hiện thứ tự mới:

1. Kiểm tra mod ID đã được một JAR hiện có cung cấp hay chưa.
2. Tìm file mà manifest CurseForge của chính modpack đã ghim bằng project identity.
3. Giữ nguyên `projectId`, `fileId`, path và version của pack.
4. Nếu file local bị thiếu hoặc không cung cấp đúng mod ID, đưa file đó trở lại hàng đợi download/repair.
5. Chỉ dùng cross-provider bridge khi pack thật sự không chứa dependency cần thiết.

Launcher không tìm theo tên gần giống và không tự thay file pack bằng bản mới nhất.

### Xác minh identity sau download

- CurseForge pack registry nâng lên schema **4**.
- Registry lưu `projectName`, `projectSlug` và `expectedModIds` với normalize tương thích dữ liệu cũ.
- File JAR có `expectedModIds` phải thật sự khai mod ID tương ứng trong metadata chính hoặc dependency JarJar được cung cấp.
- File có hash đúng nhưng identity sai không còn được xem là hoàn tất.
- Metadata project được cache trong registry; mạng chỉ cần dùng để bổ sung identity còn thiếu.

### Trường hợp RLCraft

`CompatSkills` yêu cầu mod ID `reskillable`. Nếu `Reskillable-1.12.2-1.13.0.jar` nằm trong thư mục legacy hoặc file pack-pinned bị mất, Beta 6 sẽ nhận diện hoặc repair đúng file Reskillable mà RLCraft đã chọn, thay vì báo `RequiredModDependenciesMissing` ngay lập tức.

### Phiên bản và xác thực

- Launcher runtime: `v1.1.1-beta.6`
- Python distribution metadata: `1.1.1b6`
- CurseForge pack registry schema: `4`
- Toàn bộ test: **1398 passed, 88 skipped, 2 warnings**.
- `compileall` đạt cho `src`, `mcw_core` và `test`.

Hai warning đến từ fixture ZIP cố tình chứa entry trùng trong kiểm thử bảo mật, không liên quan tới dependency resolver.

---

## English

MCW Launcher **v1.1.1-beta.6** fixes the final dependency issue found while installing and launching legacy Forge modpacks such as **RLCraft 2.9.3**. A dependency could already be pinned by the pack manifest while the final audit still failed to discover its mod ID and blocked launch.

### Legacy Forge mod discovery

- `ModManager` continues to scan `mods/*.jar`.
- For Forge and NeoForge, it also scans exactly one legacy directory matching the Minecraft version: `mods/<minecraft-version>/*.jar`.
- The launcher does not recursively scan the entire directory tree, avoiding caches, backups, and unrelated JARs.
- Enable, disable, and remove operations safely support both the main mods directory and the valid version directory.
- Legacy `mcmod.info` files containing multiple mod entries keep the first entry as the primary mod and expose the remaining entries through `provided_mods`.

### Pack-pinned dependency reconciliation

When the audit reports a missing dependency, the resolver now follows this order:

1. Check whether an installed JAR already provides the requested mod ID.
2. Find the file pinned by the modpack's own CurseForge manifest using project identity.
3. Preserve the pack's `projectId`, `fileId`, path, and version.
4. If the local file is missing or does not provide the expected mod ID, return that exact pinned file to the download/repair queue.
5. Use the cross-provider bridge only when the pack truly does not contain the dependency.

The launcher does not use fuzzy name matching and does not silently replace a pack file with the latest version.

### Post-download identity validation

- The CurseForge pack registry is upgraded to schema **4**.
- The registry persists `projectName`, `projectSlug`, and `expectedModIds` with backward-compatible normalization.
- A JAR with `expectedModIds` must actually declare the requested identity in its primary metadata or supplied JarJar dependencies.
- A file with a valid hash but the wrong mod identity is no longer considered complete.
- Project metadata is cached in the registry; network access is only needed to fill missing identities.

### RLCraft scenario

`CompatSkills` requires the `reskillable` mod ID. If `Reskillable-1.12.2-1.13.0.jar` is stored in the legacy version directory or the pack-pinned local file is missing, Beta 6 discovers or repairs the exact Reskillable file selected by RLCraft instead of immediately raising `RequiredModDependenciesMissing`.

### Versions and validation

- Launcher runtime: `v1.1.1-beta.6`
- Python distribution metadata: `1.1.1b6`
- CurseForge pack registry schema: `4`
- Full test suite: **1398 passed, 88 skipped, 2 warnings**.
- `compileall` passes for `src`, `mcw_core`, and `test`.

The two warnings come from security-test ZIP fixtures that intentionally contain duplicate entries; they are unrelated to dependency resolution.
