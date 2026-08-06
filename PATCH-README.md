# MCW Launcher v1.1.1-beta.6 — RLCraft legacy dependency fix

## Mục tiêu

Beta 6 sửa trường hợp modpack Forge legacy đã ghim dependency trong manifest nhưng audit cuối vẫn báo thiếu mod ID, điển hình:

```text
CompatSkills requires missing dependency 'reskillable' (*).
```

## Thay đổi chính

- Quét thêm đúng thư mục legacy `mods/<minecraft-version>/` cho instance Forge/NeoForge, ngoài `mods/` cấp đầu.
- Không quét đệ quy tùy ý, tránh nhận nhầm cache, backup và JAR không thuộc runtime.
- Đọc đúng `mcmod.info` legacy có nhiều entry: entry đầu là mod chính, các entry còn lại là `provided_mods`.
- Khi dependency bị báo thiếu, ưu tiên đối chiếu file mà manifest CurseForge của chính pack đã ghim.
- Giữ nguyên `projectId`, `fileId`, path và version do tác giả pack chọn; không tự thay bằng bản mới nhất.
- Nếu file pack-pinned bị thiếu hoặc không cung cấp đúng mod ID, đưa chính file đó trở lại hàng đợi download/repair.
- CurseForge pack registry nâng lên schema 4 và lưu `projectName`, `projectSlug`, `expectedModIds`.
- JAR có `expectedModIds` phải thật sự cung cấp identity đó sau download; hash đúng nhưng mod ID sai không còn được xem là hoàn tất.
- Cross-provider bridge chỉ chạy sau khi xác nhận pack không có dependency tương ứng.

## Phạm vi tích lũy

ZIP này bao gồm toàn bộ thay đổi dependency/Forge cache từ Beta 5 hotfix v1-v5, cùng bản sửa RLCraft của Beta 6. Có thể áp dụng trực tiếp lên source `v1.1.1-beta.5` gốc hoặc chồng lên một hotfix Beta 5 trước đó.

## Cách áp dụng

1. Đóng MCW Launcher.
2. Giải nén ZIP vào thư mục root source Beta 5.
3. Cho phép ghi đè file.
4. Mở launcher và launch/repair RLCraft lại.

Không cần xóa instance hoặc tải lại toàn bộ modpack. Nếu Reskillable đang thiếu vật lý, launcher sẽ đưa đúng file đã được pack ghim trở lại hàng đợi tải.

## Xác thực

```text
1398 passed
88 skipped
2 expected warnings
compileall passed
clean Beta 5 overlay regression passed
wheel import/version validation passed
ZIP integrity passed
```
