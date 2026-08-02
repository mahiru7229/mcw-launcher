# MCW Launcher v0.12.0-beta.8

## Final Stability Hardening

This beta completes the stability work planned before the v0.12 release-candidate cycle. It focuses on supervised Minecraft processes, fast instance-health diagnostics, startup recovery, and safer diagnostic exports.

### Process supervision

- Every launch receives a persisted process-session ID.
- Preparing, running, stopping, finished, crashed, and interrupted sessions are recorded separately from instance metadata.
- The runtime manager archives the session result when Minecraft exits.
- Startup recovery reconciles sessions left behind by an interrupted launcher.
- Stop and delete flows can reuse the supervised process without terminating unrelated Java processes.
- A failure after Java starts but before runtime registration now stops the process, aborts the session, and releases the instance lock.

### Instance health

A fast local health scan reports:

- healthy instances;
- metadata migration requirements;
- invalid metadata or settings;
- missing configured Java executables;
- incomplete mod-loader metadata;
- unfinished instance-operation journals;
- missing custom icons;
- previous crashed sessions.

Runtime state and persistent health remain separate, so an instance can show both `Running` and a repair warning.

### Startup and download recovery

- Startup recovery now reconciles supervised sessions.
- Invalid or completed download-journal entries are cleaned safely.
- Old unreferenced `.part` artifacts are removed only from managed cache/instance roots.
- Fresh partial files, journal-referenced downloads, and unknown file types remain untouched.

### Diagnostics

The diagnostic ZIP now includes:

- `instance-health.json`;
- `process-sessions.json`;
- `operation-journals.json`;
- the existing redacted report, download recovery data, and bounded log tails.

Absolute paths in health issues are converted to safe application-relative paths. Invalid journals are reported without including their untrusted contents.

### Public MCW Core API

The headless package now exposes:

- `InstanceHealthState`, `InstanceHealthIssue`, and `InstanceHealthReport`;
- `ProcessSession` and `ProcessSessionState`;
- `core.instances.health(...)` and `core.instances.list_health()`.

Core remains GUI-independent and importable without PySide6.

## Metadata

```text
VERSION = v0.12.0-beta.8
VERSION_ID = 0.12.0-beta.8
UPDATE_CHANNEL = beta
```

## Suggested commit

```text
feat: harden process supervision and instance recovery
```
