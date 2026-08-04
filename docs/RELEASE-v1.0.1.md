# MCW Launcher v1.0.1

## Tiếng Việt

v1.0.1 là bản bảo trì đầu tiên của dòng stable 1.0. Bản cập nhật tập trung sửa dữ liệu nội dung được đặt sai vị trí, cải thiện thiết lập lần chạy đầu, làm rõ quyết định tương thích trước khi launch, hoàn thiện theme/bản dịch và gia cố giao diện trên Windows.

### Resource pack và shader pack

- Sửa thư mục cài đặt chuẩn thành `<instance>/resourcepacks` và `<instance>/shaderpacks`.
- Thêm migration an toàn cho dữ liệu v1.0.0 từng được đặt tại `<instance>/minecraft/resourcepacks` hoặc `<instance>/minecraft/shaderpacks`.
- Migration không ghi đè file trùng tên, có thể chạy lặp an toàn và cập nhật lại đường dẫn provenance đã lưu.
- Cho phép thêm resource pack hoặc shader pack mới khi Minecraft đang chạy.
- Khi instance đang chạy, launcher vẫn chặn thay thế file, đổi trạng thái, vô hiệu hóa hoặc xóa nội dung hiện có để tránh làm hỏng tài nguyên mà game có thể đang dùng.

### FTB và icon modpack

- Sắp xếp các phiên bản FTB từ mới nhất đến cũ nhất, ưu tiên thời gian cập nhật và dùng version ID làm fallback ổn định.
- Khi import `.mrpack` hoặc CurseForge/provider ZIP, launcher ưu tiên icon đã được đóng gói trong archive.
- Nếu archive không có icon và metadata xác định được provider project một cách đáng tin cậy, launcher thử tải icon project rồi gắn cho instance.
- Tải icon là best-effort: lỗi mạng, thiếu icon, metadata mơ hồ hoặc ảnh không hợp lệ không làm import thất bại.

### First Run Setup 2.0

- Mở rộng onboarding thành năm bước: ngôn ngữ/tải xuống, Java, RAM, graphics và xác nhận.
- Quét các Java installation hiện có và cho phép chọn runtime mặc định.
- Hiển thị tổng RAM, RAM khả dụng và mức phân bổ được đề xuất; cho phép chọn automatic hoặc giá trị cụ thể.
- Thêm download concurrency vào thiết lập ban đầu.
- Giữ tùy chọn GPU rời ở trạng thái tắt mặc định và chỉ bật điều khiển khi phát hiện dGPU phù hợp.
- Lỗi quét Java hoặc phần cứng không chặn launcher khởi động; wizard dùng fallback an toàn.

### Xác nhận lỗi tương thích

- Thêm chính sách lỗi tương thích ở cấp launcher và instance: **Kế thừa**, **Hỏi**, **Chặn**, **Cho phép**.
- Với lỗi dependency/version có thể bỏ qua, launcher có thể hỏi trước khi launch và cho phép chạy một lần hoặc ghi nhớ cho instance.
- Dialog nhắc rõ chính sách có thể được thay đổi trong Launcher Settings hoặc Instance Settings.
- Lỗi cứng như loader/runtime hỏng, thiếu file game cốt lõi, integrity/security failure hoặc archive không an toàn luôn bị chặn và không thể bypass.

### Theme, màu chữ và giao diện

- Thêm chế độ màu chữ **Theo theme** hoặc **Tùy chỉnh** trong Launcher Settings.
- Hỗ trợ preview trực tiếp, reset về theme và cảnh báo độ tương phản thấp.
- Mở rộng theme contract với màu chữ chính, muted, disabled và inverse; theme cũ tiếp tục dùng fallback tương thích.
- Không ghi đè các màu ngữ nghĩa như error, warning, success, link và selection.
- Làm gọn card GPU rời để chiều cao bám theo nội dung.
- Gia cố theme repaint/polish sau runtime reload và khi cuộn nhằm khắc phục nút bị ghost hoặc chỉ xuất hiện lại khi hover.
- Trên Windows, file/folder picker ưu tiên giao diện native của hệ điều hành.

### Bản dịch

