# MCW Launcher v1.1.1-beta.1

## Tiếng Việt

MCW Launcher **v1.1.1-beta.1** bắt đầu nhánh 1.1.1 với phần đầu tiên của tích hợp **ATLauncher**. Bản beta này tập trung vào browser, metadata, tạo instance và pipeline tải nội dung được quản lý; các pack dùng thao tác cài đặt legacy/phức tạp được nhận diện và chặn an toàn thay vì cài dở dang.

### ATLauncher provider

- Thêm tab/browser ATLauncher trong luồng **Add Instance** và thanh công cụ instance.
- Tìm kiếm pack công khai, phân trang, sắp xếp và xem trạng thái cache.
- Xem thông tin pack, website hỗ trợ, phiên bản Minecraft, changelog và kênh phát hành.
- Hỗ trợ bộ lọc `release`, `beta` và `alpha`.
- Chọn chính xác phiên bản pack trước khi cài.
- Cho phép chọn cài các file tùy chọn được pack khuyến nghị.

### API và khả năng phục hồi metadata

- Dùng ATLauncher V2 GraphQL cho luồng duyệt/tìm kiếm công khai.
- Dùng API V1 và CDN manifest làm fallback cho chi tiết pack, danh sách phiên bản và dữ liệu cài đặt.
- Gửi `User-Agent` riêng của MCW Launcher theo yêu cầu của ATLauncher.
- Cache metadata có TTL, giới hạn kích thước và fallback sang cache cũ khi dịch vụ tạm thời không truy cập được.
- Chi tiết GraphQL được cô lập sau adapter để hạn chế ảnh hưởng khi schema V2 beta thay đổi.

### Cài đặt pack

- Tạo instance với đúng Minecraft version và loader được manifest khai báo: Vanilla, Forge, NeoForge, Fabric hoặc Quilt.
- Lưu registry ATLauncher riêng trong `.mcw/atlauncher-pack.json`.
- Các file pack được tải có trì hoãn ở lần Launch đầu tiên, có tối đa ba lần thử và xác minh SHA-1/MD5.
- Hiển thị progress tổng hợp thay vì spam tên từng file.
- Hỗ trợ `Configs.zip` với giải nén staging, giới hạn kích thước/số entry và chống path traversal hoặc symbolic link.
- Ghi provenance provider `atlauncher` và hiển thị nội dung đã quản lý trong Content Library.
- Áp dụng mức RAM khuyến nghị của pack vào cấu trúc settings Java đúng chuẩn khi người dùng chưa chọn override riêng.

### Giới hạn của Beta 1

Bản beta này từ chối cài và giải thích rõ nếu pack cần một trong các hành vi chưa được hỗ trợ:

- file bắt buộc tải qua trình duyệt;
- custom library hoặc custom main class;
- Java/game argument riêng của pack;
- thao tác delete/keep/extract/decomp;
- jar mod hoặc file legacy ghi trực tiếp vào root;
- quy trình cài đặt đặc biệt ngoài contract an toàn hiện tại.

Provider-native export/import ATLauncher chưa nằm trong phạm vi Beta 1. Registry nội bộ ATLauncher được loại khỏi danh sách file portable để tránh xuất nhầm metadata vận hành.

### Phiên bản

- Launcher runtime: `v1.1.1-beta.1`
- Update channel: `beta`
- Python distribution metadata: `1.1.1b1`
- Không phát hành MCW Core wheel riêng trong beta này; implementation ATLauncher được bundle trong launcher để kiểm thử trước khi đồng bộ vào bản Core stable tiếp theo.

### Xác thực

- Toàn bộ launcher test suite: `1350 passed, 86 skipped, 2 warnings`.
- Kiểm thử ATLauncher riêng: `14 passed`.
- Python `compileall`: đạt cho `src`, `mcw_core` và `test`.
- Kiểm thử có mock bao phủ GraphQL/V1 fallback, parser manifest, installer, registry, tải trì hoãn, progress tổng hợp và giải nén ZIP an toàn.
- Môi trường build không có kết nối trực tiếp ổn định tới ATLauncher và không chạy được Minecraft GUI Windows, vì vậy vẫn cần smoke test thực tế với một số pack công khai trước khi lên beta tiếp theo.

---

## English

MCW Launcher **v1.1.1-beta.1** starts the 1.1.1 line with the first phase of **ATLauncher** integration. This beta focuses on browsing, metadata, instance creation, and managed-content delivery. Packs requiring complex or legacy install actions are detected and safely rejected instead of being partially installed.

### ATLauncher provider

- Adds an ATLauncher browser to **Add Instance** and the instance toolbar.
- Searches public packs with paging, sorting, and cache status.
- Displays pack information, support website, Minecraft version, changelog, and release channel.
- Supports `release`, `beta`, and `alpha` filters.
- Requires an explicit pack-version selection before installation.
- Allows recommended optional files to be included.

### API and metadata recovery

- Uses the public ATLauncher V2 GraphQL API for browsing and search.
- Uses the V1 API and CDN manifests as fallbacks for pack details, version lists, and install data.
- Sends a dedicated MCW Launcher `User-Agent` as required by ATLauncher.
- Adds TTL-based metadata caching, a bounded cache size, and stale-cache fallback during temporary service failures.
- Keeps GraphQL schema details behind an adapter so changes to the beta V2 schema remain isolated.

### Pack installation

- Creates an instance using the Minecraft version and primary loader declared by the manifest: Vanilla, Forge, NeoForge, Fabric, or Quilt.
- Persists an ATLauncher registry in `.mcw/atlauncher-pack.json`.
- Defers managed file downloads until first Launch, with up to three attempts and SHA-1/MD5 verification.
- Reports aggregate progress instead of exposing every file name in the main progress message.
- Supports `Configs.zip` through staging extraction, entry/size limits, path-traversal protection, and symbolic-link rejection.
- Records `atlauncher` provenance and exposes managed entries in Content Library.
- Applies the pack's recommended memory to the correct nested Java settings when no explicit settings override is supplied.

### Beta 1 limitations

This beta refuses installation with a clear error when a pack requires unsupported behavior such as browser-only files, custom libraries/main classes, pack-specific Java or game arguments, delete/keep/extract/decomp actions, jar mods, legacy root files, or another special install workflow outside the current safe contract.

Provider-native ATLauncher export/import is not part of Beta 1. Internal ATLauncher registry data is excluded from portable file enumeration to avoid exporting runtime metadata as pack content.

### Version metadata

- Launcher runtime: `v1.1.1-beta.1`
- Update channel: `beta`
- Python distribution metadata: `1.1.1b1`
- No standalone MCW Core wheel is published for this beta; the ATLauncher implementation remains bundled in the launcher until the next stable Core synchronization.

### Validation

- Full launcher test suite: `1350 passed, 86 skipped, 2 warnings`.
- ATLauncher-focused tests: `14 passed`.
- Python `compileall`: passed for `src`, `mcw_core`, and `test`.
- Mocked coverage includes GraphQL/V1 fallback, manifest parsing, installation, registry persistence, deferred downloads, aggregate progress, and safe ZIP extraction.
- The build environment cannot perform a reliable live ATLauncher or Windows Minecraft GUI smoke test, so real public packs still require Windows validation before the next beta.
