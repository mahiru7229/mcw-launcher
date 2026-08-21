# Contributing

Cảm ơn bạn muốn đóng góp cho MCW Launcher.

1. Tạo branch từ nhánh phát triển hiện tại và giữ mỗi pull request trong một phạm vi rõ ràng.
2. Cài môi trường bằng `python -m pip install -e '.[dev,build]'`.
3. Thêm hoặc cập nhật test cho thay đổi hành vi.
4. Chạy `python -m pytest test -v` và `python -m tools.release_preflight`.
5. Mô tả nền tảng đã thử, bước tái hiện và ảnh/log đã loại bỏ dữ liệu cá nhân.

Quy ước kiến trúc:

- GUI gọi nghiệp vụ qua `mcw_core.api`/public facade, không import `src.core` trực tiếp.
- Import module không được tạo network request hoặc sửa persistent state.
- Code theo nền tảng phải có nhánh Windows/Linux rõ ràng và test tương ứng.
- Không commit `accounts/`, `instances/`, `cache/`, `logs/`, private config, token hoặc API key.

Bug report nên có version launcher, OS/architecture, phiên bản Python/Java, bước tái hiện, kết quả mong đợi và kết quả thực tế.
