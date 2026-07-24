# MCW Launcher 0.7 Roadmap

## v0.7.0 Stable — CurseForge Gateway and provider cache

Status: **implemented and release-ready**.

- [x] CurseForge integration without a bundled API key or private gateway URL
- [x] Five external HTTPS gateway slots with ordered failover
- [x] Windows DPAPI protection for locally saved gateway links
- [x] Masked gateway fields and localized five-second reveal confirmation
- [x] CurseForge mod search
- [x] Compatible file/version selection for Fabric and Forge
- [x] Automatic download when third-party distribution is permitted
- [x] Manual mod download and SHA-1 verification fallback
- [x] Local JSON cache
- [x] 10 MiB cache limit with LRU eviction
- [x] Last-refreshed timestamp and cache source display
- [x] Refresh cooldown, failure backoff and request deduplication
- [x] Stale-cache fallback when every gateway is temporarily unavailable
- [x] Batch project/file metadata requests
- [x] Modern Forge command/module-path hardening

## v0.7.2 Stable — Offline/Forge maintenance

- [x] Restore Offline account launches on Forge.
- [x] Remove invalid authentication host overrides from legacy settings.
- [x] Preserve Microsoft account behavior.
- [x] Keep updater compatibility with both three-part and four-part historical versions.

## v0.7.3 — Optimization and maintenance

Planned focus after the v0.7.2 maintenance release:

- Reduce CurseForge catalog latency and unnecessary refreshes.
- Improve endpoint health tracking and prefer the most recently healthy gateway without weakening configured priority.
- Optimize JSON cache reads, cleanup and startup behavior.
- Expand provider diagnostics without exposing private gateway links.
- Improve CurseForge modpack compatibility and recovery.
- Continue performance profiling for launch, repair and update flows.

## v0.7.3 Beta 1 — LAN hosting profiles

- Separate LAN authentication policy from connection transport.
- Support Microsoft-only and trusted-friends Offline-compatible hosting without MCW Verified Auth.
- Manage LAN Properties and optional e4mc through compatible Modrinth Release builds.
- Keep manual LAN, VPN, direct-port, and custom-relay workflows available when e4mc is not used.
