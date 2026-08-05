# MCW Launcher v1.1.0-beta.1

> Beta đầu tiên của nhánh 1.1.0, chỉ tập trung sửa các phần giao diện và tiến trình còn hiển thị tiếng Anh khi launcher đang dùng tiếng Việt.

---

# Tiếng Việt

## Tổng quan

MCW Launcher v1.1.0-beta.1 hoàn thiện bản dịch cho cửa sổ **Quản lý instance nâng cao** và các thông báo tiến trình động được phát ra từ MCW Core.

Bản beta này cố ý chỉ xử lý mục **1 — chưa dịch** trong kế hoạch v1.1.0. Các mục Java, responsive mod loader, retry mạng, Forge legacy và progress bảo vệ tài khoản sẽ được tách sang các beta tiếp theo.

## Thay đổi

- Dịch đầy đủ trang **Quản lý instance nâng cao**, gồm tiêu đề, mô tả, card, nút, placeholder, tooltip và nút đóng.
- Đảm bảo trang nâng cao tự dịch đúng ngay khi được tạo và khi toàn bộ giao diện được retranslate.
- Dịch các progress còn sót:
  - `Preparing Minecraft libraries...`
  - `Preparing Minecraft assets...`
  - `Checking CurseForge files...`
  - `Checking CurseForge files after round x/3...`
- Thêm semantic translation key cho subtitle của trang instance hỗ trợ Vanilla, Fabric, Quilt, Forge và NeoForge.
- Bổ sung regression test cho progress động, trang instance nâng cao và tiêu đề dialog tiếng Việt.
- Đồng bộ metadata phiên bản launcher và MCW Core thành `1.1.0-beta.1`.

## Không thuộc beta này

- Chọn Java tự động hoặc theo đường dẫn.
- Tự phục hồi khi chọn sai Java.
- Responsive và tinh gọn màn hình cài mod loader.
- Retry metadata/download và nút Retry.
- Sửa đối số `--gameDir` trùng trên Forge legacy.
- Sửa progress sau khi kiểm tra bảo vệ tài khoản.

## Xác minh tự động

- Launcher: `1281 passed, 79 skipped`.
- MCW Core source: `18 passed`.
- Wheel `mcw_core-1.1.0b1-py3-none-any.whl` được build thành công và import smoke test xác nhận runtime `1.1.0-beta.1`, distribution `1.1.0b1`.

## Kiểm tra thủ công

```text
1. Chọn ngôn ngữ Tiếng Việt và khởi động lại launcher.
2. Mở Instance → Quản lý nâng cao.
3. Xác nhận toàn bộ tiêu đề, card, nút và placeholder đều dùng tiếng Việt.
4. Launch một modpack CurseForge và theo dõi bước kiểm tra file.
5. Launch một instance chưa có đủ thư viện/assets và theo dõi progress chuẩn bị.
```

---

# English

## Overview

MCW Launcher v1.1.0-beta.1 completes localization for the **Advanced Instance Management** window and dynamic progress messages emitted by MCW Core.

This beta intentionally addresses only item **1 — missing translations** from the v1.1.0 plan. Java selection, responsive loader installation, network retry, Forge legacy launch arguments, and account-security progress recovery remain for later betas.

## Changes

- Fully localize the Advanced Instance Management page, including titles, cards, buttons, placeholders, tooltips, and the close button.
- Retranslate the advanced page both at construction time and during full UI language refreshes.
- Localize remaining Minecraft library/assets and CurseForge file-check progress messages.
- Add a semantic subtitle key for the multi-loader instance page.
- Add regression coverage for Vietnamese progress messages, advanced-page content, and dialog titles.
- Align launcher and MCW Core metadata to `1.1.0-beta.1`.

## Scope exclusions

This beta does not yet change Java selection, loader-install responsiveness, retry behavior, Forge legacy argument normalization, or account-protection progress handling.

## Automated validation

- Launcher: `1281 passed, 79 skipped`.
- MCW Core source: `18 passed`.
- The built wheel passed an isolated target-install import smoke test and reports runtime `1.1.0-beta.1` / distribution `1.1.0b1`.
