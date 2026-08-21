# Packaging MCW Core

MCW Launcher `v1.5.0-alpha.2` includes the Core implementation but deliberately does **not** publish a standalone Core source archive or wheel.

The dedicated Core release must be performed only after its version and scope are chosen. Before publishing:

1. Synchronize runtime, distribution and Git tag versions.
2. Package `mcw_core*` plus every implementation/resource dependency it imports; do not include GUI, tests or user data.
3. Install the wheel in a clean Python 3.12 environment on Windows and Linux.
4. Verify importing `mcw_core` without PySide6, the CLI, bundled LAN Agent, examples and public API tests.
5. Audit the wheel for account databases, private config, logs, cache and credentials.

Stability levels:

- `mcw_core`: preferred stable facade;
- `mcw_core.api.*`: granular public boundary;
- `src.*`: private compatibility implementation, not a consumer contract.
