# Changelog

Các thay đổi đáng chú ý của MCW Launcher được ghi tại đây. Dự án dùng semantic versioning cho version public; bản `alpha`, `beta` và `rc` có thể thay đổi API nội bộ.

## [1.8.3-beta.3] - 2026-10-17

### Added
- **Giới hạn Chơi nhanh (Quick Play) theo chuẩn Minecraft 1.20+**:
  - Tính năng Chơi nhanh (`Quick Play`) chỉ hỗ trợ chính thức từ Minecraft 1.20 trở lên (Mojang bổ sung từ snapshot 23w14a / release 1.20).
  - Tự động ẩn nút Chơi nhanh (`quick_play_button`) trên thanh điều khiển chính của `InstanceWorkspacePage` đối với các instance chạy phiên bản cũ hơn (< 1.20).
  - Tự động ẩn nút Chơi (`play_button`) trên từng thẻ thế giới (`WorldCardWidget`) thuộc tab Worlds nếu instance không hỗ trợ Quick Play.
  - Bộ xây dựng tham số game (`LauncherManager.build`) chủ động bỏ qua tham số `--quickPlaySingleplayer` / `--quickPlayMultiplayer` nếu phiên bản Minecraft chạy dưới 1.20.

### Changed
- **Cải thiện màn hình Loading (`StartupSplash`)**:
  - Chuyển cờ loại cửa sổ sang `Qt.WindowType.Window` tiêu chuẩn thay vì `Qt.WindowType.Tool`, loại bỏ hiện tượng bị hệ điều hành Windows tự động đẩy cửa sổ loading xuống layer đáy cùng (nằm sau mọi ứng dụng khác).
  - Tự động gọi `raise_()` khi hiển thị giúp màn hình loading luôn xuất hiện rõ ràng, dễ nhìn ở trung tâm màn hình trong lúc launcher khởi động.
  - Không gán cờ `WindowStaysOnTopHint`, cho phép người dùng thoải mái chuyển đổi cửa sổ và thao tác đa nhiệm với các ứng dụng khác mà không bị che khuất.

### Fixed
- **Cô lập hoàn toàn Hotfix trong môi trường Test tự động**:
  - Bổ sung kiểm tra `if "pytest" in sys.modules: return` trong các callback xử lý thông báo và modal restart của `HotfixManager` trong `MainWindow`, triệt tiêu hoàn toàn hiện tượng test runner bị treo chờ tương tác người dùng.
  - Làm sạch danh sách callbacks toàn cục `HotfixManager._on_applied_callbacks` trước và sau mỗi unit test.

## [1.8.3-beta.2] - 2026-10-17

### Added
- **Quản lý tài khoản trong First Run Setup**:
  - Hỗ trợ tạo tài khoản Offline và đăng nhập tài khoản Microsoft trực tiếp từ hộp thoại thiết lập ban đầu (`FirstRunSetupDialog`).
  - Đặt giá trị mặc định cho tùy chọn Java luôn là `Auto` (`first_run.java.auto`), bất kể trên hệ thống đã phát hiện bao nhiêu phiên bản Java.
  - Ngắt kết nối và tự động hủy tác vụ đăng nhập Microsoft an toàn khi đóng, bỏ qua hoặc hủy hộp thoại.
- **Bảo vệ thao tác lăn chuột (Wheel Guard)**:
  - Bổ sung `WheelBlockFilter` ngăn chặn việc vô tình thay đổi giá trị của các `QSpinBox`, `QComboBox`, `QSlider` khi cuộn trang cài đặt.

### Performance
- **Triệt tiêu hiện tượng đơ giao diện (UI Freezing) trên Instance Workspace**:
  - Caching `_hub_loaded_instance_key` trong `InstanceWorkspacePage`, không còn quét lại ổ đĩa cả 4 tab mỗi khi cập nhật tiến trình hoặc trạng thái instance.
  - Cơ chế Lazy-loading cho tab Screenshots, Live Logs, và Mods: chỉ quét ổ đĩa khi người dùng chủ động chuyển tab.
  - Quản lý `_poll_timer` của `InstanceLiveLogsTab` theo sự kiện ẩn/hiện (`hideEvent` / `showEvent`), ngừng đọc file nền khi ở tab khác.
- **Tối ưu hóa thao tác đọc đĩa `instance.json`**:
  - `InstanceService.list_health(instances=None)` và `InstanceController.refresh` tái sử dụng danh sách `instances` đã nạp, loại bỏ đọc lặp `instance.json`.

### Fixed
- **Cải thiện trải nghiệm Microsoft OAuth & Điều chỉnh giao diện**:
  - Khắc phục lỗi `NameError` khi mở `MicrosoftDeviceCodeDialog` và xử lý đúng modal parent khi mở từ các hộp thoại con.
  - Luôn khôi phục parent của `MicrosoftDeviceCodeDialog` về `MainWindow` khi kết thúc hoặc hủy phiên đăng nhập.
  - Căn chỉnh giao diện: tăng chiều cao nút Copy, thụt lề số thứ tự danh sách và hiển thị trọn vẹn tiêu đề ứng dụng.
  - Hỗ trợ ưu tiên phân giải IPv4 (`prefer_ipv4_dns`) trong `NetworkSession` để khắc phục lỗi timeout kết nối Microsoft trên mạng dual-stack IPv6.
  - Khôi phục `sys.path` và `sys.meta_path` sau mỗi test trong `test_hotfix_manager.py` đảm bảo tính cô lập của test suite.

## [1.8.3-beta.1] - 2026-10-16

### Added
- **Cơ chế Lazy-loading 17 hộp thoại chức năng (`QDialog`)**:
  - Chuyển đổi toàn bộ 17 modal dialog (quản lý mod, trình duyệt Modrinth/CurseForge/FTB/ATLauncher, content packs, repair center, v.v.) sang nạp động theo yêu cầu (on-demand).
  - Tự động hoàn thiện dịch thuật và gán asset (`_finalize_lazy_dialog`) khi hộp thoại được mở lần đầu.
  - Bổ sung helper `_allowed_modrinth_version_types()` đọc kênh phát hành trực tiếp từ cấu hình mà không cần khởi tạo `ModrinthBrowserDialog`.

### Performance
- **Tối ưu hóa mạnh mẽ thời gian khởi động lạnh (Cold launch time)**:
  - Rút ngắn thời gian khởi động launcher từ ~18.2 giây xuống còn ~1.61 giây (tăng tốc hơn 11 lần).
  - Trì hoãn việc kiểm tra bản vá Hotfix về background thread sau khi giao diện đã nạp xong kèm hộp thoại xác nhận.
  - Nạp trước stylesheet cơ sở trên `QApplication` ở tầng C++ và nhận diện card đồ họa (GPU) bất đồng bộ.
  - Loại bỏ các bước nạp trùng lặp Theme và reload từ điển ngôn ngữ trong quá trình khởi tạo ứng dụng.

