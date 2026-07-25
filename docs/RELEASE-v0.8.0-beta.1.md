# MCW Launcher v0.8.0 Beta 1

## Tiếng Việt

`v0.8.0-beta.1` thay thử nghiệm Hybrid Mode và bản thử LAN World Plug-n-Play trước đó bằng **MCW LAN Agent** do launcher tự quản lý.

### Private Group LAN

Trong **Instance Settings → LAN hosting**:

- **Microsoft accounts only**: giữ nguyên xác minh phiên Minecraft chính thức.
- **Private group — Microsoft and Offline accounts**: launcher gắn một Java Agent tối giản khi khởi chạy game. Agent ép integrated server của **Open to LAN** giữ `usesAuthentication = false`.

Phương thức kết nối vẫn tách riêng:

- **Manual connection**: LAN, VPN riêng, mở port hoặc relay khác.
- **e4mc tunnel**: launcher cài e4mc vào instance host; e4mc chỉ tạo tunnel.

### Cơ chế kỹ thuật

Khi Private Group được bật, command có thêm:

```text
-Dmcw.lan.offline=true
-Dmcw.lan.target.class=net/minecraft/server/MinecraftServer
-Dmcw.lan.target.method=setUsesAuthentication
-javaagent:<cache>/runtime/agents/mcw-lan-agent/mcw-lan-agent.jar
```

Agent chỉ sửa setter boolean tương ứng trong RAM:

```text
setUsesAuthentication(true)
→ setUsesAuthentication(false)
```

Agent **không**:

- thay Authlib;
- đọc hoặc ghi access token/refresh token;
- redirect Minecraft Session Service;
- tải code từ Internet;
- sửa Minecraft JAR trên ổ đĩa;
- phụ thuộc Fabric hoặc Forge để thực hiện patch LAN.

JAR agent được bundle trong launcher, kiểm tra SHA-256 trước khi sao chép vào cache và trước khi nạp. Custom JVM arguments không được phép ghi đè các property riêng của MCW LAN Agent.

### Migration từ bản thử trước

- Không còn cài `mcwifipnp` để xử lý authentication.
- `mcwifipnp` hoặc LAN auth bridge do bản beta thử trước quản lý sẽ tự bị vô hiệu hóa khi Private Group được chạy hoặc Prepare lại.
- e4mc vẫn được giữ nếu người dùng chọn e4mc tunnel.
- Cấu hình cũ `lan_auth_mode = "friends"` vẫn được chuyển thành `private_offline`.

### Cách sử dụng

1. Mở **Instance Settings → LAN hosting**.
2. Chọn **Private group — Microsoft and Offline accounts**.
3. Chọn **Manual connection** hoặc **e4mc tunnel**.
4. Nhấn **Prepare hosting support**.
5. Khởi chạy Minecraft và mở world ra LAN như bình thường.
6. Kiểm tra log game có dòng:

```text
[MCW LAN Agent] patched net.minecraft.server.MinecraftServer#setUsesAuthentication(boolean)
```

7. Chỉ chia sẻ địa chỉ với người đáng tin.

### Phạm vi Beta

- Bản agent đầu tiên được xác minh với runtime có class/method được đặt tên như Minecraft `26.2`.
- Trước khi launch, MCW kiểm tra client JAR có target tương thích. Nếu không tương thích, launcher dừng an toàn và không patch một phần.
- Các phiên bản Minecraft obfuscated cũ chưa được hỗ trợ trong bản thử này; mapping resolver rộng hơn sẽ được làm sau khi cơ chế 26.2 được test thực tế.
- Offline Mode dùng Offline UUID. Inventory, advancement và statistics có thể tách khỏi profile Microsoft; hãy backup world trước khi thử.
- Ai biết địa chỉ có thể dùng username khác. Chế độ này chỉ dành cho nhóm riêng.

### Kiểm thử

```text
812 passed, 48 skipped
```

Java Agent smoke test:

```text
Không gắn agent: setUsesAuthentication(true) → true
Có gắn agent:    setUsesAuthentication(true) → false
```

Không có `failed` hoặc `error`.

---

## English

`v0.8.0-beta.1` replaces the unreliable Hybrid Mode experiment and the earlier LAN World Plug-n-Play test patch with a launcher-managed **MCW LAN Agent**.

### Private Group LAN

Under **Instance Settings → LAN hosting**:

- **Microsoft accounts only**: keep official Minecraft session verification unchanged.
- **Private group — Microsoft and Offline accounts**: attach a minimal Java Agent when the game starts. The agent forces the integrated **Open to LAN** server to keep `usesAuthentication = false`.

Connection transport remains separate:

- **Manual connection**: LAN, a private VPN, port forwarding, or another relay.
- **e4mc tunnel**: install e4mc in the host instance; e4mc only provides the tunnel.

### Technical design

Private Group adds these launch arguments:

```text
-Dmcw.lan.offline=true
-Dmcw.lan.target.class=net/minecraft/server/MinecraftServer
-Dmcw.lan.target.method=setUsesAuthentication
-javaagent:<cache>/runtime/agents/mcw-lan-agent/mcw-lan-agent.jar
```

The agent changes only the matching boolean setter in memory:

```text
setUsesAuthentication(true)
→ setUsesAuthentication(false)
```

The agent does **not**:

- replace Authlib;
- read or write access/refresh tokens;
- redirect Minecraft Session Service;
- download code from the Internet;
- modify the Minecraft JAR on disk;
- depend on Fabric or Forge for the LAN patch itself.

The agent JAR is bundled with the launcher, SHA-256 verified before being copied into cache, and verified again before use. Custom JVM arguments cannot override the MCW LAN Agent properties.

### Migration from the earlier test patch

- `mcwifipnp` is no longer installed as the authentication component.
- A launcher-managed `mcwifipnp` or older LAN auth bridge is automatically disabled when Private Group runs or hosting support is prepared again.
- e4mc remains enabled when the e4mc tunnel is selected.
- Legacy `lan_auth_mode = "friends"` settings still migrate to `private_offline`.

### Usage

1. Open **Instance Settings → LAN hosting**.
2. Select **Private group — Microsoft and Offline accounts**.
3. Select **Manual connection** or **e4mc tunnel**.
4. Click **Prepare hosting support**.
5. Launch Minecraft and open the world to LAN normally.
6. Confirm the game log contains:

```text
[MCW LAN Agent] patched net.minecraft.server.MinecraftServer#setUsesAuthentication(boolean)
```

7. Share the address only with trusted people.

### Beta scope

- This first agent build is verified against a runtime exposing the named class and method used by Minecraft `26.2`.
- Before launch, MCW checks that the client JAR contains a compatible target. An unsupported version fails safely instead of receiving a partial patch.
- Older obfuscated Minecraft versions are not supported by this experiment yet; broader mapping resolution can follow after the 26.2 path is tested in game.
- Offline Mode uses Offline UUIDs. Inventory, advancements, and statistics may be separate from the Microsoft profile; back up the world first.
- Anyone with the address can use another username. This mode is intended only for private groups.

### Tests

```text
812 passed, 48 skipped
```

Java Agent smoke test:

```text
Without agent: setUsesAuthentication(true) → true
With agent:    setUsesAuthentication(true) → false
```

No `failed` or `error` results.
