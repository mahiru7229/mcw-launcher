# MCW Launcher v1.1.0-beta.6 — legacy native classifier hotfix

Apply this patch after the earlier **v1.1.0-beta.6 LaunchWrapper hotfix**.

## What it fixes

Forge 1.6.4 can declare native-only Maven platform libraries such as:

- `org.lwjgl.lwjgl:lwjgl-platform:2.9.0`
- `net.java.jinput:jinput-platform:2.0.5`

These coordinates do not have a normal unclassified JAR. They provide platform classifier JARs such as `natives-windows`. The launcher now creates `downloads.classifiers` and downloads the correct Windows native JAR instead of trying to resolve a nonexistent `*-platform-<version>.jar`.

## Apply

1. Close MCW Launcher.
2. Extract this ZIP into the repository root.
3. Allow files to be replaced.
4. Launch the Forge 1.6.4 instance again.

The incomplete legacy Forge cache is invalidated automatically. You do not need to delete the instance.

## Scope

Launcher diff only. No standalone MCW Core source or wheel is included.
