# MCW Launcher v1.1.0-beta.3

## Tiếng Việt

### Phạm vi

Beta 3 chỉ hoàn thiện giao diện quản lý mod loader và tách rõ luồng tạo instance khỏi khu vực quản lý instance nâng cao. Bản này không thay đổi MCW Core.

### Thay đổi

- Cho phép cửa sổ **Quản lý instance nâng cao** thay đổi kích thước tự do với kích thước tối thiểu phù hợp cho màn hình nhỏ.
- Khu vực chọn **Mod loader** và **Loader version** tự chuyển giữa bố cục ngang và dọc theo chiều rộng khả dụng.
- Các nút áp dụng, sửa chữa, khôi phục và chẩn đoán loader tự sắp xếp thành 3, 2 hoặc 1 cột.
- Các thao tác rename, clone, delete, import, export và repair instance dùng cùng cơ chế reflow responsive.
- Combo box loader/version dùng kích thước nội dung tối thiểu và chính sách co giãn để tránh tạo thanh cuộn ngang.
- Giảm margin và khoảng cách trong chế độ hẹp.
- Xóa form tạo instance, chọn Minecraft version, snapshot và lựa chọn mod loader khi tạo mới khỏi trang quản lý nâng cao.
- Giữ luồng tạo instance tại nút **Add Instance** và `CreateInstanceDialog`.
- Cập nhật bản dịch mô tả để trang nâng cao chỉ nói về instance đang được chọn.
- Thêm regression test cho bố cục rộng, trung bình và hẹp; kiểm tra form tạo instance không quay lại trang quản lý nâng cao.

### Phiên bản

- Launcher runtime: `v1.1.0-beta.3`
- Update channel: `beta`
- MCW Core implementation/wheel: không thay đổi; distribution dùng để build vẫn là `1.1.0b2` (runtime version theo metadata launcher dùng chung)

### Xác thực

- `1292 passed, 79 skipped, 2 warnings`.
- Toàn bộ source và test đã qua `compileall`.
- Các GUI regression test mới được thu thập nhưng bị skip trong môi trường đóng gói hiện tại vì không cài PySide6; cần smoke test trực tiếp trên Windows cho resize/display scaling.

### Không nằm trong Beta 3

- Retry metadata/download khi lỗi mạng.
- Sửa Forge legacy trùng singleton argument như `--gameDir`.
- Sửa progress của kiểm tra bảo vệ tài khoản.

---

## English

### Scope

Beta 3 only finalizes the mod-loader management interface and separates instance creation from advanced instance management. This release does not change MCW Core.

### Changes

- Makes the **Advanced Instance Management** window freely resizable with a compact minimum size.
- Reflows the **Mod loader** and **Loader version** fields between horizontal and vertical layouts based on available width.
- Reflows loader action buttons into three, two, or one column.
- Applies the same responsive action grid to rename, clone, delete, import, export, and instance repair actions.
- Lets loader/version combo boxes shrink without forcing horizontal overflow.
- Reduces margins and spacing in compact mode.
- Removes the instance-name, Minecraft-version, snapshot, and new-instance loader controls from the advanced management page.
- Keeps instance creation in the main **Add Instance** flow and `CreateInstanceDialog`.
- Updates descriptions so the advanced page only refers to the currently selected instance.
- Adds regression coverage for wide, medium, and narrow layouts and for the create/manage boundary.

### Versioning

- Launcher runtime: `v1.1.0-beta.3`
- Update channel: `beta`
- MCW Core implementation/wheel is unchanged; the build distribution remains `1.1.0b2` (runtime version follows the shared launcher metadata)

### Validation

- `1292 passed, 79 skipped, 2 warnings`.
- All source and test files pass `compileall`.
- The new GUI regression tests are collected but skipped in the current packaging environment because PySide6 is not installed; perform a Windows smoke test for resize/display scaling.

### Not included in Beta 3

- Network retry for metadata/download failures.
- Forge legacy singleton-argument deduplication such as duplicate `--gameDir`.
- Account-protection progress reset fixes.
