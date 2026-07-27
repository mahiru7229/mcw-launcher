# MCW Launcher v0.9.0-beta.1 — Complete Startup Recovery

This consolidated patch includes the Repair Center changes, centralized CurseForge recovery exceptions, and the complete MCW LAN package required by startup and repair checks.

It is safe to apply over `v0.8.1` or over an earlier incremental `v0.9.0-beta.1` patch installation.

The patch intentionally restores these startup-critical files:

- `src/core/lan/lan_agent_manager.py`
- `src/core/lan/lan_agent_target_resolver.py`
- `src/core/lan/lan_hosting_manager.py`
- `runtime/mcw-lan-agent.jar`

`launcher.py` now validates source-mode dependencies before importing the main interface, so an incomplete extraction reports all missing files at once rather than failing through repeated `ImportError` messages.
