# MCW Launcher v1.4.0-beta.3

## Tiếng Việt

MCW Launcher **v1.4.0-beta.3** tập trung vào Diagnostics v2 và quy trình báo lỗi có hướng dẫn.

### Thay đổi chính

- **Report Issue wizard**: bấm Báo cáo lỗi sẽ mở bước nhập tiêu đề, mô tả, cách tái hiện, kết quả mong đợi và thực tế trước khi thu thập diagnostics.
- Diagnostics được tạo bằng background task để không khóa UI; sau khi xong mới chuyển sang bước hướng dẫn.
- Bước hướng dẫn hiển thị vị trí ZIP, mẫu issue đã điền, nút copy, mở thư mục ZIP và mở GitHub New Issue đã prefill title/body.
- Error dialog có nút **Báo cáo lỗi** để prefill lỗi gần nhất vào wizard.
- Diagnostics schema v2 bổ sung `system-info.json`, `java-runtimes.json`, `task-timeline.json`, `issue-context.json`, runtime Minecraft log/crash report gần nhất, bên cạnh launcher log, process sessions, instance health và recovery journals.
- TaskRunner giữ timeline bounded 100 task gần nhất, gồm trạng thái, thời lượng, cancellation/supersede và loại lỗi.
- Secret redaction tiếp tục áp dụng cho issue text, settings, logs và JSON diagnostics; bundle vẫn giới hạn log size/count.
- Giữ toàn bộ fix/tối ưu của beta.1 và beta.2, gồm issue #19/#20, Kill Instance, shutdown cancellation, Update Priority Mode, adaptive Modrinth download, one-pass hashing và journal batching.

### Ghi chú beta

Beta/RC chỉ phát hành Launcher patch/source theo workflow dự án; standalone MCW Core artifact chỉ được build lại khi v1.4 stable.

---

## English

MCW Launcher **v1.4.0-beta.3** is focused on Diagnostics v2 and a guided issue-reporting workflow.

### Highlights

- The **Report Issue** action first opens a form for title, description, reproduction steps, expected behavior and actual behavior.
- Diagnostic collection runs in a background launcher task; guidance is shown only after collection completes.
- The guidance step shows the ZIP path, a generated issue draft, copy/open-folder actions and a prefilled GitHub New Issue action.
- Error dialogs expose a **Report issue** action that prefills the most recent error context.
- Diagnostics schema v2 adds system info, Java runtimes, task timeline, issue context and recent Minecraft runtime/crash logs.
- The TaskRunner keeps a bounded 100-entry lifecycle timeline with duration/cancellation/supersede/error metadata.
- Privacy redaction and bounded log collection remain enforced.
- All beta.1/beta.2 fixes and performance work remain included.
