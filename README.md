# MCW Launcher

<p align="center">
  <strong>Minecraft launcher theo hướng instance-first, viết bằng Python và PySide6.</strong><br>
  Quản lý Minecraft, mod loader, mod, modpack và nội dung của từng instance trong một giao diện thống nhất.
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.4.0">
    <img src="https://img.shields.io/badge/Stable-v1.4.0-brightgreen" alt="Stable version">
  </a>
  <a href="https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.4.1-beta.2">
    <img src="https://img.shields.io/badge/Beta-v1.4.1--beta.2-orange" alt="Beta version">
  </a>
  <a href="https://github.com/mahiru7229/mcw-launcher/actions">
    <img src="https://img.shields.io/badge/Tests-passing-success" alt="Tests">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  </a>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D4" alt="Windows">
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52" alt="PySide6">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB" alt="Python 3.12+">
</p>

<p align="center">
  <a href="#giới-thiệu">Giới thiệu</a> ·
  <a href="#tính-năng-nổi-bật">Tính năng</a> ·
  <a href="#tải-và-cài-đặt">Tải xuống</a> ·
  <a href="#chạy-từ-source">Chạy source</a> ·
  <a href="#mcw-core">MCW Core</a>
</p>

---

## Giới thiệu

**MCW Launcher** là một Minecraft launcher mã nguồn mở dành cho Windows, được xây dựng xoay quanh mô hình **instance độc lập**.

Mỗi instance có riêng:

- Phiên bản Minecraft và mod loader.
- Mods, resource packs, shader packs và saves.
- Java runtime, RAM, JVM arguments và cấu hình cửa sổ.
- Trạng thái runtime, lịch sử launch, backup và dữ liệu repair.
- Metadata nguồn cho mod/modpack từ Modrinth, CurseForge, FTB hoặc ATLauncher.

Mục tiêu của dự án là tạo ra một launcher dễ kiểm soát, minh bạch khi tải file, an toàn khi sửa chữa và đủ linh hoạt cho cả người chơi Vanilla lẫn người dùng modpack.
---
Hỗ trợ nâng cấp trực tiếp: MCW Launcher v1.4.0 hỗ trợ nâng cấp trực tiếp từ v0.5.1 và tất cả các phiên bản phát hành sau đó.

---

## Có gì mới trong v1.4.1-beta.2

**v1.4.1-beta.2** sửa hai regression Windows phát hiện khi test beta.1: Java scan/Diagnostics có thể kích hoạt popup từ một Java `javaw.exe` bị hỏng, và managed Java extraction có thể tự va chạm với short-workspace vừa tạo. Bản này giữ nguyên toàn bộ Java recovery + Diagnostics v2.1 của beta.1.

- Java scan/version probe ưu tiên `java.exe` console khi candidate là `javaw.exe`, tránh JVM GUI dialog từ runtime bị gỡ dở/hỏng.
- Diagnostics Java scan dùng cùng probe an toàn, nên export bundle không còn bật popup JVM cho candidate lỗi kiểu này.
- Managed Java extraction dùng thư mục con chưa tồn tại trong short workspace, sửa `WinError 183` do extractor nhận chính workspace đã được tạo sẵn.
- Diagnostics alias riêng short workspace thành `temp/...`, tránh lộ user path trong lỗi Java extraction.

- Automatic Java 8 ưu tiên MCW-managed Temurin; Java 8 cũ trên `PATH` không còn chặn managed download/recovery.
- Java được user chọn explicit vẫn được tôn trọng nếu đúng major; recovery ưu tiên runtime managed rồi mới fallback external.
- Java download báo rõ stage metadata / download+SHA-256 / extract+install và lưu timeline quyết định recovery.
- Diagnostics v2.1 dùng path alias `root/...`, `temp/...`, `user/...`, `external/...`; không export drive letter hoặc UNC share name trực tiếp.
- Runtime/crash logs được sanitize thêm player/UUID, có metadata truncation; Forge/NeoForge installer logs và Java recovery timeline được đưa vào bundle.
- Collector diagnostics lỗi độc lập không làm hỏng cả ZIP; task cancellation từ Core được ghi `cancelled` thay vì `failed`.

Xem chi tiết tại [`docs/RELEASE-v1.4.1-beta.2.md`](docs/RELEASE-v1.4.1-beta.2.md).

## Có gì mới trong v1.4.0

**v1.4.0** là bản stable hợp nhất toàn bộ nhánh v1.4: task lifecycle/cancellation mới, **Kill Instance**, hardening Forge issue #20, Update Priority, tối ưu tải modpack/I/O, Diagnostics v2 + quy trình báo lỗi có hướng dẫn, và progress ownership để trạng thái task đồng thời không ghi đè lẫn nhau.

- Launcher có thể ưu tiên shutdown, cancel/drop task nền thay vì bắt người dùng chờ task metadata/scan hoàn tất.
- Task mới có thể replace/supersede task đọc nền; stale result không được cập nhật UI.
- Instance đang chạy có **Kill Instance** với confirmation và supervised process kill; user-killed session không bị báo nhầm là crash.
- Forge profile/cache được validate trước khi dùng, poisoned cache tự invalidate; regression khóa Forge 1.12.2 / 14.23.5.2860.
- **Update Priority Mode** hủy task không liên quan và dành scheduler cho update trước khi apply.
- Modrinth `.mrpack` dùng adaptive parallel download; multi-hash SHA-1/SHA-512/SHA-256 chạy một lượt đọc, có hash-I/O budget và performance profile.
- Diagnostics v2 thu thập launcher/runtime/loader log, hardware/Java/task timeline với privacy redaction; **Báo cáo lỗi** yêu cầu nhập thông tin trước rồi mới tạo bundle và hướng dẫn GitHub issue.
- Progress global có ownership/generation guard; cancel/supersede/success/failure cleanup nhất quán, Legacy Storage probe/scan/clean có terminal state đúng.
- Giữ toàn bộ filesystem/update-integrity hardening của v1.3.2, bao gồm fix issue #19.

