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

## v0.7.1 — Optimization and maintenance

Planned focus after the successful v0.7.0 feature validation:

- Reduce CurseForge catalog latency and unnecessary refreshes.
- Improve endpoint health tracking and prefer the most recently healthy gateway without weakening configured priority.
- Optimize JSON cache reads, cleanup and startup behavior.
- Expand provider diagnostics without exposing private gateway links.
- Improve CurseForge modpack compatibility and recovery.
- Continue performance profiling for launch, repair and update flows.
