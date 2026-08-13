# MCW Launcher v1.4.1

MCW Launcher **v1.4.1** is a stable maintenance release for the v1.4 line. It promotes the Java recovery/provisioning and Diagnostics v2.1 work from v1.4.1-beta.1 and beta.2 without adding unrelated feature work.

## Highlights

- Automatic Java 8 recovery prefers an MCW-managed Temurin runtime instead of allowing an obsolete PATH Java to block managed provisioning.
- Explicit user-selected Java remains respected when compatible; automatic recovery records the runtime decision and provisioning timeline.
- Java metadata, download/SHA-256, extraction, and installation failures are classified by stage for clearer recovery errors.
- Java scanning prefers the console `java.exe` probe over `javaw.exe` where available, preventing broken/stale Java candidates from displaying a JVM GUI error during background scan or Diagnostics export.
- Managed Java archive extraction uses a fresh child destination inside the short workspace, fixing Windows `WinError 183` collisions.
- Diagnostics v2.1 sanitizes filesystem locations to aliases such as `root/...`, `temp/...`, and `external/...`, avoiding direct drive letters, UNC share names, and unnecessary user paths in public bundles.
- Runtime/crash log attachments include truncation metadata, with stronger player/UUID/path redaction; Forge/NeoForge installer logs and Java recovery evidence are included when available.
- Diagnostics collectors are isolated so one failing collector does not invalidate the whole bundle.
- User cancellation is represented as cancelled in task diagnostics rather than a generic failed download.

## Compatibility

- Launcher runtime: `v1.4.1`
- Update channel: `stable`
- Python distribution: `mcw-core 1.4.1`
- No account, instance, theme, or modpack-format migration is required.

## Validation

Stable release artifacts are validated with the full pytest suite, compileall, release preflight, package re-extraction, and an isolated MCW Core wheel import/smoke test. Windows PyInstaller executable generation remains a Windows release-workflow step.