Xem chi tiết tại [`docs/RELEASE-v1.4.0.md`](docs/RELEASE-v1.4.0.md).

## Có gì mới trong v1.4.0-beta.4

**v1.4.0-beta.4** là beta bổ sung tập trung vào tính nhất quán của progress/task state. Thanh tiến trình toàn cục giờ được reset khi task mới bắt đầu, không còn giữ `READY / 100% / detail` của task trước; kết quả của task cũ hoàn tất muộn không được phép ghi đè task mới; cancel/supersede cũng đi qua cùng đường cleanup busy/progress như success/failure. Legacy Storage probe/scan/cleanup có terminal progress riêng để thao tác bỏ qua hoặc dọn dữ liệu phản ánh đúng trạng thái.

Beta.4 giữ toàn bộ TaskRunner/Kill Instance/Forge hardening, download performance, Update Priority và Diagnostics v2 từ beta.1–beta.3.

Xem chi tiết tại [`docs/RELEASE-v1.4.0-beta.4.md`](docs/RELEASE-v1.4.0-beta.4.md).

## Có gì mới trong v1.4.0-beta.3

**v1.4.0-beta.3** tập trung vào Diagnostics v2 và quy trình báo lỗi. Nút **Báo cáo lỗi** mở màn hình nhập thông tin trước, sau đó launcher thu thập diagnostics ở background và mới hiện hướng dẫn tạo GitHub issue/đính kèm ZIP. Bundle mới bổ sung system info, Java runtime, task timeline, runtime/crash logs gần nhất và issue context đã lọc thông tin nhạy cảm.

Beta.3 giữ toàn bộ TaskRunner/Kill Instance/Forge hardening từ beta.1 và adaptive download/Update Priority từ beta.2.

Xem chi tiết tại [`docs/RELEASE-v1.4.0-beta.3.md`](docs/RELEASE-v1.4.0-beta.3.md).

## Có gì mới trong v1.4.0-beta.1

**v1.4.0-beta.1** mở nhánh v1.4 với nền tảng task lifecycle/shutdown mới, **Kill Instance** cho Minecraft đang chạy và fix Forge profile/cache cho issue #20. Background/network task có thể bị cancel hoặc supersede thay vì luôn chặn task mới; khi đóng launcher, launcher ưu tiên hủy work của chính nó và thoát mà không tự kill game đang chạy.

- Cooperative cancellation token + `REPLACE` policy cho request nền/network.
- Shutdown không còn bị task metadata/scan chậm giữ cửa sổ lại.
- Instance Workspace đổi **Launch → Kill Instance** khi game đang chạy, có cảnh báo trước force-kill.
- User-killed session không bị báo nhầm thành crash.
- Forge installer/profile cache không còn fallback sang vanilla profile; poisoned cache tự invalidated.
- Regression riêng cho Forge 1.12.2 / 14.23.5.2860.

Ba beta v1.4 được chia theo dependency: beta.1 = lifecycle/runtime stability; beta.2 = modpack download/I/O performance; beta.3 = Diagnostics v2 + Create Issue Report + polish/benchmark.

Xem chi tiết tại [`docs/RELEASE-v1.4.0-beta.1.md`](docs/RELEASE-v1.4.0-beta.1.md).

## Có gì mới trong v1.3.2

**v1.3.2** là bản stability/security update tập trung vào filesystem race trên Windows và hardening auto-update. Bản này xử lý lỗi `WinError 32` được ghi nhận ở issue #19 khi background version refresh và launch cùng ghi `version_manifest_v2.json.tmp`, đồng thời áp cùng atomic-write boundary cho instance registry/metadata quan trọng.

- Atomic text writer dùng temp file riêng theo operation, `os.replace()` có retry cho sharing violation và cleanup best-effort.
- `cleanup_short_workspace()` canonicalize đường dẫn trước khi recursive delete, chặn `..` escape và chặn xoá chính short-workspace root.
- Auto-update yêu cầu SHA-256 tin cậy: dùng GitHub asset digest hoặc `<archive>.sha256`; không còn fallback sang unverified ZIP.
- Update package bắt buộc `mcw-update.json` và khai báo managed files để updater v1.3.2+ có thể loại bỏ file release cũ có kiểm soát, kèm rollback.
- Modpack archive path validation dùng chung Windows-safe policy với MCW package importer.
- Theme overwrite import có rollback nếu bước publish cuối thất bại.
- Release preflight kiểm tra stale release evidence và dependency boundary `src.gui -> src.core`.
- Test long-path short-workspace cũ đã được đổi tên để pytest thực sự collect.

Xem chi tiết tại [`docs/RELEASE-v1.3.2.md`](docs/RELEASE-v1.3.2.md).

## Có gì mới trong v1.3.1

**v1.3.1** là hotfix tương thích Windows cho các installation đặt launcher trong đường dẫn sâu. Các bước Java extraction, Forge/NeoForge installer staging và Modrinth staging dùng short workspace dưới `%LOCALAPPDATA%\MCW\t` với prefix dễ đọc (`jvm`, `frg`, `neo`, `mrd`, `cfr`), đồng thời extraction/copy boundary hỗ trợ Windows extended paths.

Hotfix này nhắm trực tiếp hai failure đã quan sát trên Windows 10 khi path cũ chạm khoảng 260 ký tự: Temurin Java 8 `DirectoryScannerConfig.java` và Modrinth `zlm_arab.json`. Permanent launcher data vẫn ở vị trí người dùng chọn; short workspace chỉ tồn tại trong quá trình cài đặt và được cleanup sau task.

Xem chi tiết tại [`docs/RELEASE-v1.3.1.md`](docs/RELEASE-v1.3.1.md).

## Có gì mới trong v1.3.0

**v1.3.0** đưa nhánh Shared Storage & Cache Lifecycle lên stable sau ba bản beta và bổ sung các hardening cuối cho cleanup trên installation thật:

