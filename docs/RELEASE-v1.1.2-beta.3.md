# MCW Launcher v1.1.2-beta.3

## Tiếng Việt

MCW Launcher **v1.1.2-beta.3** sửa blocker dependency embedded được tái hiện từ All the Mods 9 (ATM9).

### Dependency correctness

- Dependency validation giờ sử dụng `ModCapabilityIndex` khi một required dependency chưa xuất hiện ở top-level/provided metadata.
- Forge/NeoForge JarJar capability được nhúng trong JAR có thể thỏa version range mà không cần file `.jar` độc lập trong `mods/`.
- Provider dependency resolution coi embedded capability là đã cài, tránh thêm standalone dependency trùng khi nested runtime đã cung cấp mod ID đó.
- Không hardcode `Artifacts` hay `expandability`; fix áp dụng tổng quát cho embedded mod capabilities.

### ATM9 regression

- Tái hiện `Artifacts -> expandability [9.0.0,)` với `expandability 9.0.4` nằm trong `META-INF/jarjar/`.
- Regression xác nhận không có `expandability-*.jar` top-level vẫn thỏa dependency.
- Version của embedded capability vẫn được kiểm tra; capability quá cũ tiếp tục báo `dependency-version`.

### Release metadata

- Launcher runtime: `v1.1.2-beta.3`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b3`

---

## English

MCW Launcher **v1.1.2-beta.3** fixes an embedded-dependency blocker reproduced from All the Mods 9 (ATM9).

### Dependency correctness

- Dependency validation now consults `ModCapabilityIndex` when a required dependency is absent from top-level/provided metadata.
- Forge/NeoForge JarJar capabilities embedded inside another JAR can satisfy version ranges without a standalone JAR in `mods/`.
- Provider dependency resolution treats embedded capabilities as already installed and avoids adding duplicate standalone dependencies.
- The fix is generic; no `Artifacts` or `expandability` special case is hardcoded.

### Regression coverage

- Reproduces `Artifacts -> expandability [9.0.0,)` with embedded `expandability 9.0.4` under `META-INF/jarjar/`.
- Confirms that no top-level `expandability-*.jar` is required.
- Embedded versions remain subject to normal dependency-range validation.

### Release metadata

- Launcher runtime: `v1.1.2-beta.3`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b3`
