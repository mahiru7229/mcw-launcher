# MCW Launcher Beta 7 — Runtime & Repair

Beta 7 adds process lifecycle monitoring and a full instance repair workflow to the existing Vanilla and Fabric launch pipeline.

## Runtime lifecycle

After Minecraft starts, the launcher continues monitoring the Java process until it exits.

Recorded information:

- Minecraft PID;
- process exit code;
- UTC start and end times;
- session duration;
- latest `minecraft-*.log` path;
- newest crash report created during the session;
- normal exit or crash state.

The latest runtime state is written into `instance.json` without removing custom metadata fields.

```json
{
  "last_played": "2026-07-15T12:00:00+00:00",
  "total_play_time_seconds": 4200,
  "last_exit_code": 0,
  "last_launch_crashed": false,
  "last_game_log": ".../logs/minecraft-2026-07-15_18-30-00.log",
  "last_crash_report": ""
}
```

A rolling history of the latest 50 sessions is stored at:

```text
instances/<instance>/.mcw/runtime-history.json
```

## Crash detection

A session is classified as crashed when either condition is true:

- the Java process exits with a non-zero code;
- a new file appears in `crash-reports/` during that session.

This covers modded cases where Minecraft may generate a crash report while returning exit code `0`.

The Logs page includes:

- **Open latest game log**;
- **Open latest crash report**.

Both actions use the currently selected instance.

## Full instance repair

The **Repair instance** action verifies or rebuilds:

1. Minecraft version metadata;
2. Fabric profile and Loader metadata when applicable;
3. client JAR SHA-1;
4. libraries SHA-1;
5. native extraction markers and native files;
6. asset index and all asset SHA-1 values;
7. compatible Java runtime availability.

Repair deliberately keeps:

```text
saves/
mods/
resourcepacks/
shaderpacks/
screenshots/
options.txt
settings.json
```

The last repair summary is stored at:

```text
instances/<instance>/.mcw/last-repair.json
```

Repair is blocked while the selected instance is running.

## Metadata schema

Instance metadata is now written atomically and uses:

```json
{
  "metadata_version": 2
}
```

Existing fields such as notes, icon, Modrinth extensions, play time, and custom extension data are preserved when the instance is renamed or its loader is changed.
