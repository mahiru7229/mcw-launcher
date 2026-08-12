# MCW Launcher v1.4.0-beta.4

## Tiếng Việt

MCW Launcher **v1.4.0-beta.4** là beta bổ sung tập trung vào độ chính xác của progress và trạng thái task trên toàn launcher.

### Thay đổi chính

- Task mới khi chiếm vùng progress sẽ reset trạng thái cũ thay vì chỉ đổi tiêu đề và giữ lại `READY`, `100%` hoặc detail của task trước.
- Task cũ hoàn tất muộn không còn được phép ghi đè progress của task mới đang chạy.
- Task bị cancel/supersede đi qua cùng đường cleanup UI như success/failure, tránh dialog/provider bị kẹt trạng thái busy.
- Busy state Modrinth, CurseForge, FTB, ATLauncher, content, mod catalog, modpack và update được đồng bộ lại từ danh sách task thực sự còn active.
- Blocking user operation được ưu tiên sở hữu progress; metadata/background task không chen vào progress khi operation blocking đang chạy.
- Legacy Storage probe/scan/cleanup có completion/failure progress riêng, bao gồm flow bỏ qua review và dọn dữ liệu.
- Giữ toàn bộ cải tiến từ beta.1–beta.3: TaskRunner v2, Kill Instance, Forge issue #20 hardening, Update Priority, adaptive modpack downloads và Diagnostics v2.

### Ghi chú beta

Beta/RC chỉ phát hành Launcher changed-files ZIP. Standalone MCW Core artifact chỉ được build khi v1.4 stable.

---

## English

MCW Launcher **v1.4.0-beta.4** is an additional beta focused on consistent progress and task state across the launcher.

### Highlights

- A newly displayed task resets stale global progress instead of inheriting the previous task's READY/100%/detail state.
- Late completion from an older concurrent task can no longer overwrite a newer task's progress.
- Cancelled and superseded tasks now follow the same UI busy cleanup path as success/failure.
- Provider/dialog busy state is rebuilt from actual TaskRunner activity.
- Blocking user operations own the global progress area; background metadata work cannot steal it while blocking work is active.
- Legacy Storage probe/scan/cleanup now expose explicit terminal progress states.
- All beta.1–beta.3 lifecycle, performance, update-priority and diagnostics work remains included.
