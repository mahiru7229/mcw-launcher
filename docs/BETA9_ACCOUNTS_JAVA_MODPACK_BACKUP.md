# MCW Launcher Beta 9 — Accounts, Java, Modpack Lifecycle & Backup

Beta 9 gộp scope dự kiến của Beta 9 và Beta 10 thành một release lớn.

## Microsoft Authentication

Microsoft Authentication is available in Beta 9:

```text
OAuth PKCE
→ Xbox Live
→ XSTS
→ Minecraft Services
→ entitlement
→ Minecraft profile
→ account repository
```

Launcher supports multiple Microsoft accounts and identifies an existing account by Minecraft UUID instead of username. Adding an account opens the Microsoft account picker, while selecting the same profile refreshes its tokens without creating a duplicate.

The sign-in flow runs outside the GUI thread. While waiting for the browser callback, the Accounts page shows a **Cancel Microsoft sign-in** button. Closing the browser no longer freezes the launcher; the user can cancel immediately and retry.

## Java diagnostics

Launcher Settings có card Java mới:

- quét `JAVA_HOME`;
- quét PATH;
- quét Program Files;
- quét Windows Registry;
- quét managed runtimes;
- chạy Java để xác nhận executable hoạt động;
- hiển thị major version, vendor, architecture, source và path;
- mở folder của Java đã chọn.

## Instance backup

Định dạng mới: `.mcwbackup`.

Hai scope:

- `full`: dữ liệu có thể khôi phục của instance;
- `worlds`: chỉ folder `saves`.

Backup không chứa runtime lock, launcher metadata nội bộ, logs hoặc crash reports. Restore hoạt động theo transaction và tạo safety backup trước khi thay dữ liệu.

Backup mặc định nằm tại:

```text
backups/<instance-id>/
```

## Modrinth modpack update

Instance cài từ `.mrpack` có thể:

- quét managed files;
- kiểm tra bản pack mới theo Release/Beta/Alpha settings;
- tạo full safety backup;
- tải và validate `.mrpack` mới;
- giữ file người dùng đã sửa;
- không ghi đè file unmanaged đang tồn tại;
- xóa file pack cũ chỉ khi file chưa bị người dùng chỉnh;
- cập nhật Minecraft/Fabric profile;
- rollback backup và registry khi bất kỳ bước nào thất bại.

Registry được nâng lên schema 3 và lưu:

```json
{
  "managedFiles": [],
  "preservedFiles": [],
  "lastBackup": "..."
}
```

Beta 9 giữ file conflict thay vì hiển thị trình chọn từng file. UI conflict resolution chi tiết có thể được bổ sung sau.

## Theme

Asset mới:

- `surface.microsoft_card`
- `surface.java_card`
- `surface.lifecycle_card`
- `badge.locked`
- `icon.action.microsoft`
- `icon.action.java`
- `icon.action.backup`
- `icon.action.restore`

Mọi asset vẫn optional và fallback an toàn.
