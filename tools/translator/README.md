# MCW Translation Studio — Hướng dẫn dành cho Bộ phận Dịch thuật

**MCW Translation Studio** là ứng dụng hỗ trợ dịch thuật giao diện và thông báo cho MCW Launcher. Ứng dụng được thiết kế riêng nhằm giúp các bạn dịch giả thao tác nhanh chóng, chính xác và không bao giờ gặp lỗi vỡ cấu trúc file hoặc sai biến hệ thống.

---

## 1. Cách khởi động ứng dụng

Bạn có 2 cách rất đơn giản để mở ứng dụng:

1. **Cách 1 (Khuyên dùng):** Nhấp đúp chuột vào file **`run_translator.bat`** tại thư mục gốc `mcw-launcher`.
2. **Cách 2:** Chạy dòng lệnh sau trong terminal:
   ```cmd
   python tools/translator/translator_server.py
   ```

*Ứng dụng sẽ tự động khởi chạy và mở trình duyệt web (Chrome/Edge/Firefox) tại địa chỉ `http://127.0.0.1:8765`.*

---

## 2. Các tính năng nổi bật

### 🎨 Giao diện song ngữ trực quan (Side-by-Side)
- Cột bên trái hiển thị danh sách toàn bộ **2,294 chuỗi** được phân loại theo module (`instance`, `account`, `mod_manager`, `settings`, `progress`...).
- Cột bên phải là không gian dịch thuật gồm:
  - **Khung tiếng Anh gốc (en-US):** Làm chuẩn đối chiếu, tự động tô màu các biến `{name}`, `{count}`, `{path}`...
  - **Khung bản dịch:** Soạn thảo bản dịch với thống kê số từ và ký tự theo thời gian thực.

### 🛡️ Chống lỗi biến (Placeholder Protection)
- Trong Minecraft launcher, các biến như `{name}`, `{minecraft}`, `{count}` là bắt buộc phải giữ nguyên để hiển thị dữ liệu động (nếu thiếu hoặc gõ sai tên biến, launcher sẽ bị lỗi).
- **Chèn biến 1-chạm:** Khi có biến, một thanh các nút chip nhỏ (ví dụ `+ {name}`) sẽ xuất hiện. Bạn chỉ cần bấm vào nút chip là biến sẽ tự động được chèn ngay vào vị trí con trỏ chuột!
- **Hệ thống cảnh báo thời gian thực:** Cảnh báo màu đỏ ngay lập tức nếu bạn vô tình làm mất biến hoặc gõ sai chính tả biến so với tiếng Anh gốc.

### 🔍 Bộ lọc và tìm kiếm siêu tốc
- **Tìm kiếm:** Gõ từ khóa tìm theo Key, từ tiếng Anh hoặc từ tiếng Việt (phím tắt `Ctrl + F`).
- **Nút lọc trạng thái:**
  - **Tất cả:** Toàn bộ chuỗi trong dự án.
  - **Chưa dịch:** Lọc các chuỗi đang để trống.
  - **Lỗi biến:** Lọc các chuỗi có sự sai lệch biến placeholder.
  - **Giống Anh:** Lọc các chuỗi đang để nguyên tiếng Anh (chưa dịch hoặc từ mượn).
  - **Chưa lưu:** Xem những chuỗi bạn đã sửa trong phiên làm việc hiện tại.
- **Lọc theo Module:** Giúp bạn tập trung dịch trọn vẹn từng tính năng (ví dụ hôm nay dịch hết module `mod_manager`).

### ⚡ Phím tắt dịch nhanh (Dành cho Pro Translators)
- <kbd>Ctrl</kbd> + <kbd>Enter</kbd>: Xác nhận chuỗi hiện tại và tự động nhảy sang chuỗi kế tiếp.
- <kbd>Alt</kbd> + <kbd>↓</kbd>: Xuống chuỗi tiếp theo.
- <kbd>Alt</kbd> + <kbd>↑</kbd>: Lên chuỗi phía trước.
- <kbd>Ctrl</kbd> + <kbd>S</kbd>: Lưu toàn bộ vào file `lang/vi-VN.json`.
- <kbd>Ctrl</kbd> + <kbd>F</kbd>: Di chuyển con trỏ vào thanh tìm kiếm.
- <kbd>Esc</kbd>: Đóng cửa sổ popup.

### 🔄 Tự động sao lưu an toàn (Auto-Backup)
Mỗi lần bạn bấm **"Lưu File"** (hoặc `Ctrl + S`), hệ thống sẽ tự động tạo một bản sao lưu có kèm ngày giờ tại thư mục `lang/.backups/vi-VN_YYYYMMDD_HHMMSS.json`. Bạn không bao giờ sợ bị mất bản dịch cũ.

### 📊 Kiểm tra chất lượng (QA Preflight Audit)
Bấm nút **"Kiểm tra QA"** ở góc trên thanh điều hướng để chạy bộ kiểm tra tự động theo chuẩn xuất xưởng của MCW Launcher:
- Kiểm tra tính đầy đủ 100% của các key.
- Phát hiện chuỗi để trống.
- Kiểm tra toàn bộ tính tương thích của biến placeholder.
- Nhấp trực tiếp vào từng dòng lỗi để màn hình tự động nhảy ngay đến chuỗi đó để sửa.

### 📁 Nhập / Xuất Excel (CSV)
Nếu bộ phận dịch muốn làm việc nhóm qua Google Sheets hoặc Microsoft Excel:
- Bấm nút **"CSV / Excel"** -> **"Tải file CSV về máy"** (file đã tích hợp chuẩn mã UTF-8 BOM chống lỗi font tiếng Việt trong Excel).
- Sau khi dịch trên Excel, lưu lại file CSV và dùng nút **"Nhập bản dịch từ file"** để tải ngược vào studio.

### 🌐 Hỗ trợ thêm ngôn ngữ mới
Để thêm ngôn ngữ mới (ví dụ tiếng Nhật `ja-JP`, tiếng Trung `zh-CN`, tiếng Pháp `fr-FR`):
- Bấm nút **`+`** bên cạnh ô chọn ngôn ngữ.
- Nhập mã locale và tên hiển thị.
- Hệ thống sẽ tự động sao chép bộ khung 2,294 key để bạn bắt đầu dịch ngay lập tức.
