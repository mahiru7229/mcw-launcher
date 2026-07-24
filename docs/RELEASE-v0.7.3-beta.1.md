# MCW Launcher v0.7.3 Beta 1

## Tiếng Việt

`v0.7.3-beta.1` là bản thử nghiệm đầu tiên cho luồng **host LAN không cần MCW Verified Auth**. Bản này tách chính sách xác thực khỏi phương thức kết nối, để e4mc chỉ là một lựa chọn tunnel có thể thay thế về sau.

### LAN hosting profiles

Trong **Instance Settings → LAN hosting**, mỗi instance Fabric hoặc Forge có hai nhóm lựa chọn độc lập:

- **Chính sách xác thực**
  - `Microsoft accounts only`: giữ xác minh phiên Minecraft mặc định.
  - `Friends — Microsoft and Offline accounts`: launcher cài **LAN Properties** để host có thể tắt `online-mode` và bật `hybrid-mode` khi mở world ra LAN.
- **Phương thức kết nối**
  - `Manual connection`: dùng LAN, VPN riêng, mở port hoặc relay riêng.
  - `e4mc tunnel`: launcher cài e4mc vào instance host.

Nút **Prepare hosting support** tải bản Release tương thích từ Modrinth, cài dependency cần thiết, tái sử dụng file đã đúng phiên bản và vô hiệu hóa component do launcher quản lý khi không còn được chọn.

### Quy trình Friends mode

1. Chọn `Friends — Microsoft and Offline accounts`.
2. Chọn `Manual connection` hoặc `e4mc tunnel`.
3. Nhấn **Prepare hosting support** và xác nhận cảnh báo bảo mật.
4. Mở Minecraft, vào world và chọn **Open to LAN**.
5. Trong cấu hình LAN Properties, đặt `online-mode = Off` và `hybrid-mode = On`.
6. Chia sẻ địa chỉ LAN/VPN/relay hoặc domain e4mc.

Chế độ này không sử dụng MCW Auth Server. Username Offline không được xác minh mạnh và có thể bị giả mạo, vì vậy chỉ nên dùng với nhóm đáng tin cậy, ưu tiên mạng riêng/whitelist và luôn backup world.

### Phạm vi Beta

- Hỗ trợ instance Fabric và Forge.
- Không tự thay đổi world hoặc bật offline-compatible mode một cách bí mật.
- Không bundling JAR của bên thứ ba; launcher tải bản tương thích từ Modrinth khi người dùng yêu cầu.
- e4mc không phải dependency bắt buộc; có thể thay bằng VPN, port forwarding hoặc relay khác.

---

## English

`v0.7.3-beta.1` introduces the first **LAN hosting workflow without MCW Verified Auth**. Authentication policy is separated from connection transport, so e4mc remains an optional and replaceable tunnel provider.

### LAN hosting profiles

Under **Instance Settings → LAN hosting**, each Fabric or Forge instance has two independent selections:

- **Authentication policy**
  - `Microsoft accounts only`: keep standard Minecraft session verification.
  - `Friends — Microsoft and Offline accounts`: install **LAN Properties**, allowing the host to disable `online-mode` and enable `hybrid-mode` when opening the world to LAN.
- **Connection provider**
  - `Manual connection`: use LAN, a private VPN, direct port forwarding, or another relay.
  - `e4mc tunnel`: install e4mc in the host instance.

**Prepare hosting support** downloads compatible Release builds from Modrinth, installs required dependencies, reuses an already-correct installation, and disables launcher-managed components that are no longer selected.

### Friends-mode workflow

1. Select `Friends — Microsoft and Offline accounts`.
2. Select `Manual connection` or `e4mc tunnel`.
3. Click **Prepare hosting support** and confirm the security warning.
4. Launch Minecraft, enter the world, and choose **Open to LAN**.
5. In LAN Properties configuration, set `online-mode = Off` and `hybrid-mode = On`.
6. Share the LAN/VPN/relay address or e4mc domain.

This mode does not use an MCW Auth Server. Offline usernames are not strongly verified and can be impersonated, so use it only with trusted players, prefer a private network or whitelist, and keep world backups.

### Beta scope

- Fabric and Forge instances are supported.
- The launcher does not silently alter a world or enable offline-compatible mode.
- Third-party JARs are not bundled; compatible versions are downloaded from Modrinth on explicit request.
- e4mc is optional and can be replaced by a VPN, port forwarding, or another relay.
