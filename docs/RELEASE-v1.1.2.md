# MCW Launcher v1.1.2

## Tiếng Việt

MCW Launcher **v1.1.2** đưa toàn bộ nhánh Beta 1–5 và hotfix manual-import cuối lên stable. Bản phát hành này tập trung vào correctness của dependency/modpack, giảm false warning, tăng độ ổn định khi cài mod loader và làm mượt workflow của các modpack lớn.

### Dependency resolver và modpack

- Scope dependency theo active loader; metadata Fabric/Forge/NeoForge/Quilt không còn bị trộn thành một dependency context toàn cục.
- `java`, `minecraft` và loader IDs được đánh giá như environment capabilities thay vì downloadable mods.
- Giữ manifest authority cho artifact được modpack pin; foreign-loader metadata không tự tạo blocker giả.
- CurseForge dependency candidate phải khớp Minecraft version và active loader trước khi được chọn.
- Nhận diện embedded/JarJar capabilities và nested mods để dependency như `expandability` có thể được thỏa ngay bên trong JAR cha, không cần JAR top-level trùng.
- Resolver reuse kết quả preflight khi có thể và chỉ chạy lại sau khi dependency graph thực sự thay đổi.

### Mod identity, version matching và cleanup

- Duplicate detection chỉ so sánh primary/top-level mod IDs; provided/embedded capabilities vẫn thỏa dependency nhưng không tạo false `Duplicate enabled mod ID`.
- Vẫn phát hiện duplicate thật khi hai JAR top-level cùng cung cấp một primary mod ID.
- Cải thiện Forge/Maven-style version comparison cho numeric revisions, qualifiers, combined loader versions và danh sách version alternatives.
- Optional recommendations và foreign-provider notices không actionable được hạ khỏi launch warning để diagnostics dễ đọc hơn.
- Stale required dependency chỉ được auto-clean khi provenance chứng minh launcher đã quản lý file và hash không cho thấy người dùng sửa file.

### Hiệu năng modpack và cài mod loader

- CurseForge modpack download dùng bounded concurrency; batch lớn dùng worker thận trọng hơn để giảm contention.
- Dependency progress của pack lớn được batch/throttle để giảm tải cho GUI event loop.
- Fabric/Quilt resolve metadata library song song có giới hạn.
- Forge/NeoForge staging tái sử dụng Vanilla libraries đã cache thay vì để installer tải lại không cần thiết.
- Java installer retry đúng một lần cho lỗi mạng tạm thời rõ ràng và trả diagnostic có ngữ cảnh khi timeout.

### Legacy metadata

- `mcmod.info` legacy có control characters hoặc JSON malformed nhưng còn salvage được identity sẽ được đọc tolerant.
- Parser vẫn giữ validation: metadata không thể phục hồi mod identity vẫn được coi là invalid.

### Manual dependency recovery

- Khi CurseForge/Modrinth không thể tải trực tiếp một hay nhiều dependency bắt buộc, launch pause ngay tại provider stage thay vì fail toàn bộ instance.
- GUI gom các manual requirements và cho phép import nhiều file trong một lượt.
- Sau khi đủ file, cùng launch session revalidate rồi resume; không chạy lại toàn bộ dependency preflight từ đầu.
- Manual import trong paused launch chỉ được phép với đúng preparing-lock token của phiên launch và vẫn tôn trọng Cancel.
- Hotfix cuối của Beta 5 sửa deadlock do manual batch dùng chung download pause controller, đồng thời chặn submit batch trùng khi import đang chạy.

### Xác thực thực tế trong beta

- SkyFactory 5: các false dependency do foreign-loader/pack-pinned metadata đã được loại và pack launch thành công.
- All The Mods 9: embedded `expandability` trong Artifacts được nhận diện đúng và pack launch thành công.
- RLCraft/Forge legacy được dùng để kiểm tra metadata legacy và manual dependency workflow.

### Metadata phát hành

- Launcher runtime: `v1.1.2`
- Update channel: `stable`
- Python distribution: `mcw-core 1.1.2`

---

## English

MCW Launcher **v1.1.2** promotes the complete Beta 1–5 branch and the final manual-import hotfix to stable. This release focuses on dependency/modpack correctness, quieter and more actionable preflight output, more reliable mod-loader installation, and smoother large-modpack workflows.

### Dependency resolver and modpacks

- Scopes dependency metadata to the active loader instead of merging Fabric/Forge/NeoForge/Quilt metadata globally.
- Treats Java, Minecraft, and loader IDs as environment capabilities rather than downloadable mods.
- Preserves manifest authority for pack-pinned artifacts so foreign-loader metadata does not become a false blocker.
- Requires CurseForge dependency candidates to match both the Minecraft version and active loader before selection.
- Recognizes embedded/JarJar capabilities and nested mods, allowing dependencies such as `expandability` to be satisfied inside a parent artifact without a duplicate top-level JAR.
- Reuses dependency-preflight results where possible and resolves again only after the graph actually changes.

### Mod identity, version matching, and cleanup

- Duplicate detection compares primary/top-level mod IDs only; provided/embedded capabilities still satisfy dependencies without false `Duplicate enabled mod ID` warnings.
- Real top-level duplicate mod IDs are still detected.
- Improves Forge/Maven-style version comparison for numeric revisions, qualifiers, combined loader versions, and alternative-version lists.
- Optional recommendations and non-actionable foreign-provider notices are no longer promoted to launch warnings.
- Stale required dependencies are auto-cleaned only when provenance proves launcher ownership and the stored hash does not indicate user modification.

### Modpack performance and mod-loader installation

- Uses bounded concurrency for CurseForge modpack downloads with a more conservative worker policy for large batches.
- Batches/throttles large-pack dependency progress to reduce GUI event-loop pressure.
- Resolves Fabric/Quilt library metadata concurrently with bounded workers.
- Reuses cached Vanilla libraries during Forge/NeoForge installer staging.
- Retries Java installers once for clearly transient network failures and reports timeout failures with contextual diagnostics.

### Legacy metadata

- Tolerantly salvages legacy `mcmod.info` metadata containing control characters or malformed JSON when a usable mod identity can still be recovered.
- Metadata whose identity cannot be recovered remains invalid; validation is not bypassed blindly.

### Manual dependency recovery

- When CurseForge/Modrinth cannot directly download one or more required artifacts, the current launch pauses at the provider stage instead of failing the full instance flow.
- The GUI groups manual requirements and lets the user import several files in one pass.
- Once all files are present, the same launch session revalidates and resumes without restarting dependency preflight from the beginning.
- Paused-launch imports require the exact preparing-lock token owned by the launch session and still honor cancellation.
- The final Beta 5 hotfix removes the shared-pause deadlock that could leave a manual batch task stuck as already running and prevents duplicate batch submissions while an import is active.

### Real-world beta validation

- SkyFactory 5 launched successfully after removing foreign-loader/pack-pinned false dependency blockers.
- All The Mods 9 launched successfully after correctly recognizing embedded `expandability` supplied by Artifacts.
- RLCraft/legacy Forge was used to validate legacy metadata and manual dependency workflows.

### Release metadata

- Launcher runtime: `v1.1.2`
- Update channel: `stable`
- Python distribution: `mcw-core 1.1.2`