- Shared `ContentStore`, hardlink/reuse cho managed immutable content và cleanup Forge/NeoForge staging giúp hạn chế physical duplicate khi cài thêm modpack.
- Legacy Storage Cleanup có preview item/path/reason/category, tổng dung lượng thực có thể giải phóng và revalidation ngay trước khi xóa.
- Có thể đặt **số ngày giữ Minecraft version JAR không dùng** trong Launcher Settings (mặc định 14 ngày, 1–365 ngày).
- Cleanup phát hiện các **thư mục instance cũ bị xóa dở** chỉ còn `.mcw` / `crash-reports`, nhưng chỉ khi không còn `instance.json` hoặc registry reference.
- Storage scan có progress lifecycle riêng, không còn giữ nhầm 100%/detail của task Update Check trước đó.
- Provider API Cache vẫn được tách và bảo vệ độc lập với binary Content Store.
- Instance deletion race của Beta 2 và reference-aware unused version JAR cleanup của Beta 3 được giữ nguyên.

Xem chi tiết tại [`docs/RELEASE-v1.3.0.md`](docs/RELEASE-v1.3.0.md).

## Có gì mới trong v1.3.0-beta.3

**v1.3.0-beta.3** bổ sung cleanup an toàn cho Minecraft version JAR không còn được instance nào sử dụng. Launcher chỉ đề xuất xóa `cache/versions/<version>/<version>.jar` sau khi reference graph xác nhận version không còn được dùng trực tiếp hoặc qua loader inheritance; metadata JSON vẫn được giữ để có thể tải lại khi cần.

- Không xóa cả thư mục version.
- Giữ mọi version đang được Vanilla/Forge/NeoForge/Fabric/Quilt sử dụng.
- Sửa reference mapping profile Fabric/Quilt theo đúng tên thư mục thực tế.
- Item/path/reason/dung lượng từng JAR và tổng reclaimable vẫn hiện trong Storage Cleanup trước khi xác nhận.
- Provider API Cache và phần Shared Storage đã ổn định ở Beta 1/2 không thay đổi.

Xem chi tiết tại [`docs/RELEASE-v1.3.0-beta.3.md`](docs/RELEASE-v1.3.0-beta.3.md).

## Có gì mới trong v1.3.0-beta.2

**v1.3.0-beta.2** sửa race condition khi xóa instance vừa chạy game: runtime watcher không còn có thể tạo lại `.mcw` và `crash-reports` sau khi thư mục instance đã bị xóa. Launcher chờ runtime exit finalization hoàn tất trước khi xóa toàn bộ instance root; nếu finalization chưa thể kết thúc, thao tác được queue thay vì báo thành công giả.

Xem chi tiết tại [`docs/RELEASE-v1.3.0-beta.2.md`](docs/RELEASE-v1.3.0-beta.2.md).

## Có gì mới trong v1.3.0-beta.1

**v1.3.0-beta.1** mở đầu nhánh v1.3 với **Shared Storage & Cache Lifecycle**:

- Thêm SHA-256 `ContentStore` cho binary artifact được provider quản lý; ưu tiên NTFS hardlink vào instance và fallback copy khi cần.
- Forge/NeoForge installer staging reuse client/libraries đã có và được cleanup trên cả success lẫn failure thay vì tích tụ lâu dài.
- Tách rõ Provider API/metadata cache khỏi downloaded content; API cache tiếp tục được bảo vệ để giảm request mạng.
- Thêm Legacy Storage Migration/cleanup theo reference graph cho old staging, update packages, unused versions, unreferenced provider binaries và stale temp.
- Launcher Settings có thông báo legacy storage mặc định bật và nút **Review old storage**. Cleanup luôn hiển thị item/path/reason/category + tổng dung lượng vật lý có thể giải phóng trước khi người dùng xác nhận.
- Core revalidate selected candidates ngay trước khi xóa và báo actual reclaimed / removed / skipped / failures sau cleanup.

Xem chi tiết tại [`docs/RELEASE-v1.3.0-beta.1.md`](docs/RELEASE-v1.3.0-beta.1.md).

## Có gì mới trong v1.2.0

**v1.2.0** đưa Instance Manager 2.0 lên stable sau Beta 1–3 và RC.1–RC.2:

- Favorite / Group / Tags, search/filter/sort và Instance Overview tốt hơn.
- Unified Content Library với local import/drag-drop, ownership/pinned filters và provider metadata rõ ràng hơn.
- Version & Loader + Java Runtime UX trong Instance Editor, dựa trên public Core API.
- Giữ các fix RC cho overview formatting và release lock khi ổ đĩa hết dung lượng.
- Thêm logo **M xanh** chính thức cho Windows executable và Qt window/taskbar icon; release preflight kiểm tra icon trước build.
- Update channel chuyển về `stable`; distribution metadata là `mcw-core 1.2.0`.

Xem chi tiết tại [`docs/RELEASE-v1.2.0.md`](docs/RELEASE-v1.2.0.md).

## Release Candidate v1.2.0-rc.2

**v1.2.0-rc.2** tiếp tục feature-freeze và chỉ sửa hai lỗi tìm thấy khi smoke-test RC.1: Instance Overview hiển thị literal `\n`, và lỗi hết dung lượng bị hiểu nhầm thành manual-download pause khiến instance giữ preparing lock. RC.2 chuyển lỗi storage cục bộ thành terminal failure để task kết thúc, release lock và cho phép người dùng xóa/dọn instance ngay.

- Update channel vẫn là `beta` vì RC là prerelease.
- Build release bằng `python -m tools.release_preflight` rồi `.\build_release.ps1`.
- Checklist EXE bao gồm startup one-file, Microsoft login, instance lifecycle, các loader, ATM9/SkyFactory 5/RLCraft, Java Runtime UX, Installed Content Library và process recovery.

Xem chi tiết tại [`docs/RELEASE-v1.2.0-rc.2.md`](docs/RELEASE-v1.2.0-rc.2.md).

