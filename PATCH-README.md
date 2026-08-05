# MCW Launcher v1.1.0-beta.6 — Legacy Forge certificate compatibility hotfix

Apply this patch after the previous v1.1.0-beta.6 Forge 1.6.4 hotfixes.
Extract the ZIP into the launcher repository root and overwrite the existing files.

## Fix

LaunchWrapper-based Forge profiles now receive exactly one JVM property:

```text
-Dfml.ignoreInvalidMinecraftCertificates=true
```

The property is limited to profiles that:

- use `net.minecraft.launchwrapper.Launch`; and
- contain MCW Forge metadata.

Before enabling this compatibility property, MCW performs a full SHA-1 verification of the Minecraft client JAR. A mismatched JAR is deleted and downloaded again through the existing verified client-download pipeline. Other Minecraft profiles keep the normal fast verification path.

This allows old FML certificate checks to run on current Java security policies without weakening MCW's own client-integrity verification.

## Validation

- Forge, Minecraft executor, launcher-manager, and client-download tests: `122 passed`
- Python compile validation: passed
- No MCW Core package, wheel, or source archive is included
