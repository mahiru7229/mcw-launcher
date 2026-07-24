from __future__ import annotations

from src.core import bootstrap


def test_initialize_application_reports_ordered_progress_and_returns_settings(monkeypatch):
    calls: list[str] = []
    progress: list[tuple[int, str]] = []
    settings = {"network": {"download_limit_mbps": 7.5}, "gui": {"language": "vi-VN"}}

    class FakeSettingsManager:
        def initialize(self):
            calls.append("settings.initialize")

        def load(self):
            calls.append("settings.load")
            return settings

    monkeypatch.setattr(bootstrap.Paths, "initialize", lambda: calls.append("paths.initialize"))
    monkeypatch.setattr(bootstrap, "LauncherSettingsManager", FakeSettingsManager)
    monkeypatch.setattr(bootstrap.download_bandwidth_limiter, "configure_mbps", lambda value: calls.append(f"bandwidth:{value}"))
    monkeypatch.setattr(bootstrap.AccountDatabase, "initialize", lambda: calls.append("accounts.initialize"))
    monkeypatch.setattr(bootstrap.AccountSecurityManager, "migrate_if_needed", lambda: calls.append("security.migrate"))

    result = bootstrap.initialize_application(lambda percent, key: progress.append((percent, key)))

    assert result == settings
    assert calls == [
        "paths.initialize",
        "settings.initialize",
        "settings.load",
        "bandwidth:7.5",
        "accounts.initialize",
        "security.migrate",
    ]
    assert progress == [
        (8, "startup.preparing_directories"),
        (24, "startup.loading_settings"),
        (42, "startup.configuring_downloads"),
        (62, "startup.preparing_accounts"),
        (80, "startup.protecting_accounts"),
        (90, "startup.core_ready"),
    ]


def test_initialize_application_accepts_no_progress_callback(monkeypatch):
    class FakeSettingsManager:
        def initialize(self):
            return None

        def load(self):
            return {"network": {}}

    monkeypatch.setattr(bootstrap.Paths, "initialize", lambda: None)
    monkeypatch.setattr(bootstrap, "LauncherSettingsManager", FakeSettingsManager)
    monkeypatch.setattr(bootstrap.download_bandwidth_limiter, "configure_mbps", lambda _value: None)
    monkeypatch.setattr(bootstrap.AccountDatabase, "initialize", lambda: None)
    monkeypatch.setattr(bootstrap.AccountSecurityManager, "migrate_if_needed", lambda: None)

    assert bootstrap.initialize_application() == {"network": {}}
