# MCW Launcher v1.0.0-rc.1

## Tiếng Việt

RC 1 đóng băng phần lớn phạm vi tính năng của dòng 1.0 và tập trung vào trải nghiệm khởi động lần đầu, lựa chọn GPU cho máy dùng đồ họa lai, cùng độ hoàn thiện bản dịch.

### Thiết lập lần chạy đầu

- Hiện wizard ba bước ở lần chạy đầu tiên hoặc khi người dùng chưa hoàn tất onboarding.
- Cho phép chọn ngôn ngữ launcher, bật/tắt kiểm tra cập nhật tự động và xem trạng thái GPU được phát hiện.
- Mặc định **không bật** ưu tiên GPU rời.
- Nút ưu tiên GPU rời chỉ khả dụng khi launcher phát hiện một GPU hiệu năng cao được hỗ trợ.
- Có thể dùng thiết lập mặc định để hoàn tất nhanh; mọi lựa chọn vẫn chỉnh lại được trong Launcher Settings.
- Reset Launcher Settings không làm wizard xuất hiện lại nếu onboarding đã hoàn tất.

### Ưu tiên GPU rời

- Thêm setting **Ưu tiên GPU rời khi khởi chạy Minecraft** trong Launcher Settings.
- Phát hiện adapter đồ họa trên Windows mà không mở cửa sổ PowerShell.
- Khi bật, launcher áp dụng tùy chọn đồ họa hiệu năng cao cho Java runtime đang được dùng trước khi tạo tiến trình Minecraft.
- Đây là yêu cầu ưu tiên tới Windows; hệ điều hành và driver vẫn quyết định adapter cuối cùng.
- Lỗi phát hiện hoặc áp dụng GPU không chặn việc khởi chạy Minecraft.

### Hoàn thiện bản dịch

- Quét lại toàn bộ static GUI text, tooltip, status tip, tab, item và QMessageBox literal.
- Bổ sung các key/alias còn thiếu cho en-US và vi-VN.
- Mở rộng regression test để các chuỗi GUI mới không thể được thêm mà thiếu translation key.
- Hai language pack tiếp tục có cùng tập key và cùng placeholder.

## English

RC 1 freezes most of the 1.0 feature scope and focuses on first-run onboarding, hybrid-graphics preferences, and translation completeness.

### First Run Setup

- Show a three-step wizard on the first launch or until onboarding is completed.
- Let users choose the launcher language, automatic update checks, and review detected graphics hardware.
- Keep the dedicated-GPU preference **off by default**.
- Enable the dedicated-GPU toggle only when a supported high-performance adapter is detected.
- Allow a quick defaults path; every choice remains editable in Launcher Settings.
- Resetting Launcher Settings does not reopen onboarding after it has been completed.

### Dedicated GPU preference

- Add **Prefer the dedicated GPU when launching Minecraft** to Launcher Settings.
- Detect Windows graphics adapters without opening a PowerShell window.
- When enabled, apply the high-performance graphics preference to the selected Java runtime before Minecraft starts.
- Treat this as a Windows preference; the operating system and graphics driver retain final adapter selection.
- GPU detection or preference failures never block Minecraft launch.

### Translation completion

- Re-audit static GUI text, tooltips, status tips, tabs, item labels, and literal QMessageBox content.
- Fill the remaining en-US and vi-VN keys/aliases.
- Expand regression coverage so new literal GUI text cannot be added without a translation key.
- Keep both built-in language packs aligned with matching placeholders.
