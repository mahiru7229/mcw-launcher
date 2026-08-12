# MCW Core v1.4.0-beta.1

MCW Core **1.4.0-beta.1** is the Core companion for MCW Launcher v1.4.0-beta.1. The Python distribution version is **1.4.0b1**.

## Changes

- Add force-kill support through `GameRuntimeManager.kill()` and supervised process-session termination.
- Add `ProcessSessionState.KILLING` and `GameExitResult.killed_by_user` so intentional force termination is distinguishable from a crash.
- Expose `InstanceService.kill(name)` through the existing public Core facade.
- Harden Forge profile discovery: vanilla/arbitrary fallback is rejected.
- Require Forge runtime evidence matching the requested loader before a profile/cache is accepted.
- Validate generated Forge profiles before publishing persistent cache state.
- Automatically reject poisoned Forge caches that contain Forge metadata without Forge runtime content.
- Preserve all v1.3.2 atomic-write, Windows short-workspace and update-integrity hardening.

## Compatibility

MCW Core remains GUI-independent and does not add a PySide6 dependency.

## Beta note

The process-kill implementation relies on the existing launch-session PID/instance verification boundary. Windows process-tree behavior should still be smoke-tested with real Minecraft launches before v1.4 stable.