- Dịch rõ các nút hành động chuẩn như **Lưu**, **Bỏ thay đổi**, **Hủy**.
- Bổ sung key cho tiêu đề trang, mô tả, First Run Setup, compatibility policy và text-color settings.
- Sửa chuỗi tiếng Anh còn sót trong các trang Instance, Account, Launcher Settings và các card kỹ thuật.
- Cải thiện live language reload cho page title, subtitle, combobox và nội dung động.


### Bản làm mới bản dịch và First Run Setup

- Sửa việc chọn ngôn ngữ trong First Run Setup nhưng cửa sổ launcher vẫn giữ ngôn ngữ cũ cho đến khi vào Cài đặt launcher. Sau khi hoàn tất wizard, toàn bộ cửa sổ, sidebar, page title, card và nội dung động được dịch lại ngay lập tức.
- Thêm nút **Chạy lại Thiết lập lần chạy đầu** trong Cài đặt launcher để người dùng xem lại Java, RAM, tải xuống và GPU mà không cần xóa file cấu hình.
- Sửa các chuỗi còn trộn tiếng Anh trong trang Tài khoản, Bảo mật tài khoản, kiểm tra file modpack, sidebar và trạng thái cập nhật.
- Đổi cách gọi thống nhất từ **Launcher Settings** thành **Cài đặt launcher** trong giao diện tiếng Việt.
- Progress bar giờ dịch cả stage, trạng thái và các message động có biến, ví dụ `Downloading Fabulously Optimized manifest...` được hiển thị thành `Đang tải manifest của Fabulously Optimized...`.
- Language runtime có thể nhận diện lại semantic key từ chuỗi đã render ở ngôn ngữ trước, kể cả chuỗi có placeholder, giúp live language reload ổn định hơn.

### Cấu hình CurseForge gateway

- Xóa đường dẫn CurseForge gateway mặc định khỏi `src/config.py`.
- CurseForge API và các public module vẫn được giữ nguyên.
- Người dùng hoặc bản phân phối launcher phải tự cấu hình gateway HTTPS trong Cài đặt launcher hoặc qua biến môi trường.
- Khi chưa cấu hình gateway, CurseForge được xem là chưa sẵn sàng thay vì tự động dùng endpoint do MCW cung cấp.

### Core 1.0.1

Bản launcher này đi kèm MCW Core 1.0.1. Public API mới hoặc mở rộng gồm:

- `FirstRunRecommendationService`
- `FirstRunRecommendation`
- `CompatibilityConfirmationRequired`
- `LaunchRequest.allow_compatibility_issues_once`
- `ManagedContentFailurePolicy.ASK`
- Các helper text palette và contrast
- Content-pack migration và running-instance safety policy

Ứng dụng bên ngoài chỉ nên import từ `mcw_core` hoặc `mcw_core.api.*`.

### Kiểm thử

- Full suite: **1274 passed, 74 skipped**.
- Hai warning đến từ test bảo mật cố ý tạo ZIP có duplicate member.
- Các kiểm thử GUI phụ thuộc Windows/PySide6 có thể bị skip trong môi trường headless; cần smoke-test native file picker, dGPU, DPI và scroll repaint trên Windows 10/11 trước khi phát hành EXE.

---

## English

v1.0.1 is the first maintenance release in the stable 1.0 line. It corrects content locations, expands first-run onboarding, introduces explicit compatibility decisions, completes theme/localization work, and hardens Windows UI behavior.

### Resource packs and shader packs

- Correct installation roots to `<instance>/resourcepacks` and `<instance>/shaderpacks`.
- Safely migrate v1.0.0 data from `<instance>/minecraft/resourcepacks` and `<instance>/minecraft/shaderpacks`.
- Never overwrite conflicts; migration is idempotent and normalizes stored provenance paths.
- Allow adding new packs while Minecraft is running.
- Continue blocking replacement, disable, rename, and removal operations while the instance is active.

### FTB and modpack artwork

- Sort FTB versions newest-first using update timestamps with stable version-ID fallback.
- Prefer artwork embedded in imported provider archives.
- When reliable provider metadata exists, retrieve the project icon as a best-effort fallback.
- Missing, ambiguous, invalid, or failed artwork requests never fail the import.

### First Run Setup 2.0

