# MCW Launcher v0.11.0-rc.1 — Theme Runtime Contract Freeze

## Tiếng Việt

RC 1 đóng băng tính năng của v0.11 và chuẩn bị nền tảng ổn định cho MCW Theme Studio. Từ bản này đến stable chỉ nhận sửa lỗi chặn phát hành, lỗi tương thích và lỗi đóng gói.

### Thay đổi chính

- Đóng băng Theme Schema 6 và Runtime Contract v1.
- Thêm JSON Schema máy đọc được cho toàn bộ `theme.json`.
- Xuất Asset Catalog v1 với toàn bộ slot PNG, kích thước đề xuất và mô tả.
- Thêm descriptor contract cùng SHA-256 của schema và catalog.
- Tách validator có cấu trúc khỏi GUI, không phụ thuộc PySide6.
- Thêm validation report version 1 với `severity`, `category`, `code`, `field`, `path` và `message`.
- Chuẩn hóa mã lỗi ổn định cho manifest, asset, animation, font, motion, stylesheet và security.
- Chuyển export theme sang package format v1 deterministic.
- Xác minh checksum, file thiếu, file thừa và theme ID khi import.
- Giữ khả năng import package checksum của Beta 2.
- Schema 6 dùng theme ID chuẩn hóa và từ chối field cấp cao ngoài contract.
- Schema 1–5 tiếp tục tương thích.
- Thêm `tools/export_theme_contract.py`, CLI `tools/validate_theme.py --json` và tài liệu Runtime Contract song ngữ.

### Kiểm tra RC trước stable

- Import → export → import cùng một theme.
- Duplicate default theme rồi chỉnh font, PNG, animation và QSS.
- Thử package bị sửa byte, thêm file ngoài checksum và sai theme ID.
- Mở theme schema 1–5 để kiểm tra fallback/migration.
- Kiểm tra live reload khi `theme.json` đang được ghi dở.
- Kiểm tra Full, Reduced và Off ở 100%, 125%, 150% và 200% DPI.
- Build EXE sạch và kiểm tra updater từ Beta 2 lên RC 1.

## English

RC 1 freezes the v0.11 feature set and establishes the stable contract required by MCW Theme Studio. Only release-blocking, compatibility, packaging, and regression fixes should be accepted before stable.

### Main changes

- Frozen Theme Schema 6 and Runtime Contract v1.
- Added a machine-readable JSON Schema for `theme.json`.
- Added Asset Catalog v1 with every PNG slot, recommended size, and purpose.
- Added a contract descriptor with schema and catalog hashes.
- Moved structured validation into a Qt-independent core API.
- Added validation report v1 with stable severity, category, code, field, path, and message fields.
- Standardized issue codes for manifests, assets, animations, fonts, motion, stylesheets, and security.
- Changed theme exports to deterministic package format v1.
- Imports now verify checksums, missing files, extra files, and theme ID consistency.
- Beta 2 checksum packages remain import-compatible.
- Schema 6 requires normalized IDs and rejects unknown top-level fields.
- Schemas 1–5 remain backward compatible.
- Added `tools/export_theme_contract.py`, the `tools/validate_theme.py --json` CLI, and bilingual runtime contract documentation.

## Metadata

- Version: `v0.11.0-rc.1`
- Version ID: `0.11.0-rc.1`
- Update channel: `beta`
- Theme schema: `6`
- Runtime contract: `1`
- Package format: `1`
