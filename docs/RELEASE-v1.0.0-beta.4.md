# MCW Launcher v1.0.0-beta.4

## Tiếng Việt

Beta 4 tập trung vào vòng đời nội dung đã cài, đặc biệt là **nguồn gốc của mod trong modpack**. Mod được khai báo bởi Modrinth, CurseForge hoặc FTB không còn hiển thị nguồn `-` trong Manage Mods.

### Điểm mới

- Thêm registry thống nhất `.mcw/mod-provenance.json` cho từng file mod.
- Lưu provider, project ID, version ID, file ID, hash, dung lượng, URL tải và modpack sở hữu file.
- Đồng bộ provenance ngay khi cài manifest modpack, kể cả trước lần Launch đầu tiên tải JAR.
- Modrinth `.mrpack` nhận diện project/version từ CDN URL chính thức khi manifest không khai báo ID riêng.
- CurseForge giữ chính xác cặp `projectId` / `fileId` từ manifest.
- FTB giữ `fileId`, URL chính và mirrors dưới nguồn FTB.
- Manage Mods hiển thị `Modrinth • Modpack`, `CurseForge • Modpack` hoặc `FTB • Modpack`; mod người dùng thêm thủ công vẫn là `Cục bộ`.
- Panel chi tiết hiển thị định danh provider để kiểm tra và chẩn đoán dễ hơn.
- Registry provider-specific vẫn được giữ để update/repair; provenance registry chỉ chuẩn hóa dữ liệu cho GUI và export trong tương lai.
- Launch, Pause, Resume và Cancel được mở rộng theo cả chiều ngang lẫn chiều cao của vùng điều khiển.
- Giữ nguyên rich browser, FTB, deferred first-launch download, resource pack và shader pack từ các beta trước.

### Chuẩn bị cho beta.6

Dữ liệu nguồn được lưu theo từng binary thay vì chỉ theo tên file. Exporter beta.6 có thể dùng provider reference và hash để tạo manifest nhiều nguồn, chỉ đóng gói trực tiếp file không thể tải lại an toàn.

## English

Beta 4 focuses on installed-content lifecycle and, most importantly, **mod provenance inside modpacks**. Mods declared by Modrinth, CurseForge, or FTB no longer appear with an unknown `-` source in Manage Mods.

### Highlights

- Add a unified per-instance `.mcw/mod-provenance.json` registry.
- Persist provider, project/version/file IDs, hashes, size, download URLs, and owning modpack identity.
- Synchronize provenance as soon as a modpack manifest creates the instance, before first-launch JAR downloads.
- Recover Modrinth project/version identity from official CDN URLs when the pack index has no explicit IDs.
- Preserve exact CurseForge `projectId` / `fileId` pairs and FTB file identity with mirrors.
- Show `Modrinth • Modpack`, `CurseForge • Modpack`, or `FTB • Modpack` in Manage Mods while user-added files remain Local.
- Expose provider identity in the mod detail panel for diagnostics.
- Keep provider-specific registries authoritative for update and repair workflows.
- Expand Launch, Pause, Resume, and Cancel controls in both dimensions.
- Preserve the rich browser, FTB support, deferred downloads, resource packs, and shader packs from earlier betas.

### Beta 6 preparation

Source identity is stored per binary instead of relying on filenames. The planned beta.6 exporter can resolve provider references by hash, create multi-source manifests, and embed only files that cannot be re-downloaded safely.
