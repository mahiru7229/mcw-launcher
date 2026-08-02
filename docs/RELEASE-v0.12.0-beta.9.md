# MCW Launcher v0.12.0-beta.9

## Import and Runtime Status Corrections

This beta fixes the final blockers reported before the v0.12 release-candidate cycle: Windows access-denied failures while committing imported instances, stale crash results leaking into later launches, and unclear instance runtime badges.

### Transactional package import on Windows

- Imported `.mcwpack` data is still extracted and verified entirely inside the managed staging directory.
- The final staging-to-instance directory commit now retries transient Windows sharing and access-denied errors with bounded backoff.
- A target directory that appears during commit is treated as a conflict instead of being overwritten.
- An existing orphan directory without valid instance metadata is preserved; the imported instance receives the next available name rather than deleting unknown data.
- Failed commits keep the original package untouched and roll back staging without adding a partial instance to the registry.

### Duplicate archive members

- Byte-identical duplicate ZIP members are extracted only once.
- Conflicting duplicate paths are rejected before any package files are written.
- Case-insensitive path collision protection remains enabled for Windows compatibility.

### Runtime badges

Instance artwork now follows one unambiguous lifecycle:

- never launched: no badge;
- preparing or downloading: loading badge;
- Minecraft process active: running badge;
- latest completed session exited normally: success tick;
- latest completed session crashed: error badge.

Runtime state always takes precedence over the previous completed-session result. The workspace refreshes its running-state snapshot as soon as launch progress begins.

### Session-scoped crash detection

- Crash-report files are snapshotted before Java starts.
- Only reports created or changed during the current launch session can mark that session as crashed.
- A previous crash report can no longer make a later successful run appear crashed.
- Each completed result is associated with its process-session ID.
- A stale watcher cannot overwrite metadata belonging to a newer session.
- Launcher-requested process stops are not classified as crashes solely because Java returns a non-zero termination code.

## Metadata

```text
VERSION = v0.12.0-beta.9
VERSION_ID = 0.12.0-beta.9
UPDATE_CHANNEL = beta
```

## Suggested commit

```text
fix: correct package import commits and runtime status lifecycle
```

## Windows copy-commit hotfix

A second diagnostics capture showed that extraction completed successfully, but Windows kept one or more nested mod JARs open long enough to block renaming the staging directory after all rename retries. The import transaction now has an application-level copy-commit fallback:

- directory rename remains the preferred fast path;
- after persistent Windows sharing/access errors, files are copied into a fresh target directory;
- `instance.json` is published last, so the launcher cannot discover a half-copied instance;
- each file copy uses a temporary `.part` path, bounded retry, flush, and atomic replacement;
- the source staging directory is removed best-effort and is otherwise cleaned by startup recovery;
- a failed fallback removes the unpublished target and never updates the instance registry.

This specifically avoids the Windows rule where an antivirus, indexer, or JAR scanner can allow file reads while denying deletion/rename sharing on the parent directory.
