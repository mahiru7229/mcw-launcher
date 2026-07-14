from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.core.language.language_manager import tr
from src.gui.config import VERSION
from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget
from src.gui.theme.runtime import set_theme_icon, set_theme_pixmap


class HomePage(BasePage):
    manage_accounts_requested = Signal()
    manage_instances_requested = Signal()
    open_settings_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Home", "Your launch deck: current account, active instance, and core status in one place.", "home")
        self._account: object | None = None
        self._instance: object | None = None
        self._manifest_count: int | None = None
        self._status_message = "Ready"
        self._build_ui()

    def _build_ui(self) -> None:
        hero = CardWidget("", object_name="HeroCard")
        hero_layout = QVBoxLayout()
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = set_theme_pixmap(QLabel(), "logo.main", 640, 240, "MCW")
        logo.setObjectName("BrandLabel")

        hero_title = QLabel("MCW LAUNCHER")
        hero_title.setObjectName("PageTitle")
        hero_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_version = QLabel(VERSION)
        hero_version.setObjectName("MutedLabel")
        hero_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(logo)
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_version)
        hero.layout.addLayout(hero_layout)
        self.root_layout.addWidget(hero)

        grid = QGridLayout()
        grid.setSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        account_card = CardWidget("Active account", "The account used for the next launch.")
        self.account_value = QLabel("No account selected")
        self.account_value.setObjectName("ValueLabel")
        self.account_detail = QLabel("Open Accounts to create an offline account.")
        self.account_detail.setObjectName("MutedLabel")
        account_button = set_theme_icon(QPushButton("Open Accounts"), "icon.action.account")
        account_button.clicked.connect(self.manage_accounts_requested.emit)
        account_card.layout.addWidget(self.account_value)
        account_card.layout.addWidget(self.account_detail)
        account_card.layout.addWidget(account_button)

        instance_card = CardWidget("Active instance", "The instance attached to the permanent launch bar.")
        self.instance_value = QLabel("No instance selected")
        self.instance_value.setObjectName("ValueLabel")
        self.instance_detail = QLabel("Open Instances to create or choose one.")
        self.instance_detail.setObjectName("MutedLabel")
        instance_button = set_theme_icon(QPushButton("Open Instances"), "icon.action.instance")
        instance_button.clicked.connect(self.manage_instances_requested.emit)
        instance_card.layout.addWidget(self.instance_value)
        instance_card.layout.addWidget(self.instance_detail)
        instance_card.layout.addWidget(instance_button)

        core_card = CardWidget("Core connection", "GUI only calls the public MCW Core API.")
        self.manifest_value = QLabel("Manifest not loaded")
        self.manifest_value.setObjectName("ValueLabel")
        self.last_status = QLabel("Ready")
        self.last_status.setObjectName("MutedLabel")
        settings_button = set_theme_icon(QPushButton("Launcher Settings"), "icon.action.settings")
        settings_button.clicked.connect(self.open_settings_requested.emit)
        core_card.layout.addWidget(self.manifest_value)
        core_card.layout.addWidget(self.last_status)
        core_card.layout.addWidget(settings_button)

        grid.addWidget(account_card, 0, 0)
        grid.addWidget(instance_card, 0, 1)
        grid.addWidget(core_card, 1, 0, 1, 2)
        self.root_layout.addLayout(grid)
        self.root_layout.addStretch()

    def set_account(self, account: object | None) -> None:
        self._account = account
        if account is None:
            self.account_value.setText(tr("No account selected"))
            self.account_detail.setText(tr("Open Accounts to create an offline account."))
            return
        account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
        self.account_value.setText(account.username)
        self.account_detail.setText(account_type.upper())

    def set_instance(self, instance: object | None) -> None:
        self._instance = instance
        if instance is None:
            self.instance_value.setText(tr("No instance selected"))
            self.instance_detail.setText(tr("Open Instances to create or choose one."))
            return
        self.instance_value.setText(instance.name)
        self.instance_detail.setText(tr("Minecraft {version}", version=instance.version_id))

    def set_manifest_count(self, count: int) -> None:
        self._manifest_count = count
        self.manifest_value.setText(tr("{count} versions available", count=count))

    def set_status(self, message: str) -> None:
        self._status_message = message
        self.last_status.setText(tr(message))

    def retranslate_dynamic(self) -> None:
        self.set_account(self._account)
        self.set_instance(self._instance)
        if self._manifest_count is None:
            self.manifest_value.setText(tr("Manifest not loaded"))
        else:
            self.set_manifest_count(self._manifest_count)
        self.last_status.setText(tr(self._status_message))
