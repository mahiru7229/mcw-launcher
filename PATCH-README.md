# MCW Launcher v1.1.1-beta.5 — embedded/search dependency hotfix

This small archive applies only to the **earlier v1.1.1-beta.5 dependency-resolution patch**.
It upgrades that build to Beta 5 revision 2 without requiring a return to Beta 4.

## Apply on the earlier Beta 5 build

1. Close MCW Launcher, Minecraft, and running test processes.
2. Confirm the earlier v1.1.1-beta.5 patch is already applied.
3. Back up or commit the tree.
4. Extract this ZIP into the repository root and replace existing files.
5. Run `python -m pytest -q`.
6. Smoke-test the affected Create modpack on Windows.

Do not apply this small hotfix directly to Beta 4. Use the full Beta 5 revision 2 patch for that baseline.

## Hotfix scope

- Indexes bounded nested-JAR capabilities, including Forge/NeoForge Jar-in-Jar and legacy `ContainedDeps`.
- Recognizes embedded Flywheel from the Create JAR when its actual version satisfies declared ranges.
- Searches provider projects for missing JAR-declared mod IDs such as `kotlinforforge`.
- Preserves search provenance and requested version ranges in Modrinth/CurseForge registries.
- Audits the downloaded JAR before allowing launch.
- Adds Forge/Maven-style version comparison for values such as `0.6.8.a`.

## Validation

- Full suite: 1379 passed, 88 skipped, 2 expected warnings.
- `python -m compileall -q src mcw_core test`: passed.
