# MCW Launcher v1.1.1-beta.5 — Dependency provider bridge hotfix v2

Đây là bản vá tích lũy cho `v1.1.1-beta.5`. Có thể áp dụng trực tiếp lên Beta 5 gốc hoặc lên bản đã cài hotfix dependency compatibility trước đó.

## Lỗi được sửa

Một số file CurseForge không trả dependency ở cấp file dù JAR tự khai dependency và bản phát hành tương ứng trên Modrinth có metadata đầy đủ. Trường hợp đã xác nhận:

```text
Create Slice & Dice requires missing dependency 'kotlinforforge' ([3.9.1,)).
Could not resolve required dependency 'kotlinforforge' from Modrinth or CurseForge.
```

## Cách resolver mới hoạt động

1. Giữ nguyên manifest của modpack làm nguồn sự thật.
2. Sau khi JAR của pack được tải, quét metadata thật trong JAR để tìm dependency còn thiếu.
3. Với mod được pack quản lý từ CurseForge, dùng SHA-1 của chính JAR để tìm đúng cùng bản phát hành trên Modrinth.
4. Chỉ đọc quan hệ `required` từ bản mirror có cùng hash; không tìm bằng tên mơ hồ và không hardcode Kotlin for Forge.
5. Ghép slug/title provider với mod ID bằng identity chuẩn hóa, ví dụ `kotlin-for-forge` → `kotlinforforge`.
6. Không tải trùng dependency đã có, ví dụ `Create`.
7. Thêm dependency còn thiếu vào Modrinth registry dưới dạng file do modpack quản lý và tải bằng pipeline retry/progress hiện có.
8. Trước khi cài, xác nhận JAR tải về thật sự cung cấp mod ID được yêu cầu.

## Phạm vi tích lũy

Bản ZIP này cũng giữ sửa lỗi version false-positive trước đó: dependency do modpack ghim như `1.19.2-5.1.4.3` được chấp nhận khi chính modpack đã chọn file đó, trong khi dependency thiếu hoặc bị disable vẫn chặn launch.

## Cài đặt

Giải nén ZIP vào thư mục source `v1.1.1-beta.5`, giữ nguyên cấu trúc thư mục và cho phép ghi đè file.

## Xác thực

```text
1385 passed
88 skipped
2 expected warnings
compileall passed for src, mcw_core and test
```

Hai warning đến từ fixture ZIP cố ý chứa entry trùng trong test bảo mật.