### Fixed
- **An toàn luồng Qt Signals và bảo mật RPC**:
  - Thay thế các lệnh gọi `QTimer.singleShot` từ background worker thread sang cơ chế Qt Signals chuẩn luồng (`_mclogs_uploaded`, `hotfix_available`, `hotfix_failed`, `gpu_detected`).
  - Khắc phục lỗi `NameError` tại hộp thoại báo sự cố khởi động của launcher.
  - Tích hợp heartbeat `: keepalive\n\n` cho endpoint `/events` của máy chủ HTTP RPC chống ngắt kết nối sau 5 giây.
  - Tăng cường bảo vệ RPC cục bộ bằng bộ lọc Origin `_is_trusted_origin()`, từ chối các kết nối lạ bằng HTTP 403.
  - Chặn việc tra cứu thông tin mod trên `ModsPage` kích hoạt khởi tạo ngầm các modal dialog.

## [1.8.2] - 2026-10-15

### Fixed
- **Hỗ trợ MCW LAN Agent cho các phiên bản Minecraft thấp hơn (xuống tới 1.14+)**:
  - Mở rộng phạm vi hỗ trợ của `LanAgentTargetResolver` từ 1.17+ xuống 1.14.0+ (hỗ trợ đầy đủ Minecraft 1.14, 1.15, 1.16.5,...).
  - Tự động nhận diện và gán bytecode target cho Forge SRG (`func_71229_d`), Fabric Intermediary (`method_3864`/`method_3782`) và Mojang Official Mappings (`d`).
  - Khắc phục triệt để lỗi người chơi kết nối qua mạng LAN (IP:Port) bị ngắt kết nối với lỗi `"Invalid session"` khi host bật chế độ Offline LAN.
- **Tự động đồng bộ và nạp Hotfix ngay khi launcher khởi động lần đầu**:
  - Tinh chỉnh `_bootstrap_hotfixes()` tự động kích hoạt chế độ đồng bộ nhanh fail-open (`auto_sync=True`, timeout 2.0s) khi phát hiện launcher mới tải về hoặc chưa có hotfix cục bộ trước khi nạp các module giao diện vào bộ nhớ RAM.
  - Tự động dọn dẹp và thu hồi các module cũ trong `sys.modules` (`_evict_cached_hotfix_modules`) ngay sau khi áp dụng bản vá nóng.
  - Tích hợp thông báo Toast nhắc nhở người dùng khởi động lại launcher khi có bản vá nóng mới được nạp ngầm trong phiên làm việc.
- **Tài khoản Offline chỉ gán skin Steve / Alex cục bộ, không tìm kiếm skin online**:
  - Khi tạo tài khoản offline, tự động xác định biến thể Steve (`classic`) hoặc Alex (`slim`) theo thuật toán băm UUID chuẩn của Minecraft Java (`DefaultPlayerSkin`).
  - Vô hiệu hóa việc truy vấn skin online từ Minotar/Mojang đối với tài khoản offline, kể cả khi tên tài khoản trùng với tên tài khoản bản quyền.
- **Chuyển đổi thời gian lần cuối chơi (`last_played`) sang múi giờ hệ thống (Local Timezone)**:
  - Hàm `format_last_played` chuyển đổi timestamp UTC đã lưu sang múi giờ địa phương bằng `astimezone()`, đảm bảo hiển thị đúng giờ và ngày tháng thực tế theo múi giờ của người dùng (ví dụ UTC+7).

## [1.8.1] - 2026-10-14

### Added
- **Thanh cuộn ngang cho không gian quản lý phiên bản (Instance Hub)**:
  - Bọc bảng điều khiển Instance Hub vào `QScrollArea` với chính sách tự động hiển thị thanh cuộn khi không gian chiều ngang bị giới hạn.
  - Đảm bảo hiển thị đầy đủ toàn bộ nút công cụ (như nút "Xóa") và các tab chi tiết (Mods, Nhật ký, Ảnh chụp, Thế giới) ở mọi độ phân giải màn hình hoặc cửa sổ hẹp (~1024x600).
  - Tích hợp style đồng bộ cho `QScrollBar:horizontal` tương ứng với dark theme và accent runtime của launcher.

### Fixed
- **Bỏ thuộc tính luôn nổi lên trên (`WindowStaysOnTopHint`) của màn hình Loading/Splash**:
  - Loại bỏ cờ `WindowStaysOnTopHint` khỏi `StartupSplash`, giúp màn hình loading không còn che khuất các cửa sổ ứng dụng khác của hệ điều hành Windows khi người dùng thao tác đa nhiệm trong lúc launcher khởi động.
- **Điều hướng tải trực tiếp trang chờ đếm ngược CurseForge (`/download/{file_id}`)**:
  - Tự động dẫn thẳng tới trang đếm ngược chính thức của CurseForge để tải đúng file jar của modpack thay vì trang chủ mod.
  - Tích hợp tra cứu slug dự phòng qua `cflookup.com` khi không có API key.
  - Thêm nút "Mở tất cả liên kết tải" (`open_all_button`) và tự động nạp mod từ thư mục `~/Downloads`.
- **Khử trùng lặp thư viện Maven (Deduplicate Maven Libraries) trên Classpath**:
  - Khắc phục triệt để lỗi xung đột Log4j và lwjgl, giúp các phiên bản Forge cũ (như 1.16.5) khởi động trơn tru.

### Changed
- **Khởi chạy trực tiếp theo cơ chế Prism Launcher**:
  - Không chặn kiểm tra trước khi quét phụ thuộc mod, giao quyền xử lý trực tiếp cho ModLoader trong JVM.

## [1.8.1-beta.3] - 2026-10-14