## Có gì mới trong v1.2.0-beta.3

**v1.2.0-beta.3** mở rộng Instance Manager 2.0 với Component/Runtime UX:

- Instance Editor hiển thị riêng Minecraft, mod loader/version và Java requirement; loader repair được đưa ra ngay trang Version & Loader.
- Thêm trang Java Runtime với Automatic/custom selection, scan Java và cài managed Java tương thích ngay trong instance.
- Custom Java được Core kiểm tra path + major version + compatibility và bị chặn thay đổi khi Minecraft đang chạy.
- Thêm public `InstanceRuntimeProfile`, giữ GUI không đọc trực tiếp internal version/settings files.
- Minecraft version vẫn read-only trong Beta 3 để tránh phá curated modpack hoặc mod set hiện tại.

Xem chi tiết tại [`docs/RELEASE-v1.2.0-beta.3.md`](docs/RELEASE-v1.2.0-beta.3.md).

## Có gì mới trong v1.2.0-beta.2

**v1.2.0-beta.2** mở rộng Unified Content Management cho từng instance:

- Thêm trực tiếp hoặc kéo-thả local mods (`.jar`), resource packs và shader packs (`.zip`) từ Installed Content Library; chế độ All types có thể tự nhận diện loại nội dung.
- Thêm filter User-added / Modpack-managed, Pinned only và bộ đếm số item đang hiển thị để quản lý modpack lớn dễ hơn.
- Có thể mở manager/thư mục theo loại nội dung đang filter ngay cả khi danh sách hiện tại trống.
- Local mod import dọn tracking provider cũ theo filename, provider filter có ATLauncher và CurseForge entries có fallback project URL tốt hơn.
- Không thay đổi dependency resolver, loader pipeline hoặc modpack lifecycle đã ổn định.

Xem chi tiết tại [`docs/RELEASE-v1.2.0-beta.2.md`](docs/RELEASE-v1.2.0-beta.2.md).

## Có gì mới trong v1.2.0-beta.1

**v1.2.0-beta.1** mở đầu nhánh feature v1.2 với nền tảng **Instance Manager 2.0**:

- Thêm metadata thư viện cho từng instance: **Favorite**, **Group** và **Tags**; dữ liệu được lưu ngay trong `instance.json` và tương thích ngược với instance v1.1.2.
- Instance library có bộ lọc theo group, chỉ hiện favorites, tìm kiếm theo group/tag và sắp xếp theo tên, lần chơi gần nhất hoặc Minecraft version.
- Favorites luôn được ưu tiên trong danh sách và hiển thị dấu sao trực tiếp trên card instance.
- Context menu cho phép thêm/bỏ favorite, đặt group và chỉnh tags mà không phải sửa file metadata thủ công.
- Instance overview hiển thị group, tags và trạng thái favorite cùng Minecraft version, loader và health hiện có.
- Không thay đổi dependency resolver, modpack lifecycle hoặc launch pipeline của v1.1.2 trong beta này.

Xem chi tiết tại [`docs/RELEASE-v1.2.0-beta.1.md`](docs/RELEASE-v1.2.0-beta.1.md).

## Có gì mới trong v1.1.2

**v1.1.2** đưa toàn bộ nhánh hardening dependency/modpack lên stable:

- Scope dependency theo active loader, giữ manifest authority cho modpack và không còn false blocker do metadata Fabric/Forge/NeoForge bị trộn.
- Nhận diện embedded/JarJar capabilities, bao gồm dependency lồng như `expandability`, mà không tải JAR standalone trùng.
- Phân biệt primary mod ID với provided/embedded capability để loại false `Duplicate enabled mod ID`, đồng thời vẫn phát hiện duplicate top-level thật.
- Cải thiện Forge/Maven version matching, safe cleanup cho stale dependency do launcher quản lý và giảm warning preflight không actionable.
- Tối ưu download modpack lớn, dependency progress và cài Fabric/Quilt/Forge/NeoForge với bounded concurrency, cache reuse và retry mạng giới hạn.
- Đọc tolerant `mcmod.info` legacy có thể salvage và hỗ trợ manual CurseForge/Modrinth dependency theo flow pause → import nhiều file → revalidate → resume cùng launch session.
- Hotfix cuối loại deadlock khiến manual batch bị kẹt ở `Task ... is already running` khi launch đang pause.

Các fix dependency đã được runtime kiểm tra thành công với SkyFactory 5 và All The Mods 9 trong chu kỳ beta.

Xem chi tiết tại [`docs/RELEASE-v1.1.2.md`](docs/RELEASE-v1.1.2.md).

## Có gì mới trong v1.1.1

**v1.1.1** đưa toàn bộ nhánh dependency và tương thích Forge legacy lên stable:

- Hoàn thiện dependency bắt buộc cho Modrinth, CurseForge và ATLauncher, bao gồm dependency nhiều tầng, manual download và provider bridge theo hash.
- Nhận diện dependency được cung cấp qua Forge JarJar, nested JAR và identity CurseForge đã xác minh bằng SHA-1.
- Hỗ trợ đúng thư mục mod legacy `mods/<minecraft-version>/`, metadata `mcmod.info` nhiều mod ID và file do modpack ghim.
- Không tải lại file manual đã import, không biến lỗi parser legacy thành trạng thái file thiếu và không chạy lại Forge installer khi cache hợp lệ.
- Sửa so sánh Maven/Forge range có thành phần chữ, ví dụ `0.6.10` khớp `[0.6.8.a,0.7)`.
- Bao gồm ATLauncher provider và luồng nhập OptiFine trực tiếp của nhánh v1.1.1.

Đã smoke test thành công với SkyFactory 3 (Forge 1.10.2) và RLCraft (Forge 1.12.2).

Xem chi tiết tại [`docs/RELEASE-v1.1.1.md`](docs/RELEASE-v1.1.1.md).

## Có gì mới trong v1.1.1-beta.5

