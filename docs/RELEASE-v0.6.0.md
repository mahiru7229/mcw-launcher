# MCW Launcher v0.6.0

> Bản Stable đầu tiên của dòng 0.6, hoàn thiện luồng Vanilla/Fabric/Forge, Modrinth mods và modpacks, sửa chữa an toàn, giao diện responsive và trải nghiệm khởi động ổn định.

---

## Tiếng Việt

### Điểm nổi bật

- Tạo và chạy instance **Vanilla, Fabric và Forge**.
- Cài đặt, thay đổi, repair và khôi phục mod loader.
- Trang **Cài mod** độc lập chỉ hiển thị instance khớp Minecraft version và loader.
- Tìm, cài và cập nhật mod từ Modrinth.
- Cài `.mrpack`, kiểm tra update và repair file modpack bị thiếu hoặc bị thay đổi.
- Backup và rollback trước các thao tác update/repair quan trọng.
- Cache xác minh file để giảm thời gian quét lại modpack.
- RAM slider kèm ô nhập MB chính xác với ràng buộc an toàn theo RAM vật lý.
- Splash screen hiển thị rõ trạng thái khởi động và lưu báo cáo khi startup thất bại.
- Bố cục tự thích ứng với màn hình `1920×1080`, `1366×768` và các kích thước nhỏ hơn.
- Launcher và Qt dialog luôn dùng dark theme với chữ trắng.
- Lỗi kỹ thuật dài được giữ trong Logs; progress chỉ hiển thị thông báo ngắn.

### Theme

- **Show static text over themed controls** mặc định **tắt**.
- Khi theme khai báo PNG hợp lệ trong `text_assets`, chữ Qt tĩnh sẽ không đè lên artwork.
- Nếu PNG bị thiếu hoặc không hợp lệ, launcher tự hiện lại chữ fallback.
- Người dùng vẫn có thể bật lại tùy chọn này trong **Launcher Settings → Appearance**.
- Cài đặt đã được lưu rõ ràng từ phiên bản trước vẫn được giữ nguyên.

### Ngôn ngữ

Đã kiểm tra lại toàn bộ gói ngôn ngữ tích hợp:

- `en-US.json` và `vi-VN.json` có cùng **719 semantic key**.
- Không có bản dịch rỗng.
- Không có key tiếng Việt bị thiếu.
- Không có placeholder sai lệch như `{name}`, `{version}` hoặc `{path}`.
- Mọi chuỗi tĩnh GUI và mọi lời gọi dịch literal trong source đều resolve được qua semantic key hoặc alias tiếng Anh.

### Kênh cập nhật

```text
VERSION = v0.6.0
VERSION_ID = 0.6.0
UPDATE_CHANNEL = stable
```

- Người dùng thông thường ở kênh `stable`.
- Các bản thử nghiệm `0.7.x` chỉ xuất hiện khi người dùng chủ động tham gia tester program.
- Lựa chọn tester đã lưu của người dùng không bị ghi đè bởi bản phát hành này.

### Kiểm thử

```text
752 passed
46 skipped
0 failed
0 errors
```

Các test bị skip là nhóm GUI phụ thuộc môi trường PySide6 không khả dụng trong môi trường regression hiện tại.

---

## English

### Highlights

- Create and launch **Vanilla, Fabric and Forge** instances.
- Install, change, repair and restore mod loaders.
- A dedicated **Install Mods** page only lists instances matching the selected Minecraft version and loader.
- Search, install and update Modrinth mods.
- Install `.mrpack` modpacks, check for updates and repair missing or modified managed files.
- Create backups and roll back important update/repair operations.
- Reuse successful file verification results to reduce repeated modpack scans.
- Configure memory using sliders and exact MB inputs with physical-memory safety limits.
- Show startup progress through a splash screen and save a report when startup fails.
- Automatically adapt the layout for `1920×1080`, `1366×768` and smaller displays.
- Force a dark Qt interface with white text across the launcher and dialogs.
- Keep long technical errors in Logs while showing concise progress messages.

### Themes

- **Show static text over themed controls** is **disabled by default**.
- When a theme declares a valid PNG through `text_assets`, Qt static text no longer overlaps the artwork.
- Missing or invalid PNG assets automatically restore fallback text.
- Users can still enable the option under **Launcher Settings → Appearance**.
- Explicit settings saved by existing users remain preserved.

### Languages

The bundled language packs were audited before Stable:

- `en-US.json` and `vi-VN.json` contain the same **719 semantic keys**.
- No translation value is empty.
- No Vietnamese key is missing.
- No placeholder mismatch was found for fields such as `{name}`, `{version}` or `{path}`.
- Every static GUI string and literal translation call in source resolves through a semantic key or English alias.

### Update channel

```text
VERSION = v0.6.0
VERSION_ID = 0.6.0
UPDATE_CHANNEL = stable
```

- Regular users remain on the `stable` channel.
- Experimental `0.7.x` builds require explicitly joining the tester program.
- Existing tester choices are not overwritten by this release.

### Tests

```text
752 passed
46 skipped
0 failed
0 errors
```

Skipped tests are GUI/PySide6-dependent tests unavailable in the current regression environment.

---

## Release assets

Upload only the updater ZIP and checksum:

```text
MCW-Launcher-v0.6.0-windows-x64.zip
MCW-Launcher-v0.6.0-windows-x64.zip.sha256
```
