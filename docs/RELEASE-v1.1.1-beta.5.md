# MCW Launcher v1.1.1-beta.5

## Tiếng Việt

MCW Launcher **v1.1.1-beta.5** sửa một lỗi nghiêm trọng trong pipeline modpack: manifest có thể tải đủ các file được tác giả pack liệt kê nhưng dependency bắt buộc do chính mod khai báo vẫn bị thiếu. Trước đây tùy chọn bỏ qua lỗi tương thích có thể cho Minecraft khởi chạy trong trạng thái này; Beta 5 không còn cho phép điều đó.

Bản cập nhật revision 2 của Beta 5 bổ sung lớp kiểm tra capability trong JAR và fallback tìm project trên provider. Nó xử lý cả dependency được nhúng như Flywheel trong Create và dependency chỉ xuất hiện dưới dạng mod ID như `kotlinforforge`.

### Resolver dependency theo nhiều tầng

MCW giải dependency theo thứ tự:

1. File được manifest modpack ghim.
2. Quan hệ dependency `required` có project/version ID từ Modrinth hoặc CurseForge.
3. Capability được cung cấp bởi JAR ngoài cùng hoặc JAR lồng bên trong.
4. Tìm project bằng mod ID trên provider ưu tiên của pack, rồi thử provider còn lại.
5. Tải candidate, audit metadata JAR thật và chỉ cho launch khi mod ID cùng version requirement đã được thỏa mãn.

Resolver duyệt đệ quy dependency provider với giới hạn 20 tầng và tối đa 256 file bổ sung. Metadata provider được retry tối đa ba lần đối với lỗi mạng có khả năng phục hồi. Dependency đã nằm trong manifest, graph hoặc instance không bị tải lặp.

### Dependency embedded và Jar-in-Jar

Thêm `ModCapabilityIndex` để đọc capability runtime từ:

- Forge/NeoForge `META-INF/jarjar/metadata.json`.
- JAR nằm dưới `META-INF/jarjar/` khi metadata cũ hoặc thiếu.
- Fabric nested JAR khai báo trong `fabric.mod.json`.
- Quilt metadata.
- Legacy Forge `ContainedDeps`.
- `META-INF/mods.toml`, `META-INF/neoforge.mods.toml`, `fabric.mod.json`, `quilt.mod.json` và `mcmod.info` của JAR lồng.

Scanner chỉ đọc, có giới hạn độ sâu, số lượng JAR, dung lượng giải nén và compression ratio để tránh quét không giới hạn.

Nhờ đó Flywheel `0.6.10` được nhúng trong Create có thể thỏa đồng thời:

```text
Create: [0.6.10,0.6.11)
Create Crafts & Additions: [0.6.8.a,0.7)
```

MCW không dùng ngoại lệ hard-code kiểu “bỏ qua Flywheel”; dependency chỉ được coi là đã có khi scanner thực sự tìm thấy capability đúng version trong JAR.

### Tìm dependency còn thiếu theo mod ID

Khi JAR audit phát hiện dependency bắt buộc nhưng provider relation không chứa project ID, MCW sẽ:

- Ưu tiên provider đang quản lý phần lớn mod của pack.
- Tìm project bằng mod ID, slug và tên đã chuẩn hóa.
- Lọc candidate theo Minecraft version và loader.
- Thử provider còn lại nếu provider đầu tiên không có candidate phù hợp.
- Ghi candidate với `selectionReason: jar_audit_dependency`, `providesModId`, `requestedVersionRanges` và `requiredBy`.
- Tải qua content pipeline hiện có, sau đó audit lại JAR thật trước khi launch.

Ví dụ `Create Slice & Dice` yêu cầu `kotlinforforge [3.9.1,)`: MCW có thể tìm Kotlin for Forge trên CurseForge dù relation ban đầu của pack không cung cấp project ID. Nếu file tải về không thực sự cung cấp `kotlinforforge` hoặc version không thỏa range, dependency vẫn bị coi là chưa giải quyết và launch bị chặn.

### So sánh version Forge/Maven

Bộ so sánh version đã được mở rộng cho các dạng thường gặp trong metadata Forge, bao gồm:

```text
0.6.8.a
0.6.10
3.9.1
1.0.0-beta
[0.6.10,0.6.11)
```

