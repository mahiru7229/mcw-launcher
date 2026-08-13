# MCW Launcher v1.4.1-beta.1

MCW Launcher **v1.4.1-beta.1** is the single beta planned for the 1.4.1 maintenance line. It focuses on managed Java recovery and Diagnostics v2.1.

## Java recovery / managed download

- Automatic Java 8 operations now use an MCW-managed Temurin 8 runtime when one is not already installed. A legacy Java 8 found on `PATH`, `JAVA_HOME`, or the registry no longer prevents managed provisioning.
- Explicit user-selected Java remains supported when its major version is compatible.
- Recovery prefers an existing managed runtime, then provisions a managed runtime, and only falls back to another external runtime if managed provisioning is unavailable or the managed runtime itself was the failed candidate.
- Java candidate selection consistently honors source priority.
- Managed Java provisioning reports separate metadata, download/SHA-256, and extraction/install failures.
- A bounded Java recovery trace records decisions, download host, expected size, checksum stage, selected installer Java, attempt count, and return code for diagnostics.

## Diagnostics v2.1

- Diagnostic paths use privacy aliases such as `root/...`, `temp/...`, `user/...`, and `external/...`. Windows drive letters and UNC server/share names are not exported directly.
- The same sanitizer is applied to launcher logs, runtime/crash logs, loader installer logs, issue drafts, structured paths, and tracebacks.
- Runtime attachments include `runtime/metadata.json` with original size, included size, and truncation state.
- Recent Forge/NeoForge installer logs and Java recovery events are included.
- `diagnostic-summary.json` provides a small rule-based summary of recent Java recovery/task state.
- Collector failures are isolated and recorded in `collector-errors.json` instead of aborting the entire bundle.
- Runtime logs additionally redact obvious player names and UUIDs.
- Core/user cancellation exceptions are classified as `cancelled` in task diagnostics rather than generic failures.
- System diagnostics include currently available memory and disk free percentage in addition to the existing hardware data.

## Compatibility

This beta retains all v1.4.0 task lifecycle, Kill Instance, update-priority, adaptive download, Forge profile hardening, issue reporting, and progress-state fixes. No new feature family is introduced.

## Version

- Launcher runtime: `v1.4.1-beta.1`
- Update channel: `beta`
- Python package metadata: `1.4.1b1`
