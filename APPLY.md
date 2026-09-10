# MCW Update Bridge v1.3.0 checksum CI fix

Fixes cross-platform SHA-256 sidecar verification when the Windows build writes CRLF line endings.

Changes:
- Generate `.sha256` sidecars with raw ASCII bytes and LF-only newlines.
- Normalize any `\r` bytes in downloaded sidecars before Linux `sha256sum --check`.

Apply this patch at the repository root, commit, push, then rerun the `Build MCW Update Bridge` workflow.
