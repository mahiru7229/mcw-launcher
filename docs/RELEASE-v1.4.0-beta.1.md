# MCW Launcher v1.4.0-beta.1

## Tiếng Việt

MCW Launcher **v1.4.0-beta.1** mở nhánh v1.4 với nền tảng **Task Lifecycle & Shutdown** mới, nút **Kill Instance** cho game đang chạy, và hardening Forge profile/cache để xử lý lỗi được ghi nhận ở issue #20. Các tối ưu tải modpack và Diagnostics v2 được chia sang beta.2 và beta.3 để mỗi beta có phạm vi regression rõ ràng.

### Task lifecycle / threading

- `TaskRunner` chuyển background work sang daemon worker thread để metadata/scan chậm không thể giữ process launcher sống sau khi cửa sổ đã đóng.
- Thêm cooperative `TaskCancellationToken`, trạng thái cancel, `cancel`, `cancel_group`, `cancel_all` và `begin_shutdown`.
- Background/network task hỗ trợ policy `REPLACE`: request mới supersede request cũ thay vì chỉ báo task đang chạy.
- Network retry dùng cancellation-aware wait/checkpoint nên backoff có thể dừng ngay khi task bị hủy.
- Khi shutdown bắt đầu, launcher ngừng nhận task mới, hủy progress/background work và bỏ result muộn; Minecraft đang chạy **không bị kill tự động**.
- Mutation nặng vẫn giữ policy bảo thủ trong beta.1; scheduler resource-aware/queue nâng cao sẽ tiếp tục ở beta.2.

### Kill Instance

- Nút chính tại Instance Workspace đổi từ **Launch** sang **Kill Instance** khi Minecraft đã ở trạng thái running.
- Kill luôn yêu cầu cảnh báo/confirmation vì game bị force-terminate và dữ liệu thế giới chưa lưu có thể mất.
- Runtime supervisor force-kill process tree thuộc launch session đã xác minh; action này tách biệt với Cancel Launch/progress task.
- Session bị người dùng kill được đánh dấu `killed_by_user`, không bị phân loại thành Minecraft crash chỉ vì exit code khác 0.

### Forge issue #20

- Forge profile discovery không còn fallback sang arbitrary/vanilla JSON khi installer không tạo profile Forge hợp lệ.
- Candidate chỉ được chấp nhận khi có Forge runtime marker và đúng loader version.
- Profile được parse + validate **trước khi ghi cache**.
- Cache Forge có metadata loader nhưng thiếu runtime bị coi là poisoned cache và tự invalidated/rebuilt.
- Regression bao phủ Forge 1.12.2 / 14.23.5.2860: vanilla fallback bị reject, profile có `net.minecraftforge:forge:1.12.2-14.23.5.2860` được chọn đúng.

### Kế hoạch beta v1.4

- **Beta 1:** Task lifecycle/shutdown, Kill Instance, Forge issue #20, giữ toàn bộ hardening issue #19 từ v1.3.2.
- **Beta 2:** adaptive modpack download, multi-hash one-pass, network/disk/hash resource budget, progress coalescing, journal batching và scheduler/resource conflict nâng cao.
- **Beta 3:** Diagnostics v2 (launcher/runtime/loader/hardware/task timeline), secret redaction, Create Issue Report, polish/benchmark và Windows soak trước RC/stable.
- **Beta 4 (bổ sung):** progress/task-state consistency, stale-result protection và cancel/busy cleanup trước RC.

### Metadata

- Launcher runtime: `v1.4.0-beta.1`
- Update channel: `beta`
- MCW Core runtime: `1.4.0-beta.1`
- Python distribution: `mcw-core 1.4.0b1`

### Lưu ý beta

Beta 1 thay đổi nền threading của GUI. Core/runtime regression có thể chạy headless, nhưng hành vi đóng cửa sổ, PySide signal delivery và force-kill process tree vẫn cần smoke/soak test trên Windows trước beta.2.

---

## English

MCW Launcher **v1.4.0-beta.1** starts the v1.4 line with a new **Task Lifecycle & Shutdown** foundation, a **Kill Instance** action for running games, and Forge profile/cache hardening for issue #20. Modpack performance work and Diagnostics v2 are split into beta.2 and beta.3; beta.4 was added afterward to harden progress/task-state consistency before RC.

### Task lifecycle / threading

- Background work now runs on daemon worker threads so a slow metadata/scan task cannot keep the launcher process alive after the window closes.
- Add cooperative cancellation tokens and task/group/all/shutdown cancellation APIs.
- Replaceable network/background requests supersede stale work instead of only reporting that a task is already running.
- Retry waits are cancellation-aware.
- Shutdown rejects new work, cancels launcher progress/background tasks, and ignores stale results while leaving running Minecraft processes alive by default.
- Heavy mutations remain conservative in beta.1; resource-aware mutation scheduling is planned for beta.2.

### Kill Instance

- The primary Instance Workspace action changes from **Launch** to **Kill Instance** while Minecraft is running.
- Force-kill requires confirmation and warns about unsaved game data.
- The runtime supervisor force-terminates the verified launch-session process tree.
- User-killed sessions are recorded separately and are not reported as crashes solely because of a non-zero exit code.

### Forge issue #20

- Forge profile discovery no longer falls back to arbitrary/vanilla version JSON.
- A candidate must contain a Forge runtime marker matching the requested loader.
- Profiles are parsed and validated before persistent cache publication.
- Poisoned cached profiles that advertise Forge metadata but lack Forge runtime content are invalidated and rebuilt.
- Regression coverage includes Forge 1.12.2 / 14.23.5.2860.

### Three-beta plan

- **Beta 1:** task lifecycle/shutdown, Kill Instance, Forge issue #20, plus inherited issue #19 hardening from v1.3.2.
- **Beta 2:** adaptive modpack downloads, one-pass multi-hash, resource budgets, progress coalescing, journal batching, and resource-aware scheduling.
- **Beta 3:** Diagnostics v2, secret redaction, Create Issue Report, task/runtime/loader/hardware context, polish/benchmarks, and Windows soak before RC/stable.