Điều này tránh so sánh chuỗi sai đối với range có thành phần chữ như `[0.6.8.a,0.7)`.

### Manifest của modpack vẫn là nguồn sự thật

- MCW không tự thay file mà tác giả modpack đã ghim.
- Nếu dependency yêu cầu version khác nhưng pack đã chọn sẵn một version của cùng project, file của pack được giữ lại và warning giải thích mismatch.
- Lỗi system requirement trên file pack-pinned, ví dụ JEI khai báo Minecraft `[1.21, 1.21.1)` trong pack Minecraft `1.21.1`, vẫn là warning thay vì tự đổi JEI.
- Optional và incompatible relation không bị tự cài như dependency bắt buộc.
- Embedded relation chỉ được coi là thỏa mãn sau khi capability thực tế được nhận diện.

### Không còn bỏ qua dependency bắt buộc

Tùy chọn **Launch anyway / bỏ qua lỗi tương thích** không thể bỏ qua:

- Dependency bắt buộc bị thiếu.
- Dependency bắt buộc bị disable.
- Dependency có version không thỏa yêu cầu.
- Dependency không thể xác định hoặc tải sau các bước recovery.

MCW resolve trước download, tải file mới, audit sau download rồi mới tạo process Minecraft. Warning đã được sửa thành công không còn bị lặp lại trong báo cáo cuối.

### Registry, Repair và provenance

Dependency được provider relation tự thêm dùng:

```json
{
  "selectionReason": "required_dependency",
  "requiredBy": ["FancyMenu"]
}
```

Dependency tìm từ JAR audit dùng:

```json
{
  "selectionReason": "jar_audit_dependency",
  "requiredBy": ["Create Slice & Dice"],
  "providesModId": "kotlinforforge",
  "requestedVersionRanges": ["[3.9.1,)"]
}
```

Repair modpack chạy lại resolver và capability audit. Modrinth registry dùng schema 6, CurseForge registry schema 3 và provenance registry schema 2, có normalize dữ liệu cũ.

### Phiên bản và xác thực

- Launcher runtime: `v1.1.1-beta.5`
- Python distribution metadata: `1.1.1b5`
- MCW Core source/wheel riêng: chưa phát hành lại; sẽ đồng bộ khi `v1.1.1` stable.
- Toàn bộ test: **1379 passed, 88 skipped, 2 warnings**.
- Nhóm test mod/dependency/Modrinth/CurseForge/launch/repair liên quan: **257 passed**.
- Test tập trung capability, resolver và compatibility: **19 passed**.
- `compileall` đạt cho `src`, `mcw_core` và `test`.

Hai warning đến từ fixture ZIP cố tình chứa entry trùng trong kiểm thử bảo mật, không phải lỗi dependency resolver.

Môi trường build chưa chạy Minecraft thật hoặc live provider API với pack Create được báo cáo. Smoke test Windows với chính modpack đó vẫn là bước xác nhận cuối.

---

## English

MCW Launcher **v1.1.1-beta.5** fixes a serious modpack pipeline issue: the pack manifest could download every author-pinned file while required dependencies declared by the mods themselves remained missing. The compatibility override could previously allow Minecraft to start in that state; Beta 5 no longer permits that.

Beta 5 revision 2 adds JAR capability indexing and provider project-search fallback. It handles both embedded dependencies such as Flywheel inside Create and dependencies known only by a mod ID such as `kotlinforforge`.

### Multi-stage dependency resolution

MCW resolves dependencies in this order:

1. Files pinned by the modpack manifest.
2. `required` provider relations with Modrinth or CurseForge project/version identities.
3. Capabilities supplied by top-level or nested JARs.
4. Project search by mod ID on the pack's preferred provider, followed by the other provider.
5. Download the candidate, audit the real JAR metadata, and launch only after the mod ID and version requirement are satisfied.

Provider dependency traversal is bounded to 20 levels and 256 added files. Recoverable provider requests are retried up to three times. Files already present in the manifest, dependency graph, or instance are not downloaded twice.

### Embedded and Jar-in-Jar capabilities

A new `ModCapabilityIndex` reads runtime capabilities from:

