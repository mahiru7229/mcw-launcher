# MCW Launcher v1.3.0-beta.2

## Tiếng Việt

MCW Launcher **v1.3.0-beta.2** giữ nguyên nền Shared Storage & Cache Lifecycle của Beta 1 và sửa một race condition trong vòng đời xóa instance.

### Xóa instance hoàn toàn

- Khi người dùng xóa một instance vừa chạy hoặc vừa dừng game, launcher giờ chờ bước runtime exit finalization hoàn tất trước khi xóa thư mục instance.
- Trước đây runtime watcher có thể hoàn tất trễ hơn thao tác xóa và tạo lại `crash-reports/` cùng `.mcw/runtime-history.json`, khiến thư mục instance xuất hiện trở lại dù UI đã báo xóa thành công.
- `GameRuntimeManager` theo dõi các watcher đang finalizing theo instance và `InstanceDeletionManager` chờ chúng hoàn tất trước khi `rmtree` toàn bộ root.
- Nếu finalization không kết thúc trong thời gian an toàn, launcher không báo thành công giả: deletion được queue và người dùng có thể retry/sử dụng startup recovery.
- Regression test tái hiện đúng race thực tế với `.mcw`, `crash-reports`, `mods` và runtime watcher, sau đó xác nhận `instance.instance_dir` không còn tồn tại.

### Phạm vi

- Không thay đổi Shared Storage/ContentStore đã được xác nhận ở Beta 1.
- Không thay đổi Provider API Cache.
- Không thay đổi saves/config/modpack data ngoài hành vi xóa toàn bộ khi người dùng đã xác nhận **Delete instance**.

### Version metadata

- Launcher runtime: `v1.3.0-beta.2`
- Update channel: `beta`
- Python distribution metadata: `mcw-core 1.3.0b2`

## English

MCW Launcher **v1.3.0-beta.2** keeps the Beta 1 shared-storage foundation unchanged and fixes an instance-deletion race. A runtime watcher could previously finish after the instance root had been removed and recreate `crash-reports/` plus `.mcw/runtime-history.json`. Deletion now waits for runtime exit processing before removing the complete instance root. If finalization does not finish in time, deletion is queued instead of reporting a false success.