**v1.1.1-beta.5** sửa pipeline dependency bắt buộc của modpack:

- Tự hoàn thiện dependency graph `required` cho modpack Modrinth và CurseForge trước khi Minecraft được tạo process.
- Giữ nguyên file do tác giả pack ghim; dependency bổ sung được ghi `requiredBy` và `selectionReason`.
- Không tự tải optional/embedded dependency và không tự thay file pack chỉ vì metadata system version quá chặt.
- Tùy chọn chạy dù có lỗi tương thích không còn được phép bỏ qua dependency bắt buộc bị thiếu, disable hoặc sai version.
- Repair modpack chạy lại resolver và tải các dependency mới tìm được.
- Registry Modrinth, CurseForge và provenance được nâng schema với normalize tương thích dữ liệu cũ.

Xem chi tiết tại [`docs/RELEASE-v1.1.1-beta.5.md`](docs/RELEASE-v1.1.1-beta.5.md).

## Có gì mới trong v1.1.1-beta.4

**v1.1.1-beta.4** đơn giản hóa OptiFine thành luồng nhập file trực tiếp:

- Không còn tải hoặc hiển thị danh sách phiên bản OptiFine trực tuyến.
- Chọn JAR OptiFine gốc; MCW nhận diện Minecraft version và build từ tên file.
- Chặn file sai Minecraft version trước khi tạo hoặc cài instance.
- Vanilla dùng standalone component/profile; Forge instance hoặc modpack dùng mod được quản lý trong `mods/`.
- Core vẫn xác minh cấu trúc JAR, manifest, class OptiFine và hash trước khi commit.
- Giữ nguyên Repair, Uninstall, rollback giao dịch và chính sách không nhúng OptiFine vào export.

Xem chi tiết tại [`docs/RELEASE-v1.1.1-beta.4.md`](docs/RELEASE-v1.1.1-beta.4.md).

## Có gì mới trong v1.1.1-beta.2

**v1.1.1-beta.2** là hotfix cho một số modpack Forge 1.12.2 dùng LibLoader và còn phụ thuộc vào thư viện từng được lưu trên JCenter:

- Xác định lỗi không liên quan tới tên thư mục instance hoặc hậu tố `(2)`; Forge đã nhận đúng game directory trước khi coremod tải dependency thất bại.
- Quét manifest `LibLoader-*` trong các mod JAR trước khi Java khởi chạy.
- Khôi phục dependency còn tồn tại trên Maven Central và dùng fallback giới hạn cho sáu thư viện JCenter-only đã biết.
- Mọi file tải hoặc trích xuất đều phải khớp SHA-512 do chính manifest của mod khai báo.
- Giữ đúng cấu trúc thư mục `libraries/` mà LibLoader sử dụng, bao gồm thư mục có suffix hash cho snapshot build.
- Không tự tải từ host tùy ý; dependency custom chưa được nhận diện vẫn được để cho mod xử lý như trước.
- Bao gồm toàn bộ ATLauncher provider của Beta 1; chưa phát hành MCW Core wheel mới.

Xem chi tiết tại [`docs/RELEASE-v1.1.1-beta.2.md`](docs/RELEASE-v1.1.1-beta.2.md).

## Có gì mới trong v1.1.1-beta.1

**v1.1.1-beta.1** mở đầu tích hợp ATLauncher:

- Thêm browser ATLauncher trong Add Instance và workspace của instance.
- Tìm kiếm pack công khai qua V2 GraphQL, với V1/CDN fallback cho metadata và manifest cài đặt.
- Chọn version, kênh release/beta/alpha và các file tùy chọn được khuyến nghị trước khi tạo instance.
- Tải file pack ở lần Launch đầu tiên, có retry giới hạn và xác minh SHA-1/MD5.
- Hỗ trợ Configs.zip với staging và kiểm tra an toàn đường dẫn.
- Pack dùng custom libraries, jar mods, extract/decomp hoặc browser-only files sẽ bị chặn rõ ràng trong beta này thay vì cài dở dang.
- Chưa phát hành Core wheel mới; ATLauncher được bundle trong launcher để smoke test trước khi đồng bộ Core stable.

Xem chi tiết tại [`docs/RELEASE-v1.1.1-beta.1.md`](docs/RELEASE-v1.1.1-beta.1.md).

## Có gì mới trong v1.1.0

**v1.1.0** đưa nhánh 1.1 lên stable với hai lớp bảo vệ cuối trước khi tạo và tải nội dung:

- Add Instance hiển thị danh sách phiên bản Fabric, Quilt, Forge hoặc NeoForge tương thích với Minecraft version đã chọn.
- Không thể tạo instance modded khi loader không có bản tương thích hoặc metadata chưa tải xong.
- CurseForge manual download ưu tiên trang file theo slug thay vì URL CDN vừa lỗi hoặc fallback project ID dễ dẫn tới 404.
- Bao gồm toàn bộ sửa lỗi của beta: Java tự phục hồi, retry mạng, responsive mod-loader UI, Forge legacy và progress bảo vệ tài khoản.
- MCW Core được phát hành đồng bộ dưới dạng `mcw-core 1.1.0`.

Xem chi tiết tại [`docs/RELEASE-v1.1.0.md`](docs/RELEASE-v1.1.0.md).

## Có gì mới trong v1.1.0-beta.4

**v1.1.0-beta.4** hoàn thiện cơ chế retry metadata khi mạng hoặc máy chủ gặp lỗi tạm thời:

