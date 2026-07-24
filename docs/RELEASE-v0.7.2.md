# MCW Launcher v0.7.2

## Tiếng Việt

`v0.7.2` là bản cập nhật Stable cho luồng đăng nhập Offline khi chạy Minecraft Forge.

### Sửa lỗi

- Tài khoản Offline không còn kích hoạt bất kỳ bước kiểm tra hoặc refresh Microsoft Authentication nào.
- Loại bỏ workaround cũ chuyển các dịch vụ xác thực Minecraft sang `nope.invalid`.
- Tự động gỡ bốn JVM property không an toàn khỏi command của tài khoản Offline, kể cả khi chúng còn sót trong cấu hình instance cũ hoặc Custom JVM Arguments.
- Forge không còn nhận trạng thái `Auth currently unreachable` do launcher chủ động làm hỏng địa chỉ dịch vụ xác thực.
- Danh tính launch Offline được dựng lại từ username ngay trước khi chạy: UUID dạng 32 ký tự không dấu gạch, access token `0`, user type `legacy`; `clientId` và `xuid` không còn được gửi.
- Launcher không tin UUID cũ trong database đối với tài khoản Offline, nhờ đó tự sửa các account từng lưu UUID sai hoặc UUID theo định dạng Microsoft.
- Các tham số identity trùng hoặc bị override trong Custom Game Arguments được loại bỏ và thay bằng đúng một bộ giá trị Offline chuẩn.
- Tùy chọn `offline_multiplayer_enabled` vẫn được đọc để tương thích cấu hình cũ nhưng không còn thay đổi auth host. Tài khoản Offline vẫn có thể tham gia server đặt `online-mode=false` mà không cần workaround này.

### Updater

- Phát hành theo phiên bản ba phần `0.7.2` để tương thích rõ ràng với kênh Stable.
- Bộ parser vẫn đọc được các phiên bản revision bốn phần cũ như `0.7.0.1`, nhưng release chính thức này không sử dụng định dạng đó.

### Kiểm tra khuyến nghị

- Tạo tài khoản Offline mới rồi chạy một instance Vanilla.
- Chạy Forge 1.20.1 bằng cùng tài khoản Offline.
- Chạy một instance cũ từng bật Offline Multiplayer Workaround.
- Xác nhận command không chứa `minecraft.api.*.host=https://nope.invalid`.
- Xác nhận command Forge dùng `--userType legacy`, UUID 32 ký tự và không chứa `--clientId`/`--xuid`.

---

## English

`v0.7.2` is a Stable maintenance update for the Offline account launch path on Minecraft Forge.

### Fixes

- Offline accounts no longer trigger any Microsoft authentication check or token refresh.
- Removed the legacy workaround that redirected Minecraft authentication services to `nope.invalid`.
- Automatically strips all four unsafe auth-host JVM properties from Offline launch commands, including values left in older instance settings or Custom JVM Arguments.
- Forge no longer receives an `Auth currently unreachable` state caused by launcher-provided invalid service endpoints.
- The Offline launch identity is rebuilt from the username immediately before launch: a compact 32-character UUID, access token `0`, and `legacy` user type; `clientId` and `xuid` are no longer sent.
- The launcher no longer trusts stale UUID values stored for Offline accounts, automatically repairing accounts that contain malformed or Microsoft-style UUID values.
- Duplicate or custom identity overrides in Custom Game Arguments are removed and replaced with one canonical Offline identity set.
- `offline_multiplayer_enabled` remains readable for settings compatibility but no longer rewrites auth hosts. Offline accounts can join servers configured with `online-mode=false` without this workaround.

### Updater

- Published as the conventional three-part Stable version `0.7.2`.
- The parser still accepts historical four-part revisions such as `0.7.0.1`, but this official release does not use that format.

### Recommended validation

- Create a new Offline account and launch a Vanilla instance.
- Launch Forge 1.20.1 with the same Offline account.
- Launch an older instance that previously enabled the Offline Multiplayer Workaround.
- Confirm the command contains no `minecraft.api.*.host=https://nope.invalid` properties.
- Confirm the Forge command uses `--userType legacy`, a compact 32-character UUID, and no `--clientId`/`--xuid`.
