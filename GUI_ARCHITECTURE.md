# MCW Launcher Architecture

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
├── InstanceController
├── SettingsController
├── GuiSettingsController
└── LaunchController
    └── MinecraftExecutor
        ├── VersionManager
        ├── JavaSelector
        │   └── JavaProvisioner
        │       ├── JavaMajorPolicy
        │       ├── ManagedJavaRepository
        │       ├── AdoptiumClient
        │       ├── JavaArchiveDownloader
        │       ├── JavaChecksum
        │       └── JavaArchiveExtractor
        ├── DownloadClientManager
        ├── DownloadLibraryManager
        ├── AssetManager
        ├── ContextBuilder
        ├── LauncherManager
        └── JavaRuntime
```

## SRP boundaries

- `MainWindow` chỉ lắp ráp widget và route signal.
- Controller chuyển intent GUI thành lời gọi Core.
- `TaskRunner` sở hữu vòng đời QThread.
- `MinecraftExecutor` điều phối pipeline launch.
- Java downloading/installing nằm hoàn toàn trong `src/core/java/`.
- GUI chỉ hiển thị `ProgressEvent`, không biết URL, ZIP, checksum hay thư mục runtime.
