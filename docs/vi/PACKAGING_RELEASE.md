# Đóng gói MCW Core

MCW Launcher `v1.5.0-alpha.3` có bundle implementation Core nhưng chủ động **không** phát hành source archive hoặc wheel Core độc lập.

Chỉ thực hiện đợt release Core riêng sau khi đã chốt version và phạm vi. Trước khi publish:

1. Đồng bộ version runtime, distribution và Git tag.
2. Đóng gói `mcw_core*` cùng toàn bộ implementation/resource mà public API phụ thuộc; không đưa GUI, test hoặc dữ liệu người dùng vào wheel.
3. Cài wheel trong môi trường Python 3.12 sạch trên Windows và Linux.
4. Kiểm tra import `mcw_core` không cần PySide6, CLI, LAN Agent, examples và public API tests.
5. Audit wheel để loại account database, private config, log, cache và credential.

Mức ổn định:

- `mcw_core`: facade ổn định nên ưu tiên;
- `mcw_core.api.*`: public boundary chi tiết;
- `src.*`: implementation tương thích nội bộ, không phải contract cho consumer.
