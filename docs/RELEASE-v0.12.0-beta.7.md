# MCW Launcher v0.12.0-beta.7

## Stability, Recovery and Account UX

This beta hardens instance lifecycle operations and improves Microsoft account selection in the instance-centered interface.

### Instance safety

- Clone and `.mcwpack` import now build inside a dedicated staging directory before an atomic commit.
- Rename, clone and import write recoverable operation journals.
- Startup recovery resolves interrupted operations, pending deletions, stale run locks and orphan staging files.
- `instances.json` is rebuilt from valid on-disk instance metadata after recovery.
- Failed operations attempt rollback instead of leaving a half-created instance.

### Account workflow

- Selecting another account in the Accounts page switches immediately; the confirmation button was removed.
- Microsoft profile skin metadata is stored in the account database.
- The launcher caches the signed-in player's Minecraft skin texture.
- The instance workspace displays `Account: <skin face> name` for Microsoft accounts with an available skin.
- Skin download failure never blocks authentication or launching.

### Compatibility and security

- Existing account rows migrate automatically to database schema version 3.
- Existing account integrity signatures remain compatible.
- Skin textures must use HTTPS, be valid PNG files and remain below 4 MiB.
- Core remains headless and does not depend on PySide6.

## Metadata

```text
VERSION = v0.12.0-beta.7
VERSION_ID = 0.12.0-beta.7
UPDATE_CHANNEL = beta
```

## Suggested commit

```text
feat: add startup recovery and instant account switching
```