### Fixed
- **Điều hướng tải trực tiếp trang chờ đếm ngược CurseForge (`/download/{file_id}`)**:
  - Khắc phục triệt để lỗi người dùng bị điều hướng đến trang tìm kiếm hoặc trang chủ mod rồi bấm nhầm nút Download tải về phiên bản mới nhất (1.20/1.21) gây crash Forge loader (`javafml:40` / `javafml:61`) trên các phiên bản modpack cũ (như 1.16.5).
  - Tích hợp bộ phân giải slug tự động qua `cflookup.com/{project_id}` cho các modpack chỉ khai báo ID số mà không có CurseForge Gateway API key, tự động chuyển đổi sang đường dẫn chính tắc của mod.
  - Tự động tạo URL trang chờ đếm ngược trực tiếp (`https://www.curseforge.com/minecraft/{category}/{slug}/download/{file_id}`) để trình duyệt tự động bắt đầu tải file jar chính xác sau 5 giây mà không cần thao tác thủ công.
  - Bổ sung nút **"Mở tất cả liên kết tải"** (`open_all_button`) trong hộp thoại tải thủ công khi có nhiều mod cần nạp, kết hợp tính năng tự động nhận diện file trong `~/Downloads` để tự động import và kiểm tra mã băm SHA-1.

## [1.8.1-beta.2] - 2026-10-14

### Fixed
- **Khử trùng lặp thư viện Maven (Deduplicate Maven Libraries) trên Classpath**:
  - Khắc phục triệt để lỗi xung đột thư viện Log4j (`NoSuchMethodError` / rác log `%minecraftFormatting` và `%tEx}`) khi khởi động các bản Forge như 1.16.5.
  - Tự động thay thế các thư viện nguyên bản của Mojang bằng các phiên bản mới hơn do Mod Loader khai báo (ví dụ `log4j-core 2.15.0`, `lwjgl 3.2.2`, `jopt-simple 5.0.4`), giữ nguyên vị trí trên classpath.
  - Giúp game và ModLoader (FML) khởi động ổn định, ghi đầy đủ crash report và hiển thị cửa sổ GUI cảnh báo mod lỗi thay vì làm sập ngang tiến trình Java.

## [1.8.1-beta.1] - 2026-10-13

### Changed
- **Khởi chạy trực tiếp theo cơ chế Prism Launcher (Không chặn kiểm tra trước)**:
  - Loại bỏ hoàn toàn các rào cản chặn khởi động khi quét phụ thuộc mod (`RequiredModDependenciesMissing`), chuyển sang cảnh báo phi chặn và nhường toàn quyền kiểm tra cho ModLoader trong JVM.
  - Nâng cấp schema cấu hình lên `SCHEMA_VERSION = 20`, loại bỏ tùy chọn chính sách thất bại preflight khỏi Settings và Instance config.
  - Tích hợp chính thức các cải tiến từ bản vá nóng `1.8.0.x`.

## [1.8.0.2] - 2026-10-11

### Fixed
- **Bản vá nóng (Hotfix)** cho phép bỏ qua toàn bộ lỗi tương thích Forge khi cấu hình cho phép:
  - Khắc phục triệt để lỗi chặn khởi động do `RequiredModDependenciesMissing` hoặc xác minh thư viện Forge runtime (`validate_runtime_files`) khi người dùng chọn chính sách "Cho phép chạy và bỏ qua lỗi tương thích" (`ManagedContentPolicy.ALLOW`).
  - Đảm bảo launcher bỏ qua hoàn toàn các bước chặn kiểm tra phụ thuộc bắt buộc và tiếp tục khởi chạy game mượt mà, chuyển các vấn đề phụ thuộc sang dạng cảnh báo (warnings) không gây crash.

## [1.8.0.1] - 2026-10-11

### Fixed
- **Bản vá nóng (Hotfix)** sửa lỗi nạp metadata Forge mods:
  - Khắc phục lỗi `RequiredModDependenciesMissing` khi khởi động các instance Forge (như *Roguelike Adventures and Dungeons 2*) do các mod phổ biến (*The Twilight Forest*, *Hwyla*, *Feywild*, *Sledgehammer*, *Wall-Jump!*) chứa chuỗi định dạng nhiều dòng không chuẩn trong file `META-INF/mods.toml`.
  - Bổ sung cơ chế phân tích cú pháp khoan dung (`_normalize_lenient_toml` / `mods.toml (tolerant)`) tự động xử lý ký tự xuống dòng (`\n`) và ký tự thoát chưa chuẩn hóa trong các chuỗi cơ bản, đồng bộ với hành vi nạp mod của Java NightConfig trên Forge.

## [1.8.0] - 2026-09-30

### Added
- **Tách biệt 100% Core & GUI (`mcw_core.rpc`)**:
  - Bổ sung giao thức **JSON-RPC 2.0** đa kênh (`CoreRpcDispatcher`, `CoreRpcClient`, `GuiCoreRpcBridge`) phục vụ giao tiếp độc lập giữa GUI và `mcw-launcher-core`.
  - Hỗ trợ chế độ **Stdio Sidecar Process** (`mcw-core-rpc --stdio`) và **Local HTTP + Server-Sent Events (SSE) Daemon** (`mcw-core-rpc --http` trên `127.0.0.1`).
  - Mở rộng `mcw_core/api/` và `mcw_core/api/models/` bao phủ toàn bộ models và services; loại bỏ 100% câu lệnh import trực tiếp `src.core.*` và `src.models.*` khỏi `src/gui/` và `launcher.py`.
- **Tích hợp chính thức toàn bộ cải tiến từ bản vá nóng `v1.7.1.1`**:
  - Tăng tốc khởi động ứng dụng nhờ cơ chế **Hardware GPU Caching** trong `GpuPreferenceManager`.
  - Chuyển tiến trình đồng bộ Hotfix sang luồng nền không chặn khởi động (`_start_background_hotfix_sync`).
  - Hiển thị trực quan phiên bản Hotfix đang kích hoạt trên màn hình `StartupSplash`, `HomePage`, `LauncherSettingsPage`, và `MainWindow`.

## [1.7.1] - 2026-09-25

### Added
- Tự động kiểm tra và đồng bộ bản vá nóng (Hotfix) từ Cloudflare Edge CDN khi khởi động launcher (`HotfixManager.bootstrap_sys_path(auto_sync=True)`).
- Tích hợp bộ nạp động `HotfixMetaPathFinder` cho các bản build thực thi đóng gói (PyInstaller Frozen), đảm bảo các bản vá nóng ghi đè module an toàn mà không cần cập nhật toàn bộ file nhị phân.
- Tinh chỉnh giao diện nút Làm Mới (Refresh) Modloader với chính sách co giãn ôm sát nội dung (`_update_reload_button_geometry`) và đệm lề phải (`addStretch(1)`).
- Nâng cấp **MCW Update Bridge 1.7.1**:
  - Tự động phát hiện và cập nhật lên bản phát hành mới nhất (`latest`).
  - Hỗ trợ cơ chế Fallback thông minh khi release mới đang trong quá trình build assets.
  - Cập nhật giao diện Tkinter GUI và workflow GitHub Actions hỗ trợ mục tiêu `latest`.

