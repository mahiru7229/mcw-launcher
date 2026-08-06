# MCW Launcher v1.1.1-beta.5

## Tiếng Việt

MCW Launcher **v1.1.1-beta.5** sửa một lỗi nghiêm trọng trong pipeline modpack: file của pack có thể được tải đầy đủ theo manifest nhưng các dependency bắt buộc do từng mod khai báo với Modrinth hoặc CurseForge lại không được bổ sung, khiến Minecraft được tạo process cùng nhiều cảnh báo và thường crash ngay sau đó.

### Dependency resolver cho modpack

- Thêm `ModpackDependencyResolver` dùng chung cho modpack Modrinth và CurseForge.
- Resolver duyệt đệ quy dependency loại **required** với giới hạn 20 tầng và tối đa 256 file bổ sung.
- Dependency đã nằm trong manifest hoặc đã được chọn trước đó không bị tải lại.
- Phát hiện vòng lặp bằng provider version/file identity.
- Metadata provider được retry tối đa ba lần đối với lỗi mạng có khả năng phục hồi.
- Modrinth có thể nhận diện file từ `versionId`, URL CDN hoặc SHA-512/SHA-1 lookup.
- CurseForge lưu dependency metadata của file vào registry để các lần launch/repair sau không phải truy vấn lại không cần thiết.

### Manifest của modpack vẫn là nguồn sự thật

- MCW không tự thay file mà tác giả modpack đã ghim.
- Nếu một dependency yêu cầu version khác nhưng pack đã chọn sẵn một version của cùng project, MCW giữ file của pack và ghi warning giải thích.
- Lỗi system requirement của file được pack ghim, ví dụ JEI khai báo Minecraft `[1.21, 1.21.1)` trong pack Minecraft `1.21.1`, được giữ ở mức warning thay vì tự động đổi JEI sang build khác.
- Optional, embedded và incompatible relations không bị coi nhầm là dependency bắt buộc cần tự tải.

### Không còn bỏ qua dependency bắt buộc

- Tùy chọn **Launch anyway / bỏ qua lỗi tương thích** không còn bỏ qua dependency bắt buộc bị thiếu, bị disable hoặc sai version.
- MCW thử hoàn thiện dependency graph trước khi tải, tải các file mới được thêm, rồi audit lại sau download.
- Nếu dependency bắt buộc vẫn chưa thể xác định hoặc tải, launcher chặn trước khi tạo process Minecraft và hiển thị lỗi rõ ràng.
- Các warning còn lại được gộp dưới nhãn chung `Launch warning`, không còn gắn nhầm mọi cảnh báo với Modrinth.

### Registry, Repair và provenance

Dependency tự động thêm được ghi lại với:

```json
{
  "selectionReason": "required_dependency",
  "requiredBy": ["FancyMenu"],
  "provider": "modrinth"
}
```

- File gốc của pack dùng `selectionReason: pack_manifest`.
- Provenance registry giữ nguyên `requiredBy` và lý do lựa chọn.
- Repair modpack chạy lại resolver, tải dependency mới tìm được và chặn nếu vẫn còn dependency bắt buộc chưa giải quyết.
- Modrinth registry nâng lên schema 6; CurseForge registry nâng lên schema 3; provenance registry nâng lên schema 2, có normalize tương thích dữ liệu cũ.

### Ví dụ lỗi được xử lý

Một pack có FancyMenu nhưng thiếu `drippyloadingscreen`, `fancy_entity_renderer`, `findme` và `konkrete` sẽ được MCW thử khôi phục tự động từ metadata provider trước khi launch. Nếu provider không cung cấp identity đáng tin cậy hoặc không có build tương thích với Minecraft/loader hiện tại, MCW dừng launch thay vì âm thầm chạy một pack chắc chắn thiếu dependency.

### Phiên bản và xác thực

- Launcher runtime: `v1.1.1-beta.5`
- Python distribution metadata: `1.1.1b5`
- MCW Core source/wheel riêng: chưa phát hành lại; sẽ đồng bộ khi `v1.1.1` stable.
- Toàn bộ test: **1375 passed, 88 skipped, 2 warnings**.
- `compileall` đạt cho `src`, `mcw_core` và `test`.

Hai warning đến từ fixture ZIP cố tình chứa entry trùng trong kiểm thử bảo mật, không phải lỗi dependency resolver.

---

## English

MCW Launcher **v1.1.1-beta.5** fixes a serious modpack pipeline issue: a pack manifest could download successfully while required dependencies declared by individual Modrinth or CurseForge mods were never added. Minecraft was then allowed to start with several warnings and would commonly fail immediately afterward.

### Modpack dependency resolver

- Adds a shared `ModpackDependencyResolver` for Modrinth and CurseForge managed packs.
- Recursively follows **required** dependencies with a 20-level depth limit and a maximum of 256 added files.
- Dependencies already present in the manifest or selected graph are not downloaded twice.
- Cycles are stopped using provider version/file identities.
- Recoverable provider metadata requests are retried up to three times.
- Modrinth files can be identified through `versionId`, CDN URL identity, or SHA-512/SHA-1 lookup.
- CurseForge dependency metadata is persisted in the pack registry so later launches and repairs avoid unnecessary repeated requests.

### The pack manifest remains authoritative

- MCW never silently replaces a file pinned by the modpack author.
- When a dependency requests another version of a project already pinned by the pack, the pinned file is kept and a warning explains the mismatch.
- A system requirement mismatch on a pack-pinned file, such as JEI declaring Minecraft `[1.21, 1.21.1)` inside a Minecraft `1.21.1` pack, remains a warning instead of causing an automatic JEI replacement.
- Optional, embedded, and incompatible relations are not mistaken for required dependencies that should be auto-installed.

### Required dependencies can no longer be bypassed

- **Launch anyway / compatibility override** no longer bypasses missing, disabled, or version-invalid required mod dependencies.
- MCW completes the dependency graph before downloads, downloads newly added files, and audits the result again afterward.
- If a required dependency still cannot be identified or installed, launch is blocked before a Minecraft process is created and a clear error is shown.
- Remaining warnings use the generic `Launch warning` label instead of incorrectly labeling every warning as Modrinth-specific.

### Registry, repair, and provenance

Automatically added dependencies are recorded with:

```json
{
  "selectionReason": "required_dependency",
  "requiredBy": ["FancyMenu"],
  "provider": "modrinth"
}
```

- Original pack files use `selectionReason: pack_manifest`.
- The provenance registry preserves `requiredBy` and selection reason.
- Modpack Repair reruns dependency resolution, downloads newly discovered dependencies, and blocks completion if required dependencies remain unresolved.
- Modrinth registry schema is upgraded to 6, CurseForge registry to 3, and provenance registry to 2, with backward-compatible normalization.

### Example fixed scenario

A pack containing FancyMenu but missing `drippyloadingscreen`, `fancy_entity_renderer`, `findme`, and `konkrete` is now repaired from trusted provider metadata before launch. If no trustworthy provider identity or compatible build can be found, MCW blocks launch rather than silently starting a predictably incomplete pack.

### Versions and validation

- Launcher runtime: `v1.1.1-beta.5`
- Python distribution metadata: `1.1.1b5`
- Separate MCW Core source/wheel: not republished until `v1.1.1` stable.
- Full test suite: **1375 passed, 88 skipped, 2 warnings**.
- `compileall` passes for `src`, `mcw_core`, and `test`.

The two warnings come from security-test ZIP fixtures that intentionally contain duplicate entries; they are unrelated to dependency resolution.
