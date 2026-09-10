# MCW Update Bridge v1.5.0

MCW Update Bridge v1.5.0 is the recovery companion for MCW Launcher `v1.5.1-beta.6`.

- Windows x64 and Linux x64 builds are produced from the same bridge source.
- Default target: `v1.5.1-beta.6`.
- Runtime `--tag` remains supported for an explicitly selected recovery release.
- SHA-256 sidecars are written with LF line endings on every runner.
- The publish job normalizes legacy CRLF sidecars and supplies `--repo` to GitHub CLI so it does not require a `.git` checkout.
- `MCW-USE-BRIDGE` is uploaded only when the maintainer explicitly enables the emergency override input.