## [1.7.0] - 2026-09-24

### Added
- Hệ thống Hotfix Engine động tích hợp Cloudflare Edge CDN (`mcw-download.pages.dev`).
- Hỗ trợ định dạng phiên bản vá lỗi 4 số: `1.7.x.y` (ví dụ `1.7.0.1`, `1.7.0.2`).
- Cơ chế khôi phục trạng thái bản vá và chuyển đổi nguyên tử (Atomic Directory Swap).

## [1.6.1] - 2026-09-23

### Added
- Thêm nút tải lại (reload) danh sách phiên bản modloader trong hộp thoại Tạo Instance (`CreateInstanceDialog`), cho phép người dùng nạp lại danh sách mà không cần phải khởi động lại launcher khi gặp sự cố mạng.
- Bổ sung hàm `HttpDownloader.get_with_retry` với cơ chế tự động thử lại tối thiểu 5 lần (`max_attempts=5`) và exponential backoff cho các yêu cầu API metadata của các modloader (Fabric, Quilt, Forge, NeoForge, OptiFine).
- Tự động bỏ qua cache danh sách rỗng khi tải loader thất bại để người dùng có thể thử lại ngay lập tức.

### Fixed
- Fix Issue #32: `FileNotFoundError: [WinError 3] The system cannot find the path specified` during Minecraft 1.21.1 NeoForge instance creation on Windows environments with path length >= 260 characters (`MAX_PATH`).
- Shorten staging publishing temporary file pattern in `SharedFileMaterializer` to `.tmp_<hex>.pub`, saving up to 90 path characters.
- Add extended Windows path prefix (`\\?\`) support in `windows_path.py` (`copy_file`, `link_file`, `same_file`) with streaming chunk fallback for Win32 file copying.
- Protect `NeoForgeVersionManager` and `ForgeVersionManager` against long file paths during caching, installer staging, and verification.

## [1.6.1-beta.1] - 2026-09-23

### Fixed
- Fix Issue #32: `FileNotFoundError: [WinError 3] The system cannot find the path specified` during Minecraft 1.21.1 NeoForge instance creation on Windows environments with path length >= 260 characters (`MAX_PATH`).
- Shorten staging publishing temporary file pattern in `SharedFileMaterializer` to `.tmp_<hex>.pub`, saving up to 90 path characters.
- Add extended Windows path prefix (`\\?\`) support in `windows_path.py` (`copy_file`, `link_file`, `same_file`) with streaming chunk fallback for Win32 file copying.
- Protect `NeoForgeVersionManager` and `ForgeVersionManager` against long file paths during caching, installer staging, and verification.

## [1.6.0] - 2026-09-20

### Added
- Promoted to stable release `v1.6.0` on branch `1.6`.
- Restore single-file (`onefile`) distribution packaging for Windows (`MCW Launcher.exe`) and Linux (`mcw-launcher`) to maximize initial startup compatibility and avoid false-positive anti-malware/SmartScreen scans.
- Add automatic legacy onedir artifact scrubbing: `UpdateApplier` automatically removes obsolete `_internal/` directory and prunes empty directory trees during updates from older onedir beta builds to 1.6.0.

### Fixed
- Fix CurseForge mod loader resolution, duplicated game version prefixes in Forge installer URLs, and older modpack loader detection.
- Fix FTB instance running status reporting and prevent timeout eviction of preparing run locks during large downloads.
- Fix CurseForge manual download dialog: multi-tier mod matching, automatic Downloads directory scanning, auto-close on completion, and safe cancellation.
- Fix ATLauncher Forge loader normalization, instance auto-healing, and allow installation of packs with server-only archive actions and standard Forge launch wrappers.

## [1.6.0-beta.5] - 2026-09-20

### Added
- Enhance CurseForge gateway compatibility with modern endpoint deployments.
- Add flexible mod loader identifier and structure parsing in `CurseForgePackInstaller`:
  - Support prefixed loader IDs (e.g. `1.20.1-47.3.0` -> `47.3.0`, `loader-0.15.11` -> `0.15.11`).
  - Support list of dicts, list of strings, or single dict `modLoaders`/`modLoader` in modpack manifests.
  - Expand loader alias mappings (`forge`, `minecraftforge`, `fabric`, `fabric-loader`, `quilt`, `quilt-loader`, `neoforge`, `neoforged`, `neo`).
- Parse mod loaders and Minecraft versions from `sortableGameVersions` in `CurseForgeClient` for older modpacks (1.7.10, 1.12.2).
- Automatically resolve target loader matching modpack file in `CurseForgeBrowserDialog`.
- Add `InstanceRunLock.touch()` and periodic heartbeat touching in `FTBContentManager` during large modpack validation and downloads.

### Fixed
- Fix CurseForge 404 installer URL download failure caused by duplicated game version coordinate prefixes.
- Fix FTB instance running status not reported to launcher:
  - Prevent preparing run locks owned by the active launcher process from expiring and being pruned during long downloads/content validation.
  - Auto-recreate missing lock files with state `running` in `_update_owned_lock` when the game process starts.
  - Fix button state flicker in `MainWindow` by syncing running instance state before signaling launch completion.

### Changed
- Bump development version to `v1.6.0-beta.5` on branch `1.6`.

## [1.6.0-beta.4] - 2026-09-20

### Added
- Redesign GlobalTaskIndicator with modern Modrinth-style 3-tier layout:
  - Top row: Status icon, Stage Badge pill, bold task description.
  - Middle row: 7px prominent progress bar with Modrinth green (`#00af5c`).
  - Bottom row: Network speed, progress byte counts, and completion percentage.
  - Red failure state with detailed error messaging.
- Add reusable `ActiveTaskCard` with in-place data updates and completed card caching in `TaskDrawerPopover`.
- Introduce ~30 FPS throttling for progress update events to eliminate GUI freezing during high-frequency downloads and file scanning.

### Fixed
- Eliminate modpack selection lag by removing automatic background scanning on instance selection in `MainWindow`.
- Fix local GUI freeze when opening TaskDrawerPopover and transitioning between tasks by avoiding widget allocation/destruction thrashing.
- Fix Modrinth loader compatibility check when a multi-loader mod depends on loader-specific projects (e.g. Quilted Fabric API on Fabric).
- Fix Microsoft login cancellation hang by properly handling `task_cancelled` in `AccountController`.
- Fix default Steve and Alex textures and support texture URLs from Mojang CDN.
- Avoid duplicate progress dispatch in `MainWindow._on_launch_progress`.

### Changed
- Remove legacy compact progress bar from action panel in `InstanceWorkspacePage`.
- Bump development version to `v1.6.0-beta.4` on branch `1.6`.

## [1.6.0-beta.3] - 2026-09-17

### Added
- Dynamic Loader Library Discovery for Fabric, Quilt, Forge, and NeoForge loaders.
- Global Task Drawer with background task execution and speed metrics.
- Microsoft OAuth Device Code Flow with copy code and browser launch support.
- Launch error notification dialog for Java runtime, mod incompatibilities, and early crashes.

### Changed
- Bump development version to `v1.6.0-beta.3` on branch `1.6`.

## [1.6.0-beta.2] - 2026-09-15

### Added
- Support dedicated GPU (dGPU) preference on Linux using switcheroo-control (`switcherooctl list`), with fallbacks to `lspci`, `/sys/bus/pci/devices`, and `/proc/driver/nvidia`.
- Automatically inject discrete GPU environment variables for Minecraft Java runtime on Linux:
  - NVIDIA PRIME Render Offload (`__NV_PRIME_RENDER_OFFLOAD=1`, `__GLX_VENDOR_LIBRARY_NAME=nvidia`, `__VK_LAYER_NV_optimus=NVIDIA_only`).
  - Mesa DRI (`DRI_PRIME=1`).
- Integrate SignPath.io v2 code signing into GitHub Actions release workflow.
- Add NTFS `:Zone.Identifier` unblocking to prevent Windows SmartScreen / SAC blocks during update and extraction.
- Add fallback to Windows Shell (`ShellExecuteExW`) when updater process launch is blocked by Smart App Control (`WinError 4551`).
- Add empty directory cleanup (`_internal/`) on updater rollback.
- Widen instance library sidebar (260px minimum, 320px default splitter) to prevent text truncation in instance list items.
- Move instance metadata badges to a dedicated full-width row with word-wrap disabled.

### Fixed
- Prevent platform pollution in `UpdateApplier` unit tests by skipping Windows MessageBox test on Linux instead of mutating `os.name`.

### Changed
- Bump development version to `v1.6.0-beta.2` on branch `1.6`.

## [1.6.0-beta.1] - 2026-09-14

### Added
- Introduce onedir packaging format for Windows and Linux with cold start in under 1 second.
- Redesign Instance Workspace: remove bottom launch control bar, expand top action panel to 100% full view without scrollbars.
- Add slim `CompactProgressWidget` in instance action panel displaying download %, install %, and network speed.
- Add automatic foreground window activation for Minecraft game window upon launch / Quick Play.
- Support seamless auto-updater migration from legacy 1.5.1 onefile installations to modern onedir structure.

### Changed
- Bump development version to `v1.6.0-beta.1` on branch `1.6`.
- Organize instance tools into two clean, comfortable rows of 36px buttons with adjusted padding to avoid font clipping.

## [1.6.0-alpha.4] - 2026-09-13

### Added
- Complete Instance Workspace redesign: sidebar instance list with quick filter and search, paired with tabbed hub (Worlds, Screenshots, Live Logs, Mods).
- Add Quick Play integration for direct access to singleplayer worlds and multiplayer servers.
- Fix missing text on World tab delete and open folder action buttons.
- Fix ghost element artifacts and Qt painter / Shiboken C++ object lifecycle errors during rapid instance switching.
- Fix Discord Rich Presence detecting wrong game process (Fortnite).

### Changed
- Bump development version to `v1.6.0-alpha.4` on branch `1.6`.

## [1.6.0-alpha.3] - 2026-09-13

### Added
- Add update safety recovery tool (`updater.py --recovery`) with Tkinter GUI and CLI fallback to rollback backups or clear lock files when updates fail.
- Add remote emergency hotfix and rollback bypass (`[MCW-EMERGENCY-HOTFIX]`, `[MCW-EMERGENCY-ROLLBACK]`) in update client.
- Add persistent updater backup mirroring in installation directory (`updater/backup/`).
- Add playtime tracking and last played timestamp on instances, formatted nicely and displayed in Workspace.
- Add `TaskDrawerPopover` interactive background task list and control popover when clicking `GlobalTaskIndicator`.
- Add JVM preset selection (Aikar, ZGC, Shenandoah, Default) and custom argument support to Modpack Import and Instance Settings dialogs.

### Changed
- Bump development version to `v1.6.0-alpha.3` on branch `1.6`.

## [1.6.0-alpha.2] - 2026-09-13

### Added
- Introduce `GlobalTaskIndicator` on `MainWindow` top navigation bar displaying background task states, mini progress bar, percentage, and multi-task tooltip.
- Add Discord Rich Presence (RPC) support displaying active game instance and playtime on Discord profile with toggle in Launcher Settings.
- Add direct `.mrpack` modpack export support with automatic `modrinth.index.json` generation and hash calculation.
- Add one-dir packaging architecture support (`mcw_launcher.spec`) and seamless updater migration from 1.5.1 one-file installations.

### Changed
- Bump development version to `v1.6.0-alpha.2` on branch `1.6`.

## [1.6.0-alpha.1] - 2026-09-11

### Added
- Introduce GUI Core architecture (`src/gui/core/`) including `GuiAppState`, `GuiTaskQueue`, and `GuiContext` inspired by modern launcher design patterns.
- Add JVM flags presets in Instance Settings: Aikar's Flags (G1GC low-stutter), Generational ZGC (Java 21+ low latency), and Shenandoah GC.
- Add automatic preset detection and custom flag synchronization.
- Integrate mclo.gs log sharing into the Logs page with automatic sensitive data redaction and clipboard integration.

### Changed
- Bump development version to `v1.6.0-alpha.1` on branch `1.6`.

## [1.5.1] - 2026-09-11

### Stable
- Promotes the tested Beta 7 dependency resolver to stable, including Fabric `provides` aliases and nested-JAR capabilities.
- Keeps the hardened Windows updater transition from Beta 6, including native replacement and rename-away fallback.
- Adds MCW Update Bridge v1.6.0 as the one-time recovery path from affected 1.5.0 installations directly to v1.5.1.

## [1.5.1-beta.7] - 2026-09-11

### Fixed
- Parse Fabric `fabric.mod.json` `provides` aliases and expose them as installed dependency identities.
- Treat aliases such as Cloth Config API `cloth-config2` as satisfied when the installed JAR declares the alias while keeping its primary ID (`cloth-config`).
- Index Fabric `provides` aliases in capability discovery for top-level and safely nested Fabric JARs.
- Verify auto-discovered Modrinth dependency candidates against Fabric aliases instead of requiring the requested dependency ID to be the primary mod ID.

### Scope
- No updater architecture changes in Beta 7; the Windows updater/recovery path remains the Beta 6 implementation.

## [1.5.1-beta.6] - 2026-09-11

### Fixed
- Replace the Beta 5 DELETE-access preflight with the real Win32 executable transition as the source of truth.
- Use `ReplaceFileW` / `MoveFileExW` for Windows launcher replacement and report the numeric Win32 error when Windows blocks the operation.
- Add a rename-away fallback that retires the previous launcher image before installing the new executable when direct replacement is denied by a lingering mapped image.
- Clear a stale READONLY attribute before replacement and restore it if the transition never succeeds.
- Correct rollback restart logging so a restored launcher is not described as an updated launcher.

### Recovery
- MCW Update Bridge v1.5.0 now targets `v1.5.1-beta.6` while retaining LF-safe checksum generation and repository-independent GitHub release publishing.

## [1.5.1-beta.5] - 2026-09-11

### Fixed
- Harden Windows updater handoff against `WinError 5`: after the primary PID exits, MCW Updater waits for every process using the exact launcher executable path and confirms Windows DELETE/replace access before starting the update transaction.
- Keep executable-first atomic replacement/retry so a persistent lock fails before other release files are mutated.

### Changed
- Redesign `MCW Updater.exe` into a branded standalone update window with the MCW logo, target version, phase text and progress states.
- Bundle updater logo/icon assets directly in `mcw_updater.spec` without pulling PySide6/Qt into the updater.
- Move MCW Update Bridge to v1.4.0 with `v1.5.1-beta.5` as its default target, retaining checksum/publish CI fixes and opt-in `MCW-USE-BRIDGE`.
- Continue excluding `docs/` from release ZIPs and cleaning legacy `docs/` through the update manifest.

### Safety
- If the launcher image remains locked after the pre-transaction release timeout, Beta 5 aborts before copying update files and reports recovery information instead of creating a mixed-version installation.

## [1.5.1-beta.4] - 2026-09-10

### Changed
- Hoàn thiện updater độc lập: Windows `MCW Updater.exe` có GUI riêng, launcher chỉ đóng sau khi updater mới phát tín hiệu READY.
- Thêm fallback sang updater hiện đang được cài nếu updater của release mới không thể khởi tạo.
- Release ZIP không còn chứa `docs/`; manifest thêm `cleanup_paths: ["docs"]` để updater và Bridge dọn tài liệu cũ nếu tồn tại mà không báo lỗi khi không có.
- Nâng MCW Update Bridge lên v1.3.0 và target `v1.5.1-beta.4`.
- Thêm maintainer override `MCW-USE-BRIDGE`: chỉ khi marker này tồn tại cùng Bridge + SHA-256 thì launcher mới tự dùng Bridge thay updater thường.

### Fixed
- Required Modrinth dependency do launcher quản lý (ví dụ Cloth Config API) sẽ được tải lại nếu file tracked bị stale/hash mismatch, thay vì preserve rồi tiếp tục chặn launch.

## [1.5.1-beta.3] - 2026-09-09

### Added

- Thêm `MCW Updater.exe` / `mcw-updater` là binary updater độc lập, được build cùng release đích và đóng gói trong thư mục `updater/` của ZIP.
- Thêm `updater.py` và `mcw_updater.spec` để updater không phụ thuộc entry point GUI của launcher.
- Nâng Update Bridge lên v1.2.0, hỗ trợ cả Windows x64 và Linux x64, target trực tiếp `v1.5.1-beta.3` và xác minh package schema 2.

### Changed

- Chuyển update package sang `mcw-update.json` schema 2 với trường `updater` bắt buộc.
- Launcher hiện tại lấy updater từ ZIP của **phiên bản mới**, copy updater đó sang thư mục tạm rồi mới thoát; không còn copy/rename launcher hiện tại thành updater.
- GitHub Actions và `build_release.ps1` build launcher + updater riêng trước khi tạo ZIP Windows/Linux.
- Linux ZIP encode executable mode cho cả `mcw-launcher` và `updater/mcw-updater`.

### Safety

- Package thiếu updater mới bị từ chối trước khi sửa installation; không fallback sang updater cũ.
- Giữ executable-first replacement, retry file-lock và rollback fail-safe từ Beta 2.

### Migration

- Người dùng Windows/Linux đang ở v1.5.0 dùng `MCW Update Bridge v1.2.0` một lần để lên Beta 3.
- Live gate quan trọng tiếp theo là `Beta 3 → Beta 4`, nhằm xác nhận updater được thực thi thực sự là updater nằm trong ZIP Beta 4.

## [1.5.1-beta.2] - 2026-09-09

### Changed

- Windows updater thay `MCW Launcher.exe` trước các file còn lại để lỗi file-lock không tạo installation trộn nhiều phiên bản.
- File tạm của executable chỉ được copy một lần; updater retry riêng thao tác atomic replace tối đa khoảng 30 giây thay vì copy lại toàn bộ EXE ở mỗi lượt.
- Rollback bỏ qua file vẫn giống hệt backup, tránh cố ghi đè lại executable cũ khi update chưa từng thay được file đó.

### Fixed

- Sửa `WinError 5: Access is denied` có thể xảy ra khi PyInstaller/Windows/antivirus còn giữ `MCW Launcher.exe` trong thời gian ngắn sau khi process launcher đóng.
- Không còn tự restart launcher nếu rollback cũng thất bại; updater giữ log và yêu cầu khôi phục/reinstall thay vì chạy một installation có thể không nhất quán.

### Tests

- Thêm regression tests cho executable-first update, transient file-lock retry, rollback bỏ qua executable không đổi và fail-safe restart policy.
- Nhóm test updater đạt `53 passed, 1 skipped` trong môi trường build hiện tại.

### Release status

- Beta 2 cần smoke-test trực tiếp trên Windows packaged ZIP bằng luồng update từ `v1.5.1-beta.1` lên `v1.5.1-beta.2`.

## [1.5.1-beta.1] - 2026-09-09

### Added

- Tự tìm dependency mà modpack bỏ sót trên Modrinth bằng mod ID khai báo trong metadata của mod cha.
- Xác minh candidate bằng hash, Minecraft version, loader, version constraint và mod ID đọc trực tiếp từ JAR trước khi thêm vào instance.
- Lưu cache alias `mod ID → provider project` đã xác minh để những lần launch sau không phải tìm kiếm lại.

### Changed

- Gộp nhiều lỗi cùng thiếu một dependency thành một nhóm dễ đọc, đồng thời giữ nguyên danh sách mod cha trong provenance.
- Giới hạn vòng hoàn tất dependency còn hai lượt; provider graph vẫn được duyệt đệ quy nhưng UI không lặp Resolving/Checking tới tám lần.

### Security

- Không tin tên/slug từ kết quả tìm kiếm và không cài candidate chỉ vì tên gần giống dependency.
- Candidate không đúng mod ID, sai loader, sai Minecraft version hoặc không đạt version constraint bị loại mà không thay đổi instance.

### Release status

- Beta 1 cần smoke-test bằng một modpack có dependency bị manifest bỏ sót, đặc biệt trường hợp Fabric `cloth-config2`/Cloth Config API.

## [1.5.0] - 2026-09-03

### Added

- Phát hành chính thức bản đóng gói Windows x64 và Linux x64 từ cùng một release gate.
- Hỗ trợ automatic update an toàn trên Linux, gồm kiểm tra manifest/checksum, backup, rollback, giữ executable mode và tự khởi động lại.
- Hỗ trợ Linux XDG storage, Secret Service, managed Java, Microsoft OAuth, trạng thái mạng và process-group supervision.
- Hỗ trợ Vanilla, Fabric, Quilt, Forge, NeoForge cùng quy trình cài modpack và quản lý nội dung theo instance.

### Changed

- Giao diện giữ kích thước tự nhiên của widget và dùng vùng cuộn khi không gian hiển thị bị giới hạn.
- Launch pipeline chỉ resolve/check một lần khi người dùng xác nhận bỏ qua cảnh báo tương thích.
- Trình mở file/thư mục trên Linux tách khỏi môi trường Qt/PyInstaller và có chuỗi fallback desktop phù hợp.

### Fixed

- Sửa responsive của Add Instance, Instance Info và OptiFine trên Linux.
- Sửa Open Folder không phản hồi trong bản Linux x64 đóng gói bằng PyInstaller.
- Sửa vòng đời tiến trình game/installer, lựa chọn Java theo phiên bản và nhiều lỗi regression chéo Windows/Linux.

### Release status

- Toàn bộ release gate Windows/Ubuntu và smoke-test trực tiếp Beta 4 trên Lubuntu đã đạt.
- Stable giữ nguyên runtime đã được xác nhận ở Beta 4; thay đổi phát hành chỉ gồm metadata và tài liệu.

## [1.5.0-beta.4] - 2026-09-02

### Changed

- Trình mở file/thư mục trên Linux loại bỏ đường dẫn thư viện và Qt plugin do PyInstaller chèn trước khi gọi ứng dụng desktop của hệ thống.
- `xdg-open` được kiểm tra lỗi sớm; launcher tự thử `gio open`, sau đó `pcmanfm-qt` cho thư mục trên Lubuntu.

### Fixed

- Sửa nút Open Folder của instance không phản hồi trong bản Linux x64 dù cùng đường dẫn vẫn mở được từ Terminal.
- Không còn coi process desktop handler vừa spawn là thành công khi process thoát lỗi ngay lập tức.
- Đường dẫn không tồn tại bị từ chối rõ ràng; lỗi mở thư mục instance hiện hiển thị cả đường dẫn cho người dùng.

### Release status

- Beta 4 là regression fix của Beta 3 trước khi chuyển sang RC; cần smoke-test trực tiếp trên ZIP Linux x64 đóng gói bằng PyInstaller.

## [1.5.0-beta.3] - 2026-08-30

### Changed

- Dialog OptiFine mở từ panel chức năng của instance dùng lưới hai cột ổn định thay cho form có thể nén sai chiều cao trên Linux.
- Giá trị Detected version giữ một dòng với chiều rộng tự nhiên; đường dẫn JAR dài vẫn được xuống dòng.
- Nội dung OptiFine cuộn dọc khi thiếu chiều cao, trong khi hàng nút Install/Repair/Uninstall/Close luôn cố định.

### Fixed

- Không còn cắt hoặc chồng dòng Detected version trong dialog OptiFine trên Lubuntu.

### Release status

- Automatic update Beta 1 → Beta 2 trên Linux x64 đã được xác nhận hoạt động thành công; Beta 3 tập trung chốt UI regression trước RC.

## [1.5.0-beta.2] - 2026-08-29

### Changed

- OptiFine và Instance Info giữ kích thước tự nhiên; khi thiếu chiều cao, nội dung cuộn dọc còn action/footer vẫn truy cập được.
- Các thao tác mở file/thư mục trên Linux ưu tiên `xdg-open`, sau đó `gio open`, rồi mới dùng Qt desktop services.

### Fixed

- Sửa dialog OptiFine và panel Instance Info bị cắt/chồng nội dung trên Linux ở cửa sổ nhỏ.
- Sửa các nút Open Folder không phản hồi trên một số desktop Lubuntu.

### Release status

- Beta 2 là live update gate để xác nhận updater Beta 1 → Beta 2 giữ nguyên dữ liệu XDG và khởi động lại đúng phiên bản.

## [1.5.0-beta.1] - 2026-08-28

### Added

- Automatic updater thử nghiệm cho packaged Linux x64 release.
- Platform-aware GitHub asset selection cho ZIP Windows/Linux riêng biệt.
- Linux updater helper chạy tách session, kiểm tra quyền ghi, giữ executable mode và tự restart.
- Integration test giả lập toàn bộ Beta 1 → Beta 2 mà không thay đổi dữ liệu XDG.

### Changed

- Release manifest bắt buộc khớp schema, version, platform, executable và managed-file set.
- Update applier thay từng file atomically và dùng chung backup/rollback cho Windows/Linux.

### Security

- Từ chối path traversal, symlink, duplicate archive path, file ngoài manifest và sai platform.
- Updater Linux không gọi `sudo`; thư mục cài đặt chỉ đọc phải update thủ công.

### Release status

- Beta 2 sẽ là live update gate đầu tiên cho luồng Beta 1 → Beta 2 trên Lubuntu.

## [1.5.0-alpha.5] - 2026-08-28

### Changed

- Compatibility confirmation tạm dừng launch attempt hiện tại và tiếp tục tại chỗ sau khi người dùng cho phép.
- Dialog giữ kích thước tự nhiên của action button; nội dung Add Instance tiếp tục dùng cuộn dọc khi thiếu chiều cao.

### Fixed

- Không còn chạy lại toàn bộ dependency resolving, managed-file checking và loader preflight sau cảnh báo tương thích có thể bỏ qua.
- Các nút dài trong dialog tương thích không còn bị ép nhỏ làm cắt chữ.
- Trạng thái OptiFine trong Add Instance nằm trên một hàng tự nhiên, không còn căn lệch/chồng hàng khi bị vô hiệu hóa.
- Cross-platform test không còn thay đổi `os.name` toàn cục làm pytest dùng sai `PosixPath`/`WindowsPath`; version contract cũng không còn ghim số Alpha cũ.

### Release status

- Alpha 5 là Alpha cuối của nhánh `1.5.0`; bước tiếp theo là Beta release gate trên Windows và Linux.

## [1.5.0-alpha.4] - 2026-08-23

### Added

- Forge và NeoForge được đưa vào Linux release gate.
- Fallback xác định Java 8/16/17/21 theo Minecraft release khi profile cũ hoặc custom bị thiếu `javaVersion`.
- Scrollable page dùng chung giữ minimum size tự nhiên của widget và chỉ hiện thanh cuộn dọc khi thiếu không gian.

### Changed

- Metadata `javaVersion` của Mojang luôn được ưu tiên; fallback release mapping chỉ dùng khi metadata không tồn tại.
- Add Instance, First Run Setup và các tab Runtime/Policy của Instance Settings dùng cùng một quy tắc responsive.
- Forge/NeoForge installer chạy trong process group riêng trên POSIX.

### Fixed

- Modern Forge/NeoForge không còn mặc định nhầm Java 8 khi version profile thiếu Java metadata.
- Loader installer bị timeout trên Linux dọn cả process group thay vì có thể để lại Java child process.

### Known limitations

- Forge/NeoForge vẫn cần smoke test launch thực tế trên Lubuntu trước khi chốt Alpha 4.
- Chưa có AppImage/DEB, Linux updater hoặc cam kết Linux ARM64.

## [1.5.0-alpha.3] - 2026-08-22

### Added

- XDG storage layout cho config, data, cache và state trên Linux.
- Migration một lần, copy-only từ layout portable Alpha 2; dữ liệu cũ không bị xóa hay ghi đè khi có xung đột.
- Linux Secret Service/keyring cho khóa bảo vệ refresh token Microsoft, kèm fallback local có cảnh báo.
- OAuth browser fallback qua `xdg-open` và callback server chỉ bind loopback IPv4.
- Trạng thái Online/Offline thường trực trên thanh điều hướng.
- Process group riêng cho mỗi phiên Minecraft trên POSIX để Stop/Kill xử lý đúng cây tiến trình.

### Changed

- Fabric và Quilt được đưa vào Linux release gate cùng với Vanilla và Microsoft login.
- Theme, account, instance, managed Java, backup và log dùng đúng XDG root sau bootstrap.
- Credential audit hiển thị backend bảo vệ đang dùng.

### Fixed

- Tiến trình con của loader/Java trên Linux không còn dễ bị bỏ lại khi dừng game từ launcher.
- Microsoft sign-in có thể mở trình duyệt trên các desktop Linux nơi module `webbrowser` không tìm được handler.

### Known limitations

- Chưa có AppImage/DEB và automatic updater cho Linux.
- Forge/NeoForge và Linux ARM64 chưa nằm trong release gate Alpha 3.

## [1.5.0-alpha.2] - 2026-08-21

### Added

- Linux platform profile, Adoptium metadata selection và managed Java TAR.GZ extraction.
- Linux credential encryption backend và Linux preflight tool.
- Adaptive sizing cho toàn bộ combobox trong GUI.
- Ubuntu Qt dependencies trong CI.
- Cảnh báo offline không chặn launch và thông báo khi kết nối Internet được khôi phục.

### Changed

- Java discovery dùng executable/path theo nền tảng.
- HTTP client hỗ trợ SOCKS proxy từ environment.
- Linux x64 được nâng từ nền tảng ban đầu thành source-test target.
- Manifest, Minecraft version metadata và Java startup dùng chiến lược cache-first để tránh chờ network timeout khi offline.
- Kiểm tra cập nhật và JDK online được hoãn hoặc bỏ qua khi chưa có kết nối.

### Fixed

- Adaptive combobox lấy icon của mục đang chọn qua API `itemIcon()` tương thích PySide6.
- Bổ sung lại các module cấu hình Core bị thiếu khỏi source package.
- Vanilla Minecraft 1.21.1 đã được smoke-test thành công trên Lubuntu 24.04 trong VirtualBox, gồm cả cached offline launch.

### Known limitations

- Chưa có AppImage/DEB và automatic updater cho Linux.
- Forge/NeoForge, Microsoft login và Linux ARM64 chưa nằm trong release gate.

## [1.5.0-alpha.1] - 2026-08-21

### Changed

- Chuẩn hóa metadata dự án, dependency groups và version `1.5.0-alpha.1`.
- Tách việc tải version metadata khỏi import-time để startup không tự phụ thuộc mạng.
- Dùng downloader có xác minh checksum và verified-cache fallback cho version JSON.
- Chọn native library theo hệ điều hành thay vì hard-code Windows.
- Nhận diện riêng Linux ARM64 thay vì ánh xạ nhầm sang x64.
- Validate identifier, artifact path và digest từ metadata trước khi tạo đường dẫn local.
- Chấp nhận các Minecraft version ID legacy chính thức có dấu cách; một entry lỗi không còn làm rỗng toàn bộ manifest.
- Sắp xếp lại tài liệu, release notes và quy trình preflight.

### Removed

- File delivery/patch/test output tạm ở repository root.
- Module rỗng hoặc legacy không có consumer.
- Cấu hình Microsoft trùng lặp; client metadata chỉ còn một nguồn trong `src/config.py`.
- Hàng trăm release-note rời của các bản cũ; lịch sử đầy đủ vẫn có trong Git/GitHub Releases.

### Known limitations

- Linux packaging và managed Java provisioning chưa hoàn chỉnh.
- Windows vẫn là nền tảng release chính của Alpha 1.

[1.5.0-beta.1]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0-beta.1
[1.5.1-beta.2]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.1-beta.2
[1.5.1-beta.1]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.1-beta.1
[1.5.0-beta.2]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0-beta.2
[1.5.0-beta.3]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0-beta.3
[1.5.0-beta.4]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0-beta.4
[1.5.0]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.5.0

## [1.4.1]

Maintenance release của nhánh 1.4, tập trung Java recovery/download và Diagnostics v2.1. Xem tag `v1.4.1` trong GitHub Releases để đọc release notes đầy đủ.

[1.4.1]: https://github.com/mahiru7229/mcw-launcher/releases/tag/v1.4.1
