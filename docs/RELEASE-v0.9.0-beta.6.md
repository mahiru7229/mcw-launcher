# MCW Launcher v0.9.0-beta.6

## Release Hardening

- Exports a privacy-filtered diagnostic ZIP bundle instead of a single text file.
- Includes the launcher report, sanitized download-recovery state, and a bounded set of recent log tails.
- Excludes account storage, worlds, mod JAR contents, and configuration files outside the report's safe allowlist.
- Redacts bearer tokens, OAuth codes, refresh/access tokens, passwords, client secrets, and JWT-like values.
- Caps log count, per-log bytes, and total bundled log bytes.
- Writes bundles atomically, validates ZIP integrity, rejects unsafe archive paths, and records SHA-256 plus byte size for every payload.

## RC readiness

This beta keeps features unfrozen for final tester feedback. If no blocker is found, the next milestone can be `v0.9.0-rc.1` with feature freeze and release-candidate validation.