- Expand onboarding to language/downloads, Java, memory, graphics, and review pages.
- Scan installed Java runtimes and select a default runtime.
- Display total/available memory with a conservative recommendation and automatic/custom choices.
- Configure download concurrency during setup.
- Keep dedicated-GPU preference opt-in and enabled only when a supported dGPU is detected.
- Hardware/Java scan failures fall back safely and never block startup.

### Compatibility confirmation

- Add launcher and per-instance policies: **Inherit**, **Ask**, **Block**, and **Allow**.
- Bypassable dependency/version conflicts can prompt before launch, allow a one-time launch, or remember the instance choice.
- The dialog points users to Launcher Settings and Instance Settings for later changes.
- Broken loader/runtime files, core game integrity failures, unsafe archives, and security failures remain non-bypassable.

### Theme, text color, and UI

- Add theme/custom primary text-color mode with live preview, reset, and contrast warning.
- Extend the theme contract with primary, muted, disabled, and inverse text colors while preserving backward-compatible defaults.
- Keep semantic error/warning/success/link/selection colors independent.
- Compact the dedicated-GPU card.
- Harden runtime polish/repaint and scrolling to address ghosted controls.
- Prefer native Windows file/folder dialogs.

### Localization

- Fully localize standard actions including Save, Discard, and Cancel.
- Add missing keys for pages, onboarding, compatibility policy, and text-color controls.
- Remove mixed-language strings from Instance, Account, Launcher Settings, and technical cards.
- Improve live retranslation for page titles, subtitles, combobox items, and dynamic content.


### Localization and First Run Setup refresh

- Fix the case where choosing a language in First Run Setup left the main window in the previous language until Launcher Settings was opened. Completing the wizard now retranslates the whole window immediately.
- Add **Run First Run Setup again** to Launcher Settings so Java, memory, downloads, and GPU defaults can be reviewed without deleting the settings file.
- Remove remaining mixed-language strings from Accounts, account security, managed modpack checks, the sidebar, and update status.
- Localize progress stages and dynamic messages, including provider/modpack names embedded in progress text.
- Improve the language runtime so already-rendered strings from any installed language can be resolved back to their semantic key, including placeholder-based messages.

### CurseForge gateway configuration

- Remove the bundled default CurseForge gateway URL from `src/config.py`.
- Keep the CurseForge API and public modules available.
- Users or launcher distributions must provide their own HTTPS gateway through Launcher Settings or supported environment variables.
- Without an explicit gateway, CurseForge is reported as not configured instead of silently using an MCW-hosted endpoint.

### MCW Core 1.0.1

This launcher release ships with MCW Core 1.0.1. New or extended public APIs include:

- `FirstRunRecommendationService`
- `FirstRunRecommendation`
- `CompatibilityConfirmationRequired`
- `LaunchRequest.allow_compatibility_issues_once`
- `ManagedContentFailurePolicy.ASK`
- Text palette and contrast helpers
- Content migration and running-instance safety policies

External applications should import only from `mcw_core` or `mcw_core.api.*`.

### Validation

- Full suite: **1274 passed, 74 skipped**.
- Two warnings are produced by security tests that intentionally create duplicate ZIP members.
- Windows/PySide6 visual tests may be skipped in a headless environment; smoke-test native dialogs, dGPU behavior, DPI scaling, and scroll repaint on Windows 10/11 before publishing the EXE.

## Final language restart and semantic-key hotfix

- Language changes are now saved and applied through a clean launcher restart instead of attempting to mutate the entire live widget tree.
- MCW Launcher asks whether to restart immediately and keeps the current session language consistent when the restart is postponed.
- First Run Setup records the selected language without partially retranslating the already-running launcher.
- Primary navigation now stores semantic `navigation.*` keys rather than rendered English labels.
- `Launcher Settings` is consistently shown as `Cài đặt launcher` in Vietnamese.
- `Instance` remains unchanged as a domain term but is now guaranteed to use a translation key in every built-in language pack.
- Added a language/theme editor contract and release-preflight checks for navigation key coverage.


## Pytest collection hotfix

- Enabled `--import-mode=importlib` for the launcher test suite.
- Prevents duplicate test basenames in separate directories from resolving to the same
  Python module during pytest collection.
- The standalone core public-API test is also renamed to
  `test_core_distribution_public_api.py` in the corrected core source artifact.
- No launcher runtime behavior or public core API changed.
