# CurseForge Gateway integration

MCW Launcher `v0.7.0` provides CurseForge browsing and installation without bundling a CurseForge API key or a private gateway URL in the source, EXE, or updater package.

## Architecture

```text
MCW Launcher
    │ HTTPS JSON
    ▼
Private CurseForge Gateway 1
    │ unavailable? try Gateway 2 → 3 → 4 → 5
    ▼
CurseForge API
```

The real CurseForge API key remains on the gateway server. Mod files are not proxied through the gateway: it returns metadata or download URLs and MCW Launcher's normal downloader fetches the file directly, reports progress, retries, and verifies SHA-1.

## Private endpoint configuration

No gateway is configured by default. Open **Launcher Settings → Private CurseForge gateways** and enter up to five HTTPS endpoints in priority order.

The launcher stores them in:

```text
config/private/curseforge_endpoints.json
```

Values are protected with Windows DPAPI and can only be decrypted by the Windows account that saved them. The file is excluded from Git and is not copied into release packages.

All five fields are masked by default. Enabling **Reveal protected gateway links** opens a localized warning message. The confirmation button remains disabled for five seconds before the links may be shown.

For managed deployments, these environment variables are also supported:

```text
MCW_CURSEFORGE_GATEWAY_URL_1
MCW_CURSEFORGE_GATEWAY_URL_2
MCW_CURSEFORGE_GATEWAY_URL_3
MCW_CURSEFORGE_GATEWAY_URL_4
MCW_CURSEFORGE_GATEWAY_URL_5
MCW_CURSEFORGE_CLIENT_TOKEN
```

The legacy single variable `MCW_CURSEFORGE_GATEWAY_URL` remains readable for compatibility.

> DPAPI protects values at rest and masking reduces accidental on-screen exposure. A desktop client cannot make an endpoint permanently secret from someone who controls the same Windows account or can inspect its network traffic.

## Failover policy

Requests use endpoints in the configured order. The launcher tries the next endpoint when the current one has:

- a connection or TLS failure;
- invalid JSON/invalid response data;
- HTTP `404`, `408`, `425`, `429`, or `5xx` status.

Authentication and request errors such as HTTP `400`, `401`, or `403` are not sprayed across every endpoint. This avoids unnecessary traffic when the same credentials or request would fail everywhere.

## Supported workflow

- Search CurseForge projects through the private gateway.
- Filter compatible files by Minecraft version, Fabric/Forge loader, and release channel.
- Fetch project/file metadata in batches where possible.
- Install required CurseForge mod dependencies.
- Download automatically when `downloadUrl` is available and third-party distribution is permitted.
- If automatic distribution is unavailable, open the official project page and allow the user to select the downloaded `.jar`.
- Validate manually selected files by expected byte size and SHA-1 before adding them to the instance.
- Track installed and pending files in the CurseForge registry.

The manual-download flow is implemented for mods. CurseForge modpack handling remains experimental and should be tested on copied instances.

## Local JSON cache

CurseForge responses are stored under the launcher cache directory:

```text
cache/content/curseforge/api-v2/
├── index.json
└── entries/
```

Policy:

- Maximum disk size: `10 MiB`.
- Cleanup target: `8 MiB`.
- Eviction: least recently used entries first.
- Search TTL: 30 minutes.
- File lists: 1 hour.
- Project metadata: 12 hours.
- File metadata: 24 hours.
- Download URLs are resolved at install time and are not retained as permanent download authority.
- Cache writes use temporary files and atomic replacement.
- Invalid cache schema/data is discarded safely.

If every configured gateway is temporarily unavailable, stale cached data may remain visible instead of clearing the page.

## Security and privacy

The cache and diagnostics must never contain:

- private gateway URLs;
- CurseForge API keys;
- client authorization tokens;
- Microsoft access or refresh tokens;
- account databases;
- private worlds or instance saves.

Only public project/file metadata is cached. The server-side CurseForge API key is never returned to the launcher.
