# MCW Launcher v1.1.2-beta.2

## Tiếng Việt

MCW Launcher **v1.1.2-beta.2** sửa các false dependency blocker được tái hiện từ diagnostics SkyFactory 5 và bắt đầu tối ưu download modpack theo bounded concurrency.

### Dependency correctness

- Pack-pinned artifact giữ quyền ưu tiên của manifest: metadata JAR thuộc loader khác chỉ tạo warning, không còn sinh dependency blocker giả.
- Standalone mod vẫn được kiểm tra loader/dependency nghiêm ngặt như trước.
- CurseForge dependency selection loại file sai active loader và sai Minecraft version trước khi chọn candidate.
- Provider dependency của file pack-pinned không còn ép tải artifact sai loader khi không có candidate phù hợp; manifest của pack tiếp tục là authority.
- JAR có đồng thời `mods.toml` và `neoforge.mods.toml` được parse theo active Forge/NeoForge loader.

### Launch dependency passes

- Tái sử dụng dependency resolution ban đầu khi provider ensure không có download pending, tránh lặp lại toàn bộ dependency graph không cần thiết.
- Khi có file pending/download mới, resolver vẫn refresh và tiếp tục fixed-point completion để không mất dependency xuất hiện muộn.

### Modpack performance

- CurseForge modpack artifacts được download song song bằng bounded `ThreadPoolExecutor` với tối đa 8 workers.
- Bước add/validate/finalize mod vẫn chạy tuần tự để tránh race trên instance state.
- Giữ nguyên shared HTTP client, checksum/integrity validation, retry behavior và aggregate progress reporting.

### Regression coverage

- Thêm regression cho SkyFactory 5 Forge 1.20.1: Fabric API/Fabric Loader/NeoForge foreign metadata và YACL -> CurseForge project `306612`.
- Thêm regression cho Forge/NeoForge mixed metadata, strict CurseForge candidate selection, reuse dependency resolution và concurrent modpack downloads.

### Release metadata

- Launcher runtime: `v1.1.2-beta.2`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b2`

---

## English

MCW Launcher **v1.1.2-beta.2** fixes false dependency blockers reproduced from the SkyFactory 5 diagnostics and introduces bounded-concurrency CurseForge modpack downloads.

### Dependency correctness

- Pack-pinned artifacts keep manifest authority: foreign-loader JAR metadata becomes advisory instead of a false dependency blocker.
- Standalone mods remain strictly validated.
- CurseForge dependency selection rejects wrong-loader and wrong-Minecraft-version candidates before selection.
- Pack-pinned provider relations no longer force a foreign-loader artifact when no active-loader candidate exists.
- Mixed `mods.toml` / `neoforge.mods.toml` JARs are parsed according to the active Forge-family loader.

### Performance and validation

- Reuses the initial dependency result when no managed download occurred.
- Keeps fixed-point refresh when content was downloaded or new dependencies were added.
- Downloads CurseForge modpack artifacts concurrently with at most 8 workers while keeping instance mutation/finalization sequential.
- Preserves integrity checks, retries, shared HTTP pooling and aggregate progress reporting.

### Release metadata

- Launcher runtime: `v1.1.2-beta.2`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b2`
