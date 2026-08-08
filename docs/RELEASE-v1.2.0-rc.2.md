# MCW Launcher v1.2.0-rc.2

## Tiếng Việt

MCW Launcher **v1.2.0-rc.2** là release candidate thứ hai của nhánh v1.2. Bản này tiếp tục **feature freeze**; không thêm tính năng mới và chỉ sửa hai lỗi được phát hiện khi test bản `.exe` RC.1.

### Fixes

- Sửa **Instance Overview** hiển thị literal `\n` giữa Favorite / Group / Tags. Chuỗi localization giờ dùng line break thực.
- Sửa lỗi **ổ đĩa hết dung lượng (ENOSPC)** bị hiểu nhầm thành manual-download recovery ở CurseForge/Modrinth.
- `DISK_SPACE_ERROR` và local `FILE_ACCESS_ERROR` giờ là **terminal local-storage failure**: launcher không pause để yêu cầu tải file thủ công vì file thủ công không thể khắc phục việc đích ghi đang hết dung lượng/không ghi được.
- Khi lỗi storage xảy ra trong launch preparation, task kết thúc và `InstanceRunLock` được release; người dùng có thể xóa instance hoặc dọn dung lượng ngay thay vì bị giữ ở trạng thái Preparing.
- Manual download flow cho các lỗi thực sự cần nguồn bên thứ ba vẫn giữ nguyên.

### Release policy

RC.2 không thay đổi feature set của Beta 1–3. Nếu smoke test `.exe` không phát hiện blocker mới, bước tiếp theo là **v1.2.0 stable**.

### Version metadata

- Launcher runtime: `v1.2.0-rc.2`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0rc2`

## English

MCW Launcher **v1.2.0-rc.2** is the second release candidate for the v1.2 line. It remains **feature frozen** and only fixes two issues found while smoke-testing the RC.1 Windows build.

### Fixes

- Fixed **Instance Overview** rendering literal `\n` text between Favorite / Group / Tags; localization now contains real line breaks.
- Fixed **out-of-disk-space (ENOSPC)** failures being misclassified as manual-download recovery for CurseForge/Modrinth.
- `DISK_SPACE_ERROR` and local `FILE_ACCESS_ERROR` are now terminal local-storage failures, because selecting a manual source cannot fix an unwritable/full destination.
- A storage failure during launch preparation now terminates the task and releases the instance preparing lock, allowing the user to delete the instance or free storage immediately.
- Genuine third-party/manual-source recovery remains unchanged.

### Version metadata

- Launcher runtime: `v1.2.0-rc.2`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.2.0rc2`
