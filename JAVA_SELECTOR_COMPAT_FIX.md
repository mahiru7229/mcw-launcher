# Java selector compatibility fix

This patch fixes regressions introduced when managed Java auto-install was added.

## What changed

- Restored `JavaSelector` to its original responsibility: select an already discovered Java installation.
- Restored exact-version preference and nearest-higher fallback.
- Restored the original errors:
  - `No Java found.`
  - `Java <major> was not found.`
- Added `JavaResolver` as the orchestration layer:
  - Try `JavaSelector.select_java(required_major)` first.
  - If selection fails, call `JavaProvisioner.ensure(required_major, reporter)`.
- Restored `MinecraftExecutor` pipeline order, progress messages and return payload.
- `MinecraftExecutor` no longer passes `reporter=` into `JavaSelector.select_java`, preserving existing monkeypatches and tests.

## Managed runtime behavior

The launcher still only downloads managed Java 8, 17 and 25. `JavaMajorPolicy` remains inside `JavaProvisioner`:

- required `<= 8` -> download Java 8
- required `9..17` -> download Java 17
- required `18..25` -> download Java 25

Installed system Java versions can still be selected using the original nearest-higher rule.

## Files

- `src/core/java/java_selector.py`
- `src/core/java/java_resolver.py`
- `src/core/minecraft/minecraft_executor.py`
- `test/core/java/test_java_resolver.py`

## Run tests

```powershell
pytest test/core/java/test_java_selector.py test/core/java/test_java_resolver.py test/core/minecraft/test_minecraft_executor.py
```
