# MCW Launcher v1.4.0-beta.2

## Tiếng Việt

MCW Launcher **v1.4.0-beta.2** là beta hiệu năng của nhánh v1.4. Bản này giữ TaskRunner/Kill Instance/Forge hardening từ beta.1, đồng thời giảm contention khi tải modpack và thêm **Update Priority Mode** để việc cập nhật launcher được ưu tiên tương tự shutdown.

### Update Priority Mode

- Khi người dùng xác nhận **Update now**, `TaskRunner` chuyển sang priority scope `update.*`.
- Các task launcher đang chạy ngoài scope update nhận cooperative cancellation; queued/background work không được phép chen task mới vào trong thời gian update.
- Core operation hiện tại cũng nhận cancel request để download/install/launch preparation có thể dừng ở checkpoint an toàn.
- Update download/prepare chỉ bắt đầu exclusive phase sau khi các task cạnh tranh đã settle; không force-kill worker đang ở critical filesystem commit.
- Minecraft process đang chạy không bị kill bởi Update Priority Mode. Launcher vẫn yêu cầu đóng instance game trước bước update như policy an toàn hiện tại.
- Nếu prepare/apply thất bại hoặc bị hủy, priority mode được release để launcher trở lại scheduling bình thường.

### Modpack / download performance

- Managed files của Modrinth `.mrpack` được download song song với concurrency thích ứng: thấp trên CPU ít core, tăng dần trên máy mạnh, và luôn bị cap bởi giới hạn download hiện tại.
- Mutation-heavy mod installation vẫn tuần tự trong beta.2 để tránh nhiều worker cùng thay đổi registry/content state của một instance.
- Thêm profile **Automatic / Responsive / Balanced / Maximum** trong Launcher Settings.
- `Automatic` tự giảm download concurrency khi Minecraft đang chạy để ưu tiên game; manual concurrency vẫn là explicit override.
- Hash verification hỗ trợ SHA-1/SHA-512/SHA-256 trong **một lượt đọc file** thay vì đọc lại artifact theo từng algorithm.
- Hash I/O có semaphore riêng: máy <=4 core mặc định chỉ một hash-heavy operation; máy mạnh hơn tối đa hai operation đồng thời.
- Download journal batch các cập nhật progress ngắn hạn và vẫn flush ngay các state quan trọng như start/cancel/fail/complete, giảm `fsync` cạnh tranh trên HDD.
- Progress reporter/coalescing hiện có tiếp tục giới hạn repaint/signal churn thay vì phát UI update theo từng chunk.

### Giới hạn beta.2

- Streamed hash reuse trực tiếp từ network sang Content Store và scheduler mutation/resource-lock sâu hơn chưa được coi là hoàn tất; chúng chỉ được đưa tiếp nếu benchmark beta cho thấy cần thiết.
- Beta.2 không phát hành MCW Core ZIP/WHL riêng. Core source bundled trong Launcher tiếp tục được regression-test, còn standalone Core artifact sẽ được build lại khi v1.4 stable.
- PySide6/Windows behavior cần smoke test thực tế cho Update Priority Mode, profile switching và installer handoff trước beta.3.

### Metadata

- Launcher runtime: `v1.4.0-beta.2`
- Update channel: `beta`
- Bundled Core runtime: `1.4.0-beta.2`

---

## English

MCW Launcher **v1.4.0-beta.2** is the performance beta of the v1.4 line. It retains beta.1 task lifecycle, Kill Instance, and Forge hardening while reducing modpack download contention and adding **Update Priority Mode**.

### Update Priority Mode

- Confirming **Update now** switches `TaskRunner` into an `update.*` priority scope.
- Non-update launcher tasks receive cooperative cancellation and new unrelated tasks are rejected while update priority is active.
- The current Core operation is also asked to cancel so download/install/launch preparation can stop at safe checkpoints.
- Exclusive update preparation/application waits for competing workers to settle rather than force-terminating critical filesystem work.
- Running Minecraft processes are never force-killed by update priority; the existing close-game requirement remains in place.
- Failed/cancelled update preparation releases priority mode cleanly.

### Modpack / download performance

- Modrinth `.mrpack` managed artifacts use adaptive parallel downloads bounded by CPU class and the configured download cap.
- Mutation-heavy instance mod installation remains serialized in beta.2 for data safety.
- Add **Automatic / Responsive / Balanced / Maximum** download profiles.
- Automatic mode downshifts concurrency while Minecraft is running; an explicit manual concurrency remains an override.
- SHA-1/SHA-512/SHA-256 verification is computed in one file pass.
- Hash I/O has its own small concurrency budget to reduce HDD/low-core contention.
- Download journal progress writes are batched while important state transitions remain immediately persisted.
- Existing progress coalescing continues to bound GUI update frequency.

### Beta limitations

- Direct streamed-hash reuse into Content Store and deeper mutation/resource-lock scheduling are not claimed complete in beta.2; they will only be extended if beta benchmarks justify the extra complexity.
- No separate MCW Core ZIP/WHL is published for beta.2. Standalone Core artifacts are reserved for the v1.4 stable release.
- Windows/PySide smoke testing remains required before beta.3.

### Metadata

- Launcher runtime: `v1.4.0-beta.2`
- Update channel: `beta`
- Bundled Core runtime: `1.4.0-beta.2`
