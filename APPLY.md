# MCW Update Bridge v1.3.0 CI publish fix

Fixes two GitHub Actions portability issues in `.github/workflows/update-bridge.yml`:

1. SHA-256 sidecars are emitted with LF line endings and normalized before `sha256sum --check`.
2. `gh release upload` receives `--repo "${{ github.repository }}"` so the publish job does not need a `.git` checkout.

Apply at repository root, then commit and rerun `Build MCW Update Bridge`.
