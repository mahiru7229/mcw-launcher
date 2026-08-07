# MCW Launcher v1.1.2-beta.5

- Fixed paused-launch manual imports so verified local files can be copied while network downloads remain paused; cancellation is still honored, and the manual import button is disabled while a batch is active.

## Tiếng Việt

MCW Launcher **v1.1.2-beta.5** là beta cuối dự kiến trước stable, tập trung vào độ mượt của modpack workflow, metadata legacy và manual dependency recovery trong cùng phiên launch.

### Modpack responsiveness

- Dependency-resolution progress của pack lớn được batch/throttle thay vì phát event cho từng artifact, giảm áp lực lên GUI event loop mà không đổi dependency semantics.
- CurseForge download batch lớn dùng concurrency thận trọng hơn và progress UI được throttle để giảm CPU/UI contention; batch nhỏ vẫn giữ mức concurrency hiện có.

### Legacy mod metadata

- `mcmod.info` JSON có control characters được đọc tolerant theo semantics legacy.
- Metadata malformed nhưng còn salvage được `modid`/name/version sẽ được dùng như legacy metadata thay vì tạo warning `Invalid mcmod.info` không cần thiết.
- File thực sự không thể xác định mod identity vẫn bị coi là invalid; parser không bỏ qua lỗi một cách mù quáng.

### Manual dependency pause/resume

- Khi CurseForge hoặc Modrinth không thể tải trực tiếp một hay nhiều artifact bắt buộc, launch worker pause ngay tại provider stage thay vì fail toàn bộ launch.
- GUI hiển thị toàn bộ manual requirements của provider để người dùng import nhiều file trong một lượt.
- Manual import được phép trong lúc launch đang pause chỉ khi có đúng instance preparing-lock token của phiên launch đó.
- Khi tất cả manual requirements đã đủ, launcher resume cùng launch session, revalidate provider stage và tiếp tục launch; không chạy lại dependency preflight từ đầu.
- Cancel trong khi đang chờ manual content vẫn hủy launch đúng cách.

### Regression coverage

- Large-pack dependency progress batching và large-download worker policy.
- Tolerant/salvageable legacy `mcmod.info` cases từ diagnostics RLCraft.
- CurseForge/Modrinth manual dependency pause, resume, cancellation và preparing-lock ownership.
- Batch manual import trong phiên launch đang pause.

### Release metadata

- Launcher runtime: `v1.1.2-beta.5`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b5`

---

## English

MCW Launcher **v1.1.2-beta.5** is the planned final beta before stable, focused on smoother modpack workflows, legacy metadata tolerance, and same-session recovery for manually supplied dependencies.

### Modpack responsiveness

- Large-pack dependency-resolution progress is batched/throttled instead of emitting an event for every artifact, reducing GUI event-loop pressure without changing dependency semantics.
- Large CurseForge download batches use a more conservative concurrency limit and slower UI progress emission to reduce CPU/UI contention, while smaller batches retain the existing concurrency level.

### Legacy mod metadata

- Legacy `mcmod.info` JSON with control characters is parsed tolerantly.
- Malformed metadata that still exposes a salvageable mod id/name/version is treated as legacy metadata instead of producing unnecessary `Invalid mcmod.info` warnings.
- Files whose mod identity cannot be recovered remain invalid; parsing failures are not ignored blindly.

### Manual dependency pause/resume

- When CurseForge or Modrinth cannot directly download one or more required artifacts, the launch worker pauses at that provider stage rather than failing the complete launch.
- The GUI presents all manual requirements for that provider so several files can be imported in one pass.
- Manual import during a paused launch is allowed only with the exact instance preparing-lock token owned by that launch session.
- Once all manual requirements are satisfied, the same launch session resumes, revalidates the blocked provider stage, and continues without restarting dependency preflight from the beginning.
- Cancelling while waiting for manual content still cancels the launch correctly.

### Regression coverage

- Large-pack dependency progress batching and large-download worker policy.
- Tolerant/salvageable legacy `mcmod.info` cases based on the RLCraft diagnostics.
- CurseForge/Modrinth manual dependency pause, resume, cancellation, preparing-lock ownership, and batch import while launch is paused.

### Release metadata

- Launcher runtime: `v1.1.2-beta.5`
- Update channel: `beta`
- Python distribution: `mcw-core 1.1.2b5`
