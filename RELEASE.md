# MCW Launcher v1.8.3-beta.3

Bản thử nghiệm **MCW Launcher v1.8.3-beta.3** mang đến tính năng kiểm soát chế độ Chơi nhanh (Quick Play) theo đúng chuẩn Minecraft 1.20+, cải thiện màn hình Loading (`StartupSplash`) hiển thị tự nhiên không bị đẩy xuống layer đáy hệ điều hành, tích hợp quản lý tài khoản ngay trong First Run Setup, bổ sung bộ lọc chống đổi giá trị khi lăn chuột (Wheel Guard), và hoàn thiện độ ổn định hệ thống trước bản phát hành chính thức.

---

## Điểm nổi bật trong bản phát hành (Highlights)

### 1. Giới hạn Chơi nhanh (Quick Play) chuẩn Minecraft 1.20+
- **Ẩn nút Chơi nhanh cho các phiên bản cũ (< 1.20)**:
  - Tính năng Chơi nhanh (`Quick Play`) được Mojang giới thiệu chính thức từ Minecraft 1.20 (snapshot 23w14a).
  - Giao diện `InstanceWorkspacePage` tự động ẩn nút Chơi nhanh (`quick_play_button`) trên thanh hành động chính khi instance chọn phiên bản Minecraft thấp hơn 1.20.
  - Tự động ẩn nút Chơi (`play_button`) trên từng thẻ thế giới (`WorldCardWidget`) trong tab Worlds nếu phiên bản instance không hỗ trợ Quick Play.
  - Bộ chuẩn bị lệnh khởi chạy (`LauncherManager.build`) chủ động bỏ qua tham số `--quickPlaySingleplayer` / `--quickPlayMultiplayer` nếu phiên bản game thấp hơn 1.20, ngăn ngừa game bị crash do nhận cờ không hợp lệ.

### 2. Cải thiện màn hình Loading (`StartupSplash`) thân thiện
- **Sử dụng layer cửa sổ chuẩn (`Qt.WindowType.Window`)**:
  - Khắc phục triệt để hiện tượng cửa sổ loading bị Windows tự động đẩy xuống layer đáy cùng (nằm sau mọi ứng dụng khác) do cờ `Qt.WindowType.Tool`.
  - Tự động gọi `raise_()` khi hiển thị giúp màn hình loading luôn xuất hiện rõ ràng ở trung tâm màn hình, cho phép người dùng thoải mái quan sát tiến trình nạp dữ liệu.
  - Giữ nguyên thiết kế không dùng `WindowStaysOnTopHint`, giúp người dùng thoải mái chuyển đổi cửa sổ làm việc mà không bị màn hình splash che khuất hay chiếm quyền.

### 3. Quản lý tài khoản trong First Run Setup & Mặc định Java Auto
- **Tạo tài khoản Offline và đăng nhập Microsoft ngay từ Setup**:
  - Tích hợp thêm bước thiết lập tài khoản vào hộp thoại `FirstRunSetupDialog`.
  - Hỗ trợ tạo tài khoản Offline trực tiếp hoặc kích hoạt luồng đăng nhập Microsoft Device Code ngay trong wizard khởi chạy đầu tiên.
  - Tự động hủy tác vụ đăng nhập Microsoft an toàn khi đóng, bỏ qua hoặc hủy hộp thoại.
- **Mặc định lựa chọn Java luôn là `Auto`**:
  - Java selector trong First Run Setup luôn ưu tiên mục `Auto` (dù máy đã có sẵn các bản cài Java) trừ khi người dùng chủ động chỉ định.

### 4. Triệt tiêu hiện tượng đơ giao diện (UI Freezing) & Giảm 50% I/O đĩa
- **Loại bỏ quét đĩa thừa khi cập nhật giao diện**:
  - Ghi nhận `_hub_loaded_instance_key` trong `InstanceWorkspacePage`: không còn quét lại toàn bộ dữ liệu 4 tab (`saves/`, `screenshots/`, `latest.log`, `mods/*.jar`) ngay trên GUI thread khi cập nhật trạng thái.
- **Cơ chế Lazy-loading cho các Hub Tab**:
  - 3 tab nặng (`Screenshots`, `Live Logs`, `Mods`) được nạp lười: chỉ thực hiện đọc đĩa khi người chơi thực sự bấm chuyển sang tab đó.
- **Tối ưu hóa tài nguyên Live Logs**:
  - Quản lý `_poll_timer` của `InstanceLiveLogsTab` theo chu kỳ hiển thị (`showEvent` / `hideEvent`): timer đọc file log ngầm tự động tạm dừng khi chuyển sang tab khác, giảm tải CPU và disk I/O.
- **Khử trùng lặp nạp `instance.json`**:
  - `InstanceController.refresh` tái sử dụng dữ liệu từ `list()`, loại bỏ hoàn toàn lần đọc đĩa thứ hai của `list_health()`.

### 5. Bảo vệ thao tác cuộn chuột (Wheel Guard)
- **Tích hợp `WheelBlockFilter`**:
  - Ngăn chặn hiện tượng người dùng lăn chuột để cuộn trang Settings / Instance Settings nhưng vô tình làm thay đổi giá trị của các `QSpinBox`, `QComboBox`, `QSlider`.
  - Khởi tạo lười và bảo vệ an toàn vòng đời `QCoreApplication`.

### 6. Khắc phục kết nối Microsoft OAuth & Cô lập Hotfix trong Test Suite
- **Khắc phục lỗi Device Code Dialog**:
  - Tự động gán modal parent chính xác theo cửa sổ đang kích hoạt (First Run Setup hoặc MainWindow), khắc phục lỗi `NameError`.
  - Luôn khôi phục `parent` về `MainWindow` khi kết thúc hoặc hủy phiên đăng nhập.
- **Ưu tiên phân giải IPv4 (`prefer_ipv4_dns`)**:
  - Khắc phục lỗi timeout kết nối Microsoft trên các mạng dual-stack IPv4/IPv6 khi định tuyến IPv6 bị rớt gói.
- **Cô lập test suite Hotfix**:
  - Chặn các modal câu hỏi restart và request mạng nền trong môi trường test (`if "pytest" in sys.modules: return`), triệt tiêu hoàn toàn hiện tượng test runner bị đóng băng.

---

## Thông tin kiểm thử & Xác thực (Verification)

- **Release Preflight**: Đạt chuẩn 100% cho `v1.8.3-beta.3` (`python -m tools.release_preflight`).
- **Kiểm thử toàn bộ hệ thống**: Vượt qua toàn bộ 2,175+ tests.
- **Kiểm thử giao diện (GUI Tests)**: Vượt qua toàn bộ 298/298 GUI tests.
- **Ngôn ngữ**: Đầy đủ 2,310 khóa dịch ngữ đồng bộ giữa tiếng Anh (`en-US`) và tiếng Việt (`vi-VN`).
