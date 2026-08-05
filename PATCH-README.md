# MCW Launcher v1.1.0-beta.6 — Forge 1.6.4 OS-rule native hotfix

Apply this patch after the previous Beta 6 native-classifier hotfix.

## Fix

Older Minecraft metadata can contain an LWJGL nightly native entry that is only allowed on macOS 10.5. The previous compatibility normalizer inspected every `*-platform` entry before evaluating its operating-system rules, so Windows attempted to resolve a nonexistent `natives-windows` classifier.

This patch:

- skips metadata normalization and downloads for libraries disallowed on the current OS;
- ignores disallowed libraries when validating whether the Windows native cache is complete;
- preserves those library entries unchanged for metadata compatibility;
- adds regression coverage for `org.lwjgl.lwjgl:lwjgl-platform:2.9.1-nightly-20130708-debug3`.

## Apply

Extract the ZIP over the launcher repository root.

## Validation

- Forge/native/classpath tests: `62 passed`
- Python compile check: passed