- Tự động thử tối đa 3 lần với khoảng chờ 0,5 giây và 1 giây.
- Chỉ retry timeout, lỗi kết nối/DNS tạm thời, rate limit và các lỗi máy chủ có khả năng phục hồi.
- Không retry lỗi validation, loader không hỗ trợ, xác thực hoặc các HTTP client error vĩnh viễn.
- Sau khi ba lần tự động thất bại, hiển thị hộp thoại **Thử lại/Hủy**.
- Nút Thử lại chạy lại đúng tác vụ và tham số trước đó, bắt đầu một vòng retry giới hạn mới.
- Ngăn task trùng, giới hạn số task được ghi nhớ và lọc dữ liệu nhạy cảm khỏi lỗi hiển thị/log.
- Áp dụng cho Minecraft manifest, metadata mod loader, Modrinth, CurseForge, FTB, resource pack và shader pack.
- Không thay đổi triển khai MCW Core và không phát hành wheel mới; distribution dùng để build vẫn là `1.1.0b2`.

Xem chi tiết tại [`docs/RELEASE-v1.1.0-beta.4.md`](docs/RELEASE-v1.1.0-beta.4.md).

## Có gì mới trong v1.1.0-beta.3

**v1.1.0-beta.3** hoàn thiện luồng quản lý mod loader và dọn lại cửa sổ quản lý instance nâng cao:

- Cửa sổ quản lý nâng cao có thể thay đổi kích thước và phù hợp hơn với màn hình nhỏ hoặc Windows display scaling.
- Hai trường Mod loader và Loader version tự chuyển từ bố cục ngang sang dọc khi chiều rộng bị thu hẹp.
- Các nút thao tác tự sắp xếp thành 3, 2 hoặc 1 cột để tránh tràn giao diện.
- Combo box phiên bản loader có thể co lại khi tên phiên bản dài.
- Xóa toàn bộ form tạo instance khỏi khu vực quản lý nâng cao; việc tạo instance chỉ còn ở luồng Add Instance chính.
- Giữ nguyên luồng tạo instance và cài modpack hiện có trong Create Instance Dialog.
- Thêm regression test cho responsive layout và ranh giới giữa Create Instance với Manage selected instance.
- Không có thay đổi triển khai MCW Core và không phát hành wheel mới; distribution dùng để build vẫn là `1.1.0b2`. Runtime `mcw_core.__version__` tiếp tục theo metadata launcher dùng chung.

Xem chi tiết tại [`docs/RELEASE-v1.1.0-beta.3.md`](docs/RELEASE-v1.1.0-beta.3.md).

## Có gì mới trong v1.1.0-beta.2

**v1.1.0-beta.2** chỉ tập trung vào lựa chọn và tự phục hồi Java cho từng instance:

- Thêm chế độ chọn Java rõ ràng: **Tự động** hoặc **Đường dẫn file thực thi tùy chọn**.
- Áp dụng cùng một lựa chọn cho trang Instance Settings và trình chỉnh sửa thiết lập mặc định của instance.
- Kiểm tra đường dẫn Java tùy chọn trước khi lưu và trước khi launch.
- Nếu Java tùy chọn bị thiếu hoặc không tương thích, launcher tự chọn Java phù hợp và chuyển instance về chế độ Tự động sau khi phục hồi thành công.
- Nếu Java đã chọn thoát ngay với dấu hiệu lỗi runtime/phiên bản, launcher thử lại một lần bằng Java tương thích khác hoặc Java do launcher quản lý.
- Nếu không thể tìm hoặc cài Java thay thế, launcher dừng an toàn và hiển thị lỗi rõ ràng thay vì tiếp tục với runtime sai.
- Giữ lại log của lần launch Java thất bại khi retry xảy ra trong cùng một giây.
- Các mục responsive cài mod loader, retry mạng, Forge legacy và progress bảo vệ tài khoản vẫn dành cho các beta sau.

Xem chi tiết tại [`docs/RELEASE-v1.1.0-beta.2.md`](docs/RELEASE-v1.1.0-beta.2.md).

## Có gì mới trong v1.0.2

**v1.0.2** là hotfix dành cho cơ chế khởi động lại launcher sau khi đổi ngôn ngữ. Bản EXE one-file giờ tạo một tiến trình PyInstaller độc lập thay vì tái sử dụng thư mục giải nén tạm của tiến trình cũ. Điều này ngăn lỗi khởi động lại thiếu module PySide6 sau khi launcher hiện thông báo đổi ngôn ngữ.

- Khởi động lại đúng chính file `MCW Launcher.exe` ở bản đóng gói.
- Thiết lập `PYINSTALLER_RESET_ENVIRONMENT=1` chỉ cho tiến trình thay thế.
- Không làm thay đổi môi trường của launcher đang chạy.
- Chạy source vẫn dùng Python hiện tại cùng `launcher.py`.
- Có regression test cho frozen mode, command, environment và lỗi spawn.
- Không thay đổi dữ liệu instance, tài khoản, theme, language pack hoặc provider.

Xem chi tiết tại [`docs/RELEASE-v1.0.2.md`](docs/RELEASE-v1.0.2.md).

## Có gì mới trong v1.0.1

**v1.0.1** là bản bảo trì đầu tiên sau mốc stable 1.0.0, tập trung vào độ chính xác của nội dung, trải nghiệm thiết lập ban đầu và tính nhất quán của giao diện:

- Sửa đường dẫn resource pack và shader pack về đúng thư mục gốc của instance, kèm migration an toàn cho dữ liệu được tạo bởi v1.0.0.
- Cho phép cài thêm resource pack/shader pack khi game đang chạy, nhưng vẫn chặn thao tác thay thế, vô hiệu hóa hoặc xóa nội dung đang có.
- Sắp xếp phiên bản FTB từ mới nhất đến cũ nhất.
- Mở rộng First Run Setup với quét Java, chọn runtime mặc định, gợi ý RAM, download concurrency và tóm tắt cấu hình.
- Thêm chính sách xác nhận lỗi tương thích theo từng instance: Kế thừa, Hỏi, Chặn hoặc Cho phép.
- Khôi phục icon modpack từ archive hoặc provider theo cơ chế best-effort.
- Thêm màu chữ tùy chỉnh cho Launcher Settings và theme contract, có preview, reset và kiểm tra độ tương phản.
- Làm gọn card GPU rời, hoàn thiện bản dịch, dùng file picker native trên Windows và gia cố repaint khi cuộn.
- Sửa live language reload sau First Run Setup, thêm nút chạy lại wizard và dịch toàn bộ progress động theo ngôn ngữ launcher.

