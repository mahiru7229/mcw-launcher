from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal


class AppState(QObject):
    """Centralized reactive state store for the MCW Launcher GUI.

    Inspired by Modrinth's centralized store architecture, this class acts as
    the single source of truth for GUI components, emitting signals whenever
    shared application state changes.
    """

    instances_changed = Signal(list, str)
    selected_instance_changed = Signal(object)
    running_instances_changed = Signal(list)
    health_reports_changed = Signal(list)
    accounts_changed = Signal(list, str)
    selected_account_changed = Signal(object)
    connectivity_changed = Signal(bool)
    theme_changed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._instances: list[Any] = []
        self._selected_instance_name = ""
        self._selected_instance: Any = None
        self._running_instances: list[Any] = []
        self._health_reports: list[Any] = []
        self._accounts: list[Any] = []
        self._selected_account_id = ""
        self._selected_account: Any = None
        self._is_online = True
        self._active_theme = "mcw-default"

    # --- Instances State ---

    @property
    def instances(self) -> list[Any]:
        return list(self._instances)

    @property
    def selected_instance_name(self) -> str:
        return self._selected_instance_name

    @property
    def selected_instance(self) -> Any:
        return self._selected_instance

    @property
    def running_instances(self) -> list[Any]:
        return list(self._running_instances)

    @property
    def health_reports(self) -> list[Any]:
        return list(self._health_reports)

    def set_instances(self, instances: list[Any], selected_name: str = "") -> None:
        self._instances = list(instances)
        if selected_name:
            self._selected_instance_name = selected_name
        elif self._selected_instance_name not in [getattr(inst, "name", "") for inst in self._instances]:
            self._selected_instance_name = getattr(self._instances[0], "name", "") if self._instances else ""
        self.instances_changed.emit(self._instances, self._selected_instance_name)

    def set_selected_instance(self, instance: Any) -> None:
        self._selected_instance = instance
        name = getattr(instance, "name", "") if instance is not None else ""
        if name:
            self._selected_instance_name = name
        self.selected_instance_changed.emit(self._selected_instance)

    def set_running_instances(self, running_instances: list[Any]) -> None:
        self._running_instances = list(running_instances)
        self.running_instances_changed.emit(self._running_instances)

    def set_health_reports(self, reports: list[Any]) -> None:
        self._health_reports = list(reports)
        self.health_reports_changed.emit(self._health_reports)

    # --- Accounts State ---

    @property
    def accounts(self) -> list[Any]:
        return list(self._accounts)

    @property
    def selected_account_id(self) -> str:
        return self._selected_account_id

    @property
    def selected_account(self) -> Any:
        return self._selected_account

    def set_accounts(self, accounts: list[Any], selected_id: str = "") -> None:
        self._accounts = list(accounts)
        if selected_id:
            self._selected_account_id = selected_id
        self.accounts_changed.emit(self._accounts, self._selected_account_id)

    def set_selected_account(self, account: Any) -> None:
        self._selected_account = account
        acc_id = getattr(account, "account_id", "") if account is not None else ""
        if acc_id:
            self._selected_account_id = acc_id
        self.selected_account_changed.emit(self._selected_account)

    # --- Connectivity & Theme ---

    @property
    def is_online(self) -> bool:
        return self._is_online

    def set_online(self, online: bool) -> None:
        if self._is_online != online:
            self._is_online = bool(online)
            self.connectivity_changed.emit(self._is_online)

    @property
    def active_theme(self) -> str:
        return self._active_theme

    def set_active_theme(self, theme: str) -> None:
        theme_str = str(theme or "").strip()
        if theme_str and self._active_theme != theme_str:
            self._active_theme = theme_str
            self.theme_changed.emit(self._active_theme)