- Forge/NeoForge `META-INF/jarjar/metadata.json`.
- JARs below `META-INF/jarjar/` when older or incomplete metadata is used.
- Fabric nested JAR declarations in `fabric.mod.json`.
- Quilt metadata.
- Legacy Forge `ContainedDeps`.
- Nested `META-INF/mods.toml`, `META-INF/neoforge.mods.toml`, `fabric.mod.json`, `quilt.mod.json`, and `mcmod.info` metadata.

The scanner is read-only and bounded by depth, nested-JAR count, extracted size, and compression ratio.

An embedded Flywheel `0.6.10` can therefore satisfy both:

```text
Create: [0.6.10,0.6.11)
Create Crafts & Additions: [0.6.8.a,0.7)
```

There is no hard-coded “ignore Flywheel” rule. The dependency is considered present only when the required capability and version are actually found inside a JAR.

### Searching for dependencies known only by mod ID

When JAR audit finds a required dependency but provider relations contain no project ID, MCW now:

- Prefers the provider managing most of the pack's mods.
- Searches by normalized mod ID, slug, and project name.
- Filters candidates by Minecraft version and loader.
- Falls back to the other provider when needed.
- Records the candidate with `selectionReason: jar_audit_dependency`, `providesModId`, `requestedVersionRanges`, and `requiredBy`.
- Downloads through the existing content pipeline and audits the real JAR again before launch.

For example, when Create Slice & Dice requires `kotlinforforge [3.9.1,)`, MCW can locate Kotlin for Forge on CurseForge even when the original pack relation supplied no project ID. If the downloaded file does not actually provide `kotlinforforge`, or its version does not satisfy the range, the dependency remains unresolved and launch is blocked.

### Forge/Maven-style version comparison

The version comparator now handles common Forge metadata forms including:

```text
0.6.8.a
0.6.10
3.9.1
1.0.0-beta
[0.6.10,0.6.11)
```

This prevents lexical comparison errors for ranges containing letter components such as `[0.6.8.a,0.7)`.

### The pack manifest remains authoritative

- MCW does not silently replace files pinned by the modpack author.
- When a dependency requests another version of a project already pinned by the pack, the pinned file remains and a warning explains the mismatch.
- A system requirement mismatch on a pack-pinned file, such as JEI declaring Minecraft `[1.21, 1.21.1)` in a Minecraft `1.21.1` pack, remains a warning instead of triggering an automatic JEI replacement.
- Optional and incompatible relations are not installed as required dependencies.
- An embedded relation is considered satisfied only after its actual capability is identified.

### Required dependencies cannot be bypassed

**Launch anyway / compatibility override** cannot bypass:

- A missing required dependency.
- A disabled required dependency.
- An invalid required dependency version.
- A dependency that remains unidentified or unavailable after recovery.

MCW resolves before download, downloads new files, audits after download, and only then creates the Minecraft process. Warnings fixed during recovery are not repeated in the final report.

### Registry, repair, and provenance

Provider-relation dependencies use:

```json
{
  "selectionReason": "required_dependency",
  "requiredBy": ["FancyMenu"]
}
```

JAR-audit search dependencies use:

```json
{
  "selectionReason": "jar_audit_dependency",
  "requiredBy": ["Create Slice & Dice"],
  "providesModId": "kotlinforforge",
  "requestedVersionRanges": ["[3.9.1,)"]
}
```

Modpack Repair reruns both dependency resolution and capability audit. The Modrinth registry uses schema 6, CurseForge schema 3, and provenance schema 2 with backward-compatible normalization.

### Versions and validation

- Launcher runtime: `v1.1.1-beta.5`
- Python distribution metadata: `1.1.1b5`
- Separate MCW Core source/wheel: not republished until `v1.1.1` stable.
- Full test suite: **1379 passed, 88 skipped, 2 warnings**.
- Relevant mod/dependency/Modrinth/CurseForge/launch/repair tests: **257 passed**.
- Focused capability, resolver, and compatibility tests: **19 passed**.
- `compileall` passes for `src`, `mcw_core`, and `test`.

The two warnings come from security-test ZIP fixtures that intentionally contain duplicate entries; they are unrelated to dependency resolution.

The build environment did not launch Minecraft or call live provider APIs with the reported Create pack. A Windows smoke test with that exact pack remains the final confirmation step.
