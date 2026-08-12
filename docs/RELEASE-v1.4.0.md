# MCW Launcher v1.4.0

## Tiếng Việt

MCW Launcher **v1.4.0** là bản stable hợp nhất toàn bộ nhánh v1.4, tập trung vào khả năng phản hồi của launcher, lifecycle task có thể hủy, hiệu năng tải modpack trên máy trung/yếu, độ tin cậy của Forge/runtime, diagnostics và tính nhất quán của progress UI.

### Task lifecycle, cancellation và shutdown

- TaskRunner hỗ trợ cooperative cancellation, task generations và replace/supersede cho background/network work.
- Task cũ trả kết quả muộn không còn được phép ghi đè UI của task mới.
- Khi đóng launcher, launcher ngừng nhận work mới, hủy/drop work nền và ưu tiên shutdown thay vì chặn cửa sổ cho tới khi metadata/scan hoàn tất.
- Minecraft đang chạy được giữ sống khi launcher đóng theo mặc định.
- Network retry/wait và các operation đã migrate có cancellation checkpoint rõ ràng.

### Kill Instance

- Nút Launch trong Instance Workspace đổi thành **Kill Instance** khi Minecraft thực sự đang chạy.
- Kill yêu cầu confirmation và đi qua runtime/process supervisor thay vì gọi process API trực tiếp từ GUI.
- Process/session ownership được kiểm tra trước khi force-kill.
- Phiên bị người dùng kill được đánh dấu riêng nên không bị báo nhầm thành Minecraft crash.

### Forge issue #20 và runtime integrity

- Forge profile selection không còn fallback sang arbitrary/vanilla JSON khi installer không tạo profile hợp lệ.
- Forge runtime/profile được validate trước khi cache và trước khi launch.
- Poisoned Forge cache cũ tự invalidate để launcher có thể rebuild thay vì lặp lại lỗi vĩnh viễn.
- Regression bao phủ Minecraft 1.12.2 / Forge 14.23.5.2860.
- Diagnostics bổ sung loader/profile/cache context để lỗi legacy Forge có thể được phân tích từ bundle.

### Update Priority Mode

- Khi người dùng chọn cập nhật launcher, TaskRunner chuyển sang update-priority mode.
- Task không liên quan được cancel/drop và task mới ngoài update bị chặn trong lúc update chiếm scheduler.
- Bước apply chỉ bắt đầu sau khi work cũ đã drain tới safe checkpoint.
- Running Minecraft instance không bị launcher tự force-kill để cập nhật.

### Modpack download và I/O performance

- Modrinth `.mrpack` managed files hỗ trợ adaptive parallel download với giới hạn bảo thủ theo CPU/concurrency profile.
- SHA-1, SHA-512 và SHA-256 được tính trong một lượt đọc thay vì đọc lại artifact cho từng digest.
- Hash I/O có budget riêng để giảm disk thrashing trên máy ít core/HDD.
- Download journal progress được batch/coalesce để giảm `fsync` cạnh tranh khi nhiều artifact đang tải.
- Performance profile gồm **Automatic / Responsive / Balanced / Maximum**; Automatic giảm tải khi Minecraft đang chạy.
- Mutation-heavy work trên cùng instance vẫn được serialize để ưu tiên consistency hơn throughput.

### Diagnostics v2 và Report an issue

- Diagnostics bundle có launcher logs, runtime/crash logs gần nhất, loader context, system/CPU/RAM/GPU/storage summary, Java runtimes, instance state/health và task timeline.
- Collector failure được cô lập: một collector lỗi không làm toàn bộ diagnostics export thất bại.
- Log/bundle có size limits và centralized redaction cho token, authorization data và path nhạy cảm.
- Nút **Báo cáo lỗi** mở màn hình nhập title, mô tả, bước tái hiện, expected/actual trước; chỉ sau khi người dùng tiếp tục launcher mới thu diagnostics ở background và hiện hướng dẫn GitHub issue.
- Error dialog có thể prefill context lỗi gần nhất.
- Report dialog được thu gọn để phù hợp tốt hơn với màn hình 1366×768.

### Progress/state consistency

- Global progress có ownership/generation guard: task cũ hoàn tất muộn không được ghi đè task mới.
- Task mới reset stale READY/100%/detail state thay vì chỉ đổi tiêu đề.
- Cancel/supersede chạy cùng cleanup path với success/failure để busy state không bị kẹt.
- Blocking user operation được ưu tiên vùng progress so với metadata/background work.
- Legacy Storage probe/scan/clean có completion/failure terminal state riêng, bao gồm flow Skip và Delete/Clean.
- Stable chứa hotfix import `ProgressStage` và static regression guard để runtime symbol progress không bị thiếu import trong headless CI.

### Hardening kế thừa từ v1.3.2

- Giữ fix issue #19 cho Windows fixed-temp race/WinError 32.
- Atomic writer dùng per-operation temporary file, retry `os.replace()` và best-effort cleanup.
- Short-workspace recursive cleanup canonicalize path và chặn parent escape/root deletion.
- Automatic updater yêu cầu SHA-256 tin cậy và update manifest có managed-file inventory/rollback.
- Modpack archive path validation và transactional theme publish tiếp tục được giữ nguyên.

### Compatibility và version metadata

- Launcher runtime: `v1.4.0`
- Update channel: `stable`
- Python distribution: `mcw-core 1.4.0`
- Không có migration bắt buộc cho account database, instance format, theme schema hoặc modpack package format.

---

## English

MCW Launcher **v1.4.0** promotes the complete v1.4 beta line to stable, with a focus on responsive task lifecycle, cancellable background work, lower-impact modpack downloading, Forge/runtime reliability, diagnostics, and consistent progress ownership.

### Highlights

- Cooperative task cancellation, replace/supersede generations, stale-result suppression, and shutdown-first launcher behavior.
- **Kill Instance** for supervised forced termination of a running Minecraft session without misclassifying user termination as a crash.
- Strict Forge profile/runtime validation, validate-before-cache, and poisoned-cache invalidation, including regression coverage for Forge 1.12.2 / 14.23.5.2860.
- **Update Priority Mode** that cancels unrelated launcher work and reserves scheduling for update operations before apply.
- Adaptive Modrinth `.mrpack` downloads, one-pass SHA-1/SHA-512/SHA-256 hashing, bounded hash I/O, batched journal progress, and performance profiles.
- Diagnostics v2 with runtime/loader/system/Java/task context, collector isolation, size limits, privacy redaction, and a guided issue-report workflow.
- Progress ownership/generation protection so late or cancelled tasks cannot leave stale READY/100%/busy state or overwrite newer work.
- Carries forward the v1.3.2 Windows atomic-write, update-integrity, filesystem-containment, modpack-path, and transactional-theme hardening.

### Version metadata

- Launcher runtime: `v1.4.0`
- Update channel: `stable`
- Python distribution: `mcw-core 1.4.0`
