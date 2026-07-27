# MCW Launcher v0.8.0 Beta 2

## Tiếng Việt

`v0.8.0-beta.2` mở rộng **MCW LAN Agent** từ runtime đặt tên mới sang các phiên bản Minecraft hiện đại còn obfuscation, bắt đầu từ **Minecraft 1.17 trở lên**.

### Mapping resolver mới

Launcher không còn hard-code duy nhất:

```text
net.minecraft.server.MinecraftServer#setUsesAuthentication(Z)V
```

Thay vào đó, khi host bật **Private group — Microsoft and Offline accounts**, launcher tạo danh sách target theo runtime:

- **Named runtime**: thử cả `setUsesAuthentication(boolean)` và tên cũ `setOnlineMode(boolean)`.
- **Mojang/official runtime**: tải và kiểm tra `client_mappings` chính thức của đúng Minecraft version, sau đó lấy tên method production tương ứng.
- **Fabric runtime**: đọc `mappings/mappings.tiny` từ thư viện `net.fabricmc:intermediary` đã tải, rồi chuyển target official sang intermediary.
- **Forge runtime**: đọc cặp `client-...-slim.jar` và `client-...-srg.jar` do Forge cài đặt, đối chiếu cùng vị trí method để chuyển target official sang tên SRG production.

Command mới sử dụng nhiều candidate an toàn:

```text
-Dmcw.lan.offline=true
-Dmcw.lan.targets=<class#method;class#method;...>
-Dmcw.lan.log=<instance>/logs/mcw-lan-agent.log
-javaagent:<cache>/runtime/agents/mcw-lan-agent/mcw-lan-agent.jar
```

Agent chỉ patch candidate có đúng class, đúng method descriptor `(Z)V`, và đúng mẫu setter ghi vào field boolean. Các candidate còn lại được bỏ qua.

### Hỗ trợ phiên bản

- Minecraft **1.17 trở lên**: được đưa vào phạm vi resolver mới.
- Minecraft **1.16.5 trở xuống**: agent không được gắn; game vẫn launch bình thường và log giải thích giới hạn.
- Fabric 1.20.1: resolver có thể chuyển `setOnlineMode` sang intermediary method tương ứng.
- Minecraft 26.1+ hoặc runtime đã đặt tên: vẫn dùng target named như Beta 1.

### Fail-safe và log

Static preflight cứng của Beta 1 đã được loại bỏ. Mapping không chắc chắn không còn khiến Forge hoặc Minecraft cũ bị chặn trước khi vào game.

Log mới ghi:

```text
[MCW Launcher] Mapping profile: Minecraft 1.20.1; loader=fabric; candidates=...
[MCW Launcher] Resolved target [intermediary]: ...#method_...(Z)V
[MCW Launcher] Resolved target [official]: ...#...(Z)V
[MCW LAN Agent] enabled with ... resolved target candidate(s)
[MCW LAN Agent] patched ...#...(boolean)
```

Nếu không target nào khớp, Minecraft vẫn chạy nguyên bản và log ghi rõ mapping/runtime chưa tương thích.

### Download và integrity

- Mojang client mappings được cache theo Minecraft version.
- Download mapping sử dụng downloader chung của launcher, có progress và SHA-1 verification.
- Fabric intermediary mapping được đọc từ thư viện đã tải cho chính instance đó.
- Agent JAR tiếp tục được bundle và kiểm tra SHA-256 trước khi nạp.

### Kiểm thử

```text
820 passed, 48 skipped
```

- Parser Mojang ProGuard mapping.
- Parser Fabric Tiny v1 và Tiny v2.
- Candidate resolution cho Fabric 1.20.1 và Forge 1.20.1, bao gồm target SRG `m_129985_(Z)V` từ artifact Forge thật.
- Legacy version dưới 1.17 không chặn launch.
- Java smoke test với nhiều target candidate.

---

## English

`v0.8.0-beta.2` expands the **MCW LAN Agent** from newly named runtimes to modern obfuscated Minecraft releases, starting with **Minecraft 1.17 and newer**.

### New mapping resolver

The launcher no longer hard-codes only:

```text
net.minecraft.server.MinecraftServer#setUsesAuthentication(Z)V
```

