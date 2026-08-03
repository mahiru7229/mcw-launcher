# MCW Launcher Architecture

```text
MCW Launcher GUI / launcher.py
        │
        │ imports only mcw_core / mcw_core.api
        ▼
┌──────────────────────────────────────┐
│ Public MCW Core library              │
│                                      │
│ MCWCore                              │
│ ├── InstanceService                  │
│ ├── LoaderService                    │
│ ├── JavaService                      │
│ ├── OperationHandle                  │
│ └── launch(LaunchRequest)            │
│                                      │
│ mcw_core.api                         │
│ └── compatibility exports for        │
│     existing GUI adapters            │
└──────────────────────────────────────┘
        │
        ▼
src.core / src.models / src.database
```

The core package is installable without `src.gui` and without PySide6. A CLI,
test runner, or another Python application can configure `CorePaths`, load an
instance, and launch Minecraft through the same `MCWCore` facade used by the
launcher.

```text
MainWindow
├── SidebarWidget
├── QStackedWidget
│   ├── HomePage
│   ├── AccountPage
│   ├── InstancesPage
│   ├── InstanceSettingsPage
│   ├── LauncherSettingsPage
│   ├── LogsPage
│   └── AboutPage
├── LaunchControlWidget
└── RightPanelWidget

Controllers
├── VersionController
├── AccountController
├── InstanceController ──► MCWCore.instances
├── JavaController ──────► MCWCore.java
├── SettingsController
├── GuiSettingsController
└── LaunchController ────► MCWCore.launch
```

## Dependency rules

- `src.core` and `src.models` must not import `src.gui`, PySide6, or PyQt.
- `src.gui` and `launcher.py` must not import `src.core` directly.
- New integrations should use top-level objects exported from `mcw_core`.
- `mcw_core.api` preserves domain-level compatibility while GUI adapters are
  gradually simplified around the high-level facade.
- Core paths are supplied through `CorePaths`; the default launcher root is no
  longer the only supported runtime location.
- Core progress and pause/resume/cancel contracts are independent of Qt
  signals, widgets, and threads.

## SRP boundaries

- `MainWindow` only assembles widgets and routes signals.
- Controllers translate GUI intent into public MCW Core calls.
- `TaskRunner` owns the QThread lifecycle.
- `MCWCore` is the application facade; `MinecraftExecutor` remains the internal
  launch orchestrator.
- Java downloading/installing remains inside the core library.
- The GUI displays `ProgressEvent` and does not own download URLs, ZIP
  extraction, checksums, runtime paths, or launch command construction.
