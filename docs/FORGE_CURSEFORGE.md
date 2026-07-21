# Forge and CurseForge — MCW Launcher v0.6.0 Beta 3

## Scope

Beta 3 focuses on transactional Forge version switching, one-step rollback, pre-launch compatibility checks, and privacy-safe diagnostics. CurseForge groundwork remains present, but its actions are hidden unless an API key is configured. Vanilla, Fabric, and Modrinth behavior remain available.

## CurseForge API key

CurseForge API requests require an API key. MCW Launcher does not store a public key in the repository.

Use either:

```powershell
$env:MCW_CURSEFORGE_API_KEY="your-api-key"
.\dist\MCW Launcher.exe
```

or create a local file that is excluded by `.gitignore`:

```json
{
  "api_key": "your-api-key"
}
```

Save it as:

```text
config/curseforge.json
```

Never commit or publish this file.

## Forge workflow

```text
Create/Manage Instance
→ Select Forge
→ Load compatible Forge versions
→ Download the official installer
→ Run the installer outside the GUI thread
→ Import generated Forge libraries/profile
→ Launch through the normal Minecraft pipeline
```

Forge downloads use the shared progress reporter, pause/resume controller, bandwidth limiter, retry behavior, and file verification.

## CurseForge mod workflow

```text
Open a Forge instance
→ Manage Mods
→ Browse CurseForge
→ Select project and compatible file
→ Install required dependencies
→ Verify and copy JAR files into mods/
→ Save CurseForge provenance in .mcw/curseforge.json
```

## CurseForge modpack workflow

```text
Browse CurseForge Modpacks
→ Select pack file and instance name
→ Download and validate manifest.json
→ Resolve Minecraft + Forge versions
→ Create Forge instance
→ Safely extract overrides
→ Save managed-file registry
→ Download managed files when Launch is pressed
```

Managed files follow this launch flow:

```text
Check every file
→ Download all missing files
→ Check again
→ Retry up to 3 rounds
→ Launch or show the missing-file error
```

Files already present with the expected size/hash are checked and skipped, not downloaded again.

## Third-party distribution restrictions

Some CurseForge files are not available to third-party launchers. When the API marks a file unavailable or returns no permitted download URL, MCW Launcher records a clear manual-install error instead of treating the whole package as corrupted.

The existing per-instance managed-file policy controls whether missing required files block Launch after all retry rounds.

## Beta 3 scope and limitations

- CurseForge browsing remains unavailable until an API key is configured.
- NeoForge modpacks are not supported in this beta.
- Forge Repair verifies profile metadata and downloaded libraries, then restores the previous profile if repair fails.
- Local Mod Manager supports Fabric, modern Forge, and legacy Forge metadata.
- The packaged Windows EXE still requires manual validation on Windows before release.


## Forge version switching and rollback

When changing from one Forge version to another, MCW Launcher prepares and verifies the target profile and required libraries before updating `instance.json`. After a successful change, the previous loader is recorded at:

```text
instances/<instance>/.mcw/forge/previous-installation.json
```

The **Restore previous loader** action prepares the recorded loader, verifies Forge files when applicable, and only then updates the instance. A failed change or restore leaves the current loader untouched.

## Forge pre-launch check

Forge instances are checked before Minecraft starts. Errors block Launch; warnings are returned with the normal launch warnings.

Blocking checks include:

- invalid or missing Forge runtime metadata;
- Fabric/NeoForge mods in a Forge instance;
- duplicate enabled mod IDs;
- missing, disabled, or incompatible required dependencies;
- required Forge libraries that remain missing or invalid after the downloader runs.

## Forge diagnostics

**Export Forge diagnostics** creates a ZIP containing the cached Forge profile, Forge installer/change logs, sanitized instance settings, mod metadata, Minecraft logs, and pre-launch results. It never includes account databases, OAuth credentials, worlds, saves, or mod JAR contents.
