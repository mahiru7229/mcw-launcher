# MCW Launcher v0.9.0-beta.3

## Download Engine Hardening & Recovery

- Recovers valid `.part` files after a launcher restart instead of discarding downloaded bytes.
- Detects downloads that are ready for checksum verification and keeps them for the next request.
- Reconciles completed or stale journal records during startup.
- Removes oversized partial files only when the path is a verified MCW cache/instance download target.
- Keeps journal cleanup best-effort so a locked Windows journal cannot block launcher startup.

## Compatibility

- Existing instances, accounts, settings, Modrinth metadata, CurseForge metadata, and backups remain compatible.
- Download recovery does not fetch anything during startup; normal downloads still own all network activity and progress reporting.
