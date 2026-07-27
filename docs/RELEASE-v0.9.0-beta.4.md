# MCW Launcher v0.9.0-beta.4

## Safe Modpack Update Preview

- Builds an exact file plan before a Modrinth modpack update is applied.
- Shows add, replace, remove, preserve, unchanged, and estimated-download totals.
- Detects user-modified managed files and unmanaged path conflicts before confirmation.
- Blocks unsupported loader migrations and updates while Minecraft is running.
- Applies the previewed target version while still revalidating all files during the real update.
- Keeps the existing full safety backup and rollback behavior.

## Compatibility

- Existing Modrinth registry schema and installed packs remain compatible.
- Previewing downloads only the signed/checksummed `.mrpack` manifest; pack payload downloads still occur through the normal progress pipeline after confirmation.
