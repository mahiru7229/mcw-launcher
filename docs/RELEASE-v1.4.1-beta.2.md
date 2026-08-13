# MCW Launcher v1.4.1-beta.2

Beta 2 is a focused Windows regression fix on top of v1.4.1-beta.1.

## Fixed

- Java discovery now probes `java.exe` when a discovered candidate is `javaw.exe`, preventing broken or partially removed Java runtimes from opening a **Java Virtual Machine Launcher** dialog during background scan.
- Diagnostics Java collection uses the same console probe path, so exporting a diagnostics bundle does not trigger that popup for the same stale runtime candidate.
- Managed Java extraction now receives a non-existent child directory inside the allocated short workspace. This fixes `WinError 183` where the extractor attempted to create the workspace directory that `Paths.create_short_workspace()` had already created.
- Diagnostics recognizes the MCW short workspace as `temp/...`, reducing user-path leakage in Java provisioning errors.

## Scope

All Java recovery/provisioning and Diagnostics v2.1 changes from v1.4.1-beta.1 remain unchanged. No new feature work is included.