Xem chi tiết tại [`docs/RELEASE-v1.0.1.md`](docs/RELEASE-v1.0.1.md).

## Tính năng nổi bật

### Quản lý instance

- Tạo, đổi tên, clone, xóa, import và export instance.
- Hỗ trợ **Vanilla, Fabric, Quilt, Forge và NeoForge**.
- Thư viện instance dạng icon với tìm kiếm, trạng thái runtime và thao tác nhanh.
- Mỗi instance có Java, RAM, độ phân giải, fullscreen, JVM arguments và game arguments riêng.
- Run lock ngăn khởi chạy trùng cùng một instance.

### Tài khoản và khởi chạy

- Tài khoản Offline và Microsoft OAuth PKCE.
- Hỗ trợ nhiều tài khoản Microsoft.
- Bảo vệ dữ liệu nhạy cảm bằng Windows DPAPI.
- Theo dõi process Minecraft, exit code, crash state và game log.
- Pause, resume và cancel trong các bước tải được hỗ trợ.

### Mod và modpack

- Duyệt và cài mod/modpack từ **Modrinth** và **CurseForge**.
- Duyệt và cài modpack từ **FTB**.
- Trang chi tiết project có icon, mô tả, metadata, gallery, phiên bản và link web.
- Chọn Minecraft version, loader và release channel trước khi cài.
- Deferred download: cài modpack chỉ lưu manifest; mod được tải ở lần Launch đầu tiên.
- Giữ provenance của từng mod: provider, project ID, version/file ID, hash và modpack sở hữu.
- Manual-download fallback cho file không thể tải tự động.

### Import và export modpack

MCW Launcher hỗ trợ hai hướng import:

- **Duyệt trực tuyến** từ provider.
- **Import package native** như Modrinth `.mrpack`, CurseForge `.zip`, Provider Profile hoặc Portable MCWPack.

Hai chế độ export chính:

- **Provider Profile** — giữ nguyên package/reference của provider và chỉ thêm instance settings của MCW.
- **Portable MCWPack** — manifest portable với nguồn tải, hash, embedded file được phép và manual-download fallback.

Full/offline export vẫn có thể dùng cho backup hoặc chia sẻ riêng tư, kèm cảnh báo về giấy phép và chính sách phân phối.

### Resource pack và shader pack

- Duyệt từ Modrinth hoặc CurseForge.
- Cài, import file local, bật/tắt, gỡ và mở thư mục.
- Kiểm tra ZIP, `pack.mcmeta`, cấu trúc shader và archive security.
- Lưu metadata provider để phục vụ update và export sau này.

### Installed Content Library

- Xem modpack, mod, resource pack và shader pack trong một thư viện chung.
- Lọc theo loại, provider và trạng thái.
- Hiển thị `Ready`, `Disabled`, `Pending`, `Missing` hoặc `Broken`.
- Hỗ trợ thao tác hàng loạt, pin version và ignore update.
- Bảo vệ mod được quản lý bởi modpack khỏi việc xóa nhầm.

### Repair, backup và diagnostics

- Fast scan và full repair cho instance.
- Backup/restore `.mcwbackup`.
- Diagnostic bundle có redaction dữ liệu nhạy cảm.
- Cleanup file `.part`, stale session và trạng thái runtime cũ.
- Xác minh hash, size và rollback khi thao tác thất bại.

### Giao diện và trải nghiệm

- GUI PySide6 responsive, hỗ trợ DPI Windows.
- First Run Setup cho ngôn ngữ, cập nhật, Java, RAM và phần cứng.
- Tùy chọn ưu tiên dedicated GPU khi máy có GPU rời.
- Hỗ trợ tiếng Việt và English.
- Theme ngoài EXE, animation, custom font, accent color và text color.
- Navigation Back/Forward riêng, sidebar có thể thu gọn.

### LAN và multiplayer offline

- MCW LAN Agent cho các cấu hình được hỗ trợ.
- Profile Microsoft-only hoặc Microsoft + Offline friends.
- Tích hợp workflow e4mc/LAN theo từng instance.

---

## Tải và cài đặt

Tải bản Windows mới nhất tại:

