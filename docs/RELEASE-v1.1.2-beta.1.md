# MCW Launcher v1.1.2-beta.1

## Tiếng Việt

MCW Launcher **v1.1.2-beta.1** mở nhánh beta v1.1.2 với trọng tâm đầu tiên là tính đúng đắn của dependency resolver theo active loader.

### Dependency correctness

- Mở rộng environment capability handling cho `java`, `minecraft` và loader IDs để chúng không bị coi như mod cần tải.
- Giới hạn dependency metadata theo active loader, đặc biệt tránh kéo Fabric-side dependency vào NeoForge context.
- Không fallback sang dependency table của sibling/nested Forge component khi mod ID hiện tại không có table tương ứng.
- CurseForge multi-loader compatibility chỉ coi Fabric/Forge là universal trong chính context Fabric hoặc Forge, không áp dụng sai cho NeoForge.

### Regression coverage

- Bổ sung regression tests cho loader-scoped dependency parsing, environment capabilities, nested Forge metadata và CurseForge foreign-loader dependency traversal.
- Full test suite của source package beta: **1422 passed, 88 skipped** trước bước version metadata packaging; release metadata được validate lại trong gói beta.

### Release metadata

- Launcher runtime: `v1.1.2-beta.1`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b1`

### Scope

Beta 1 chỉ tập trung vào dependency correctness và regression coverage. Tối ưu modpack performance sẽ được tiếp tục sau khi loader-scoped dependency behavior ổn định.

---

## English

MCW Launcher **v1.1.2-beta.1** starts the v1.1.2 beta line with loader-scoped dependency correctness as the first priority.

### Dependency correctness

- Treats `java`, `minecraft`, and loader IDs as environment capabilities instead of downloadable mods.
- Scopes dependency metadata to the active loader, preventing Fabric-side dependencies from leaking into NeoForge resolution.
- Avoids falling back to dependency tables from sibling or nested Forge components when the current mod ID has no matching table.
- Restricts CurseForge Fabric/Forge universal compatibility to Fabric or Forge contexts instead of incorrectly applying it to NeoForge.

### Regression coverage

- Adds regression tests for loader-scoped parsing, environment capabilities, nested Forge metadata, and foreign-loader CurseForge dependency traversal.
- The beta source package is validated with the project test suite after release metadata is applied.

### Release metadata

- Launcher runtime: `v1.1.2-beta.1`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b1`

### Scope

Beta 1 is intentionally limited to dependency correctness and regression coverage. Large-modpack performance work follows after this behavior is stable.
