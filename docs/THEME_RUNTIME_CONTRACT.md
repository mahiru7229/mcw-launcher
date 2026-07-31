# MCW Theme Runtime Contract v1

## Tiếng Việt

MCW Launcher `v0.11.0-rc.1` đóng băng giao kèo theme để MCW Theme Studio và các công cụ bên ngoài có thể tạo theme mà không phải sao chép logic từ GUI launcher.

### Các phiên bản đã chốt

| Thành phần | Phiên bản |
|---|---:|
| Runtime contract | `1` |
| Theme manifest schema | `6` |
| Asset catalog | `1` |
| Theme package ZIP | `1` |
| Validation report | `1` |

Theme schema 6 không đổi tên field, không đổi ý nghĩa field và không xóa asset key trong dòng `v0.11.x`. Thay đổi phá tương thích phải dùng schema mới. Launcher tiếp tục đọc schema 1–5 để giữ tương thích với theme cũ.

### Tệp máy có thể đọc

Các tệp sau nằm trong [`docs/schema`](schema):

- [`theme.schema.v6.json`](schema/theme.schema.v6.json): JSON Schema Draft 2020-12 cho `theme.json`.
- [`theme-assets.v1.json`](schema/theme-assets.v1.json): danh mục asset key, đường dẫn gợi ý, kích thước và mục đích.
- [`theme-runtime-contract.v1.json`](schema/theme-runtime-contract.v1.json): descriptor liên kết schema, catalog, package và validation report.

Có thể tạo lại chính xác ba tệp bằng:

```bash
python tools/export_theme_contract.py
```

### Validation report

Core validator không phụ thuộc PySide6:

```python
from pathlib import Path
from src.core.theme import ThemeValidator

report = ThemeValidator().validate_directory(Path("themes/my-theme"))
print(report.to_dict())
```

CLI tương đương, phù hợp cho editor hoặc CI:

```bash
python tools/validate_theme.py themes/my-theme --json
```

Mỗi issue có cấu trúc ổn định:

```json
{
  "severity": "error",
  "category": "asset",
  "code": "THEME_ASSET_UNKNOWN_KEY",
  "field": "assets.icon.example",
  "message": "Unknown asset key: icon.example"
}
```

`message` dành cho con người; Theme Studio nên quyết định hành vi dựa trên `code`, `field`, `severity` và version của report.

### Package ZIP v1

Export RC 1 có các đặc điểm:

- thứ tự file và timestamp ZIP cố định;
- cùng nội dung theme tạo cùng byte ZIP trong cùng runtime;
- đường dẫn dùng `/`;
- permission entry cố định;
- `theme-checksums.json` dùng SHA-256;
- checksum không tự bao gồm chính `theme-checksums.json`;
- import kiểm tra file thiếu, file thừa, checksum sai và theme ID không khớp;
- package Beta 2 dùng trường `sha256` vẫn được hỗ trợ khi import.

Cấu trúc chuẩn:

```text
my-theme.zip
└── my-theme/
    ├── theme.json
    ├── theme-checksums.json
    ├── styles.qss
    ├── fonts/
    ├── icons/
    └── animations/
```

### Quy tắc tương thích

- Schema 6 yêu cầu theme ID dạng chữ thường: `a-z`, `0-9`, `.`, `_`, `-`.
- Schema 6 từ chối field cấp cao không thuộc contract.
- Schema 1–5 giữ hành vi tương thích cũ.
- Theme không được chạy Python, JavaScript hoặc executable.
- Core theme không import `PySide6` hay `src.gui`.
- Theme Studio có thể tái sử dụng trực tiếp `src/core/theme` hoặc chỉ dùng các JSON contract.

---

## English

MCW Launcher `v0.11.0-rc.1` freezes the theme contract so MCW Theme Studio and external tools can create packages without copying launcher GUI logic.

### Frozen versions

| Component | Version |
|---|---:|
| Runtime contract | `1` |
| Theme manifest schema | `6` |
| Asset catalog | `1` |
| Theme package ZIP | `1` |
| Validation report | `1` |

Schema 6 fields will not be renamed, reinterpreted, or removed during the `v0.11.x` line. Breaking changes require a new schema version. Schemas 1–5 remain readable for backward compatibility.

### Machine-readable files

[`docs/schema`](schema) contains:

- [`theme.schema.v6.json`](schema/theme.schema.v6.json), a Draft 2020-12 JSON Schema for `theme.json`;
- [`theme-assets.v1.json`](schema/theme-assets.v1.json), the stable asset slot catalog;
- [`theme-runtime-contract.v1.json`](schema/theme-runtime-contract.v1.json), the contract descriptor and document hashes.

Regenerate them with:

```bash
python tools/export_theme_contract.py
```

### Stable validation API

`ThemeValidator` and the package helpers live under `src/core/theme` and do not depend on Qt. Validation reports expose versioned dictionaries and stable issue codes. Tooling should use codes and fields for behavior while treating messages as display text.

A CLI bridge is also available:

```bash
python tools/validate_theme.py themes/my-theme --json
```

### Deterministic package format

Package v1 fixes ZIP ordering, timestamps, permissions, path separators, and checksum structure. Imports reject missing, extra, modified, duplicated, unsafe, or mismatched files. Beta 2 checksum manifests remain import-compatible.