**[GitHub Releases](https://github.com/mahiru7229/mcw-launcher/releases)**

Thông thường release sẽ có:

```text
MCW Launcher.exe
MCW-Launcher-v1.0.1-windows-x64.zip
MCW-Launcher-v1.0.1-windows-x64.zip.sha256
```

### Yêu cầu hệ thống

- Windows 10 hoặc Windows 11 64-bit.
- Kết nối Internet cho lần tải Minecraft, Java, loader, mod hoặc modpack đầu tiên.
- Dung lượng trống phù hợp với số instance, assets, mods và backups.

Java tương thích có thể được launcher tự phát hiện hoặc cài đặt.

---

## Bắt đầu sử dụng

1. Mở `MCW Launcher.exe`.
2. Hoàn thành **First Run Setup**.
3. Thêm tài khoản Offline hoặc Microsoft.
4. Nhấn **Thêm instance**.
5. Chọn tạo instance thường hoặc cài/import modpack.
6. Kiểm tra Java, RAM và setting của instance.
7. Nhấn **Launch**.

Ở lần chạy đầu tiên, launcher sẽ tải những file Minecraft hoặc mod còn thiếu rồi mới khởi chạy game.

---

## Chạy từ source

Python `3.12` trở lên được khuyến nghị.

```powershell
git clone https://github.com/mahiru7229/mcw-launcher.git
cd mcw-launcher

git switch main

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python launcher.py
```

---

## Kiểm thử

Chạy toàn bộ test suite:

```powershell
python -m pytest -q
```

Chạy release preflight:

```powershell
python -m tools.release_preflight
```

Một bản release chỉ nên được đóng gói khi:

- Không có test thất bại.
- Không có lỗi collection/runtime.
- Hai language pack có đủ key.
- Không còn merge marker.
- Metadata version và update channel chính xác.

---

## Build bản Windows

Chạy quy trình release tự động:

```powershell
.\build_release.ps1
```

Hoặc build EXE thủ công:

```powershell
python -m PyInstaller --clean --noconfirm mcw_launcher.spec
```

EXE được tạo tại:

```text
dist/MCW Launcher.exe
```

---

## MCW Core

Từ phiên bản 1.0.0, launcher có một core headless riêng dưới package:

```python
import mcw_core
```

MCW Core cung cấp API cho:

- Instance lifecycle.
- Launch lifecycle.
- Java management.
- Mod loader và modpack.
- Modrinth, CurseForge và FTB.
- Repair, backup và diagnostics.
- Progress, pause, resume và cancel.
- Portable package import/export.

Cài wheel:

```powershell
python -m pip install mcw-core==1.0.0
```

Tài liệu core nằm trong repository/package riêng:

- `README.md`
- `docs/QUICKSTART.md`
- `docs/API_OVERVIEW.md`
- `docs/USAGE.md`
- `docs/MIGRATION.md`
- `docs/CORE_ARCHITECTURE.md`

---

## Kiến trúc

MCW Launcher giữ GUI ở phía ngoài và chỉ giao tiếp qua public core API:

```text
PySide6 GUI
    ↓
mcw_core / mcw_core.api
    ↓
Domain services
    ↓
Filesystem · Network · Providers · Minecraft Runtime
```

GUI không nên trực tiếp:

- Truy cập database nội bộ.
- Tải file riêng ngoài Download Engine.
- Gọi private implementation của core.
- Xử lý authentication hoặc manifest provider một cách độc lập.

---

## Ngôn ngữ và theme

Language packs mặc định:

```text
lang/en-US.json
lang/vi-VN.json
```

Theme hỗ trợ:

- Palette và accent color.
- Text color tùy chỉnh.
- PNG assets và spritesheet animation.
- Custom font `.ttf` / `.otf`.
- Full, Reduced hoặc Off motion mode.
- Live reload và theme authoring tools.

Tài liệu theme:

- `docs/THEME_CREATION_GUIDE.md`
- `docs/THEME_ASSET_GUIDE.md`
- `docs/THEME_ANIMATION_GUIDE.md`
- `docs/THEME_MOTION_GUIDE.md`

---

## Cảnh báo phân phối modpack

> Người dùng có trách nhiệm bảo đảm việc chia sẻ, xuất bản hoặc lưu trữ modpack tuân thủ giấy phép của từng mod, quyền của tác giả và chính sách của provider. MCW Launcher không xác nhận hoặc khuyến khích việc phân phối lại trái phép.

Khi export công khai, nên ưu tiên:

- Provider Profile.
- Manifest/reference chính thức.
- File có license cho phép redistribution rõ ràng.
- Manual-download flow nếu quyền phân phối không rõ.

---

## Cấu hình CurseForge

MCW Launcher không còn đóng gói sẵn đường dẫn CurseForge gateway mặc định. Để sử dụng các tính năng CurseForge, hãy cấu hình gateway HTTPS riêng trong **Cài đặt launcher** hoặc qua biến môi trường được hỗ trợ. API key vẫn phải được giữ ở phía gateway và không được đưa vào launcher, source hoặc diagnostic bundle.

---

## Bảo mật

Vui lòng không đưa vào issue công khai:

- Microsoft access/refresh token.
- CurseForge API key.
- Cookie hoặc credential.
- Diagnostic bundle chưa kiểm tra.
- Đường dẫn hoặc dữ liệu cá nhân không cần thiết.

Khi báo lỗi, hãy dùng diagnostic bundle đã được launcher redaction và kiểm tra lại trước khi upload.

---

## Đóng góp

Issue và pull request đều được chào đón.

Trước khi gửi PR:

```powershell
python -m pytest -q
python -m tools.release_preflight
```

Nên giữ:

- GUI phụ thuộc public `mcw_core` API.
- Progress thống nhất cho mọi tác vụ dài.
- en-US và vi-VN đầy đủ key.
- Test hồi quy cho bug được sửa.
- Không commit token, cache, instance cá nhân hoặc build output.

---

## Giấy phép

MCW Launcher được phát hành theo giấy phép **MIT**.

Minecraft, Microsoft, Mojang, Modrinth, CurseForge, FTB và các thương hiệu liên quan thuộc về chủ sở hữu tương ứng. MCW Launcher là dự án độc lập và không phải sản phẩm chính thức của các bên này.

---

## CurseForge configuration

MCW Launcher no longer bundles a default CurseForge gateway URL. CurseForge features require a user- or deployment-provided HTTPS gateway configured through Launcher Settings or the supported environment variables. API credentials must remain server-side and must not be embedded in the launcher.

---

## English summary

MCW Launcher is an open-source, Windows-focused, instance-first Minecraft launcher built with Python and PySide6. It supports Vanilla, Fabric, Quilt, Forge and NeoForge instances; Offline and Microsoft accounts; Modrinth, CurseForge and FTB modpacks; resource/shader packs; repair, backup, diagnostics, provider-native import, portable export, theming and a public headless `mcw_core` package.

Download the latest build from **[GitHub Releases](https://github.com/mahiru7229/mcw-launcher/releases)**.

### Language and theme authoring

Primary navigation and new UI surfaces use semantic translation keys. Changing the launcher language now prompts for a clean restart, preventing partially translated pages and dialogs. The machine-readable contract for future translation/theme tools is documented in `docs/LANGUAGE_THEME_EDITOR_CONTRACT.md`.


## Pytest test-module isolation

The launcher test suite uses pytest importlib mode. This prevents `import file mismatch`
errors when launcher and standalone core tests contain the same filename in different
directories. Core distribution tests also use a unique basename in the corrected 1.0.1
source package.