When the host enables **Private group — Microsoft and Offline accounts**, the launcher now builds runtime-specific candidates:

- **Named runtime**: tries both `setUsesAuthentication(boolean)` and the older `setOnlineMode(boolean)` name.
- **Mojang/official runtime**: downloads the official `client_mappings` for the exact Minecraft version and resolves the production method name.
- **Fabric runtime**: reads `mappings/mappings.tiny` from the downloaded `net.fabricmc:intermediary` library and converts the official target to intermediary.
- **Forge runtime**: tries both named and official candidates so ModLauncher can expose whichever namespace that release uses.

The launch command now supplies multiple safe candidates:

```text
-Dmcw.lan.offline=true
-Dmcw.lan.targets=<class#method;class#method;...>
-Dmcw.lan.log=<instance>/logs/mcw-lan-agent.log
-javaagent:<cache>/runtime/agents/mcw-lan-agent/mcw-lan-agent.jar
```

The agent patches only a candidate with the correct class, `(Z)V` descriptor, and boolean-field setter shape. Other candidates are ignored.

### Version support

- Minecraft **1.17 and newer**: included in the new resolver scope.
- Minecraft **1.16.5 and older**: the agent is not attached; the game still launches and the log explains the limit.
- Fabric 1.20.1: the resolver can translate `setOnlineMode` to its intermediary runtime method.
- Minecraft 26.1+ or already named runtimes: continue using the named target from Beta 1.

### Fail-safe behavior and diagnostics

Beta 1's hard static preflight has been removed. An uncertain mapping no longer blocks Forge or an older Minecraft version before the game starts.

The dedicated log now records the mapping profile, every resolved candidate, the class loader that exposes the target, and the exact candidate that was patched. When no candidate matches, Minecraft remains unchanged and continues running.

### Downloads and integrity

- Mojang client mappings are cached per Minecraft version.
- Mapping downloads use the launcher's shared downloader with progress and SHA-1 verification.
- Fabric intermediary mappings are read from the libraries already downloaded for that instance.
- The bundled agent JAR remains SHA-256 verified before loading.

### Tests

```text
820 passed, 48 skipped
```

- Mojang ProGuard mapping parser.
- Fabric Tiny v1 and Tiny v2 parsers.
- Fabric 1.20.1 and Forge 1.20.1 target resolution, including the real Forge SRG target `m_129985_(Z)V`.
- Pre-1.17 versions do not block launch.
- Multi-target Java Agent smoke test.
## Beta 2 mapping hotfix

- Fixed Fabric Tiny v1 parsing when an identity class mapping is omitted.
- Fabric 1.20.1 can now resolve `MinecraftServer#d(Z)V` to `method_3864(Z)V`.
- Added regression coverage using the same owner/method layout as the published Fabric 1.20.1 intermediary mapping.


## Beta 2 Forge SRG hotfix

### Tiếng Việt

- Xác định từ artifact Forge 1.20.1 thật rằng runtime dùng namespace `srg`.
- Resolver đọc `--fml.mcpVersion` trong version metadata để tìm đúng thư mục `net/minecraft/client/<mc>-<mcp>`.
- Đối chiếu method table giữa `client-...-slim.jar` và `client-...-srg.jar`; chỉ chấp nhận khi số lượng method khớp, method official là duy nhất và descriptor vẫn là `(Z)V`.
- Forge 1.20.1 hiện resolve `MinecraftServer#d(Z)V` thành `MinecraftServer#m_129985_(Z)V`.
- Nếu artifact thiếu hoặc cấu trúc không khớp, resolver chỉ ghi warning và giữ nguyên Minecraft.

### English

- Confirmed from real Forge 1.20.1 artifacts that the production runtime uses the `srg` naming domain.
- The resolver reads `--fml.mcpVersion` from version metadata to locate `net/minecraft/client/<mc>-<mcp>`.
- It correlates the method tables in `client-...-slim.jar` and `client-...-srg.jar`; resolution is accepted only when the method counts match, the official method is unique, and the descriptor remains `(Z)V`.
- Forge 1.20.1 now resolves `MinecraftServer#d(Z)V` to `MinecraftServer#m_129985_(Z)V`.
- Missing or mismatched artifacts produce a warning and leave Minecraft unchanged.
