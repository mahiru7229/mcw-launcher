from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton

from mcw_core.api.account.account_skin_manager import AccountSkinManager
from mcw_core.api.language.language_manager import tr
from src.gui.media.minecraft_skin import minecraft_skin_face_pixmap
from src.gui.pages.base_page import BasePage
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget


class AccountPage(BasePage):
    create_offline_requested = Signal(str)
    create_microsoft_requested = Signal()
    cancel_microsoft_requested = Signal()
    select_requested = Signal(str)
    remove_requested = Signal(str)
    refresh_requested = Signal()
    security_audit_requested = Signal()
    security_reprotect_requested = Signal()

    def __init__(self) -> None:
        super().__init__(tr("Accounts"), tr("account.page.subtitle"), "accounts")
        self._accounts: dict[str, object] = {}
        self._selected_id = ""
        self._synchronizing = False
        self._microsoft_auth_active = False
        self._microsoft_status_override = ""
        self._build_ui()

    def _build_ui(self) -> None:
        selected_card = CardWidget(tr("Saved accounts"), tr("account.selection.instant"))
        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self._account_changed)
        self.skin_preview = QLabel()
        self.skin_preview.setObjectName("AccountSkinPreview")
        self.skin_preview.setFixedSize(48, 48)
        self.skin_preview.setScaledContents(False)
        self.username_value = QLabel(tr("Username: -"))
        self.username_value.setObjectName("ValueLabel")
        self.type_value = QLabel(tr("Type: -"))
        self.type_value.setObjectName("MutedLabel")
        self.uuid_value = QLabel(tr("UUID: -"))
        self.uuid_value.setObjectName("TinyLabel")
        self.uuid_value.setWordWrap(True)
        self.selection_status = QLabel(tr("account.selection.none"))
        self.selection_status.setObjectName("StatusBadge")

        action_grid = QGridLayout()
        self.remove_button = set_theme_icon(QPushButton(tr("Remove")), "icon.action.remove")
        self.remove_button.setObjectName("DangerButton")
        self.refresh_button = set_theme_icon(QPushButton(tr("Refresh")), "icon.action.refresh")
        self.remove_button.clicked.connect(self._confirm_remove)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        action_grid.addWidget(self.remove_button, 0, 0)
        action_grid.addWidget(self.refresh_button, 0, 1)

        selected_card.layout.addWidget(self.account_combo)
        selected_card.layout.addWidget(self.skin_preview)
        selected_card.layout.addWidget(self.username_value)
        selected_card.layout.addWidget(self.type_value)
        selected_card.layout.addWidget(self.uuid_value)
        selected_card.layout.addWidget(self.selection_status)
        selected_card.layout.addLayout(action_grid)
        self.root_layout.addWidget(selected_card)

        create_card = CardWidget(tr("account.create.title"), tr("account.create.description"))
        create_card.setProperty("themeRole", "microsoft")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(tr("Example: Steve"))
        self.create_button = set_theme_icon(QPushButton(tr("Create and select")), "icon.action.add")
        self.create_button.setObjectName("PrimaryButton")
        self.create_button.clicked.connect(lambda: self.create_offline_requested.emit(self.username_input.text()))

        self.microsoft_button = set_theme_icon(QPushButton(tr("account.microsoft.add")), "icon.action.microsoft")
        self.microsoft_button.setToolTip(tr("account.microsoft.tooltip"))
        self.microsoft_button.clicked.connect(self.create_microsoft_requested.emit)

        self.microsoft_cancel_button = set_theme_icon(QPushButton(tr("account.microsoft.cancel")), "icon.action.remove")
        self.microsoft_cancel_button.setObjectName("DangerButton")
        self.microsoft_cancel_button.clicked.connect(self.cancel_microsoft_requested.emit)
        self.microsoft_cancel_button.setVisible(False)

        self.microsoft_status = QLabel(tr("account.microsoft.status_available"))
        self.microsoft_status.setObjectName("StatusBadge")
        self.microsoft_status.setWordWrap(True)

        create_card.layout.addWidget(QLabel(tr("Username")))
        create_card.layout.addWidget(self.username_input)
        create_card.layout.addWidget(self.create_button)
        create_card.layout.addWidget(self.microsoft_button)
        create_card.layout.addWidget(self.microsoft_cancel_button)
        create_card.layout.addWidget(self.microsoft_status)
        self.root_layout.addWidget(create_card)

        security_card = CardWidget(tr("account.security.title"), tr("account.security.description"))
        security_card.setProperty("themeRole", "security")
        self.security_status = QLabel(tr("account.security.checking"))
        self.security_status.setObjectName("StatusBadge")
        self.security_status.setWordWrap(True)
        security_buttons = QGridLayout()
        self.verify_button = set_theme_icon(QPushButton(tr("account.security.verify")), "icon.action.shield")
        self.reprotect_button = set_theme_icon(QPushButton(tr("account.security.reprotect")), "icon.action.reprotect")
        self.verify_button.clicked.connect(self.security_audit_requested.emit)
        self.reprotect_button.clicked.connect(self.security_reprotect_requested.emit)
        security_buttons.addWidget(self.verify_button, 0, 0)
        security_buttons.addWidget(self.reprotect_button, 0, 1)
        security_card.layout.addWidget(self.security_status)
        security_card.layout.addLayout(security_buttons)
        self.root_layout.addWidget(security_card)
        self.root_layout.addStretch()

    def set_accounts(self, accounts: list, selected_id: str) -> None:
        self._accounts = {account.account_id: account for account in accounts}
        self._synchronizing = True
        self.account_combo.blockSignals(True)
        try:
            self.account_combo.clear()
            for account in accounts:
                account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
                self.account_combo.addItem(f"{account.username}  [{account_type}]", account.account_id)
            target_index = self.account_combo.findData(selected_id) if selected_id else -1
            if target_index < 0 and self.account_combo.count():
                target_index = 0
            self.account_combo.setCurrentIndex(target_index)
            self._selected_id = str(self.account_combo.currentData() or "") if selected_id else ""
        finally:
            self.account_combo.blockSignals(False)
            self._synchronizing = False
        self._update_details()

    def current_account_id(self) -> str:
        return str(self.account_combo.currentData() or "")

    def set_busy(self, busy: bool) -> None:
        self.set_interaction_locked(busy)

    def set_microsoft_auth_state(self, active: bool, message: str = "") -> None:
        self._microsoft_auth_active = bool(active)
        self._microsoft_status_override = str(message or "")
        self.microsoft_button.setEnabled(not active)
        self.microsoft_cancel_button.setVisible(active)
        self.microsoft_cancel_button.setEnabled(active and message != tr("account.microsoft.cancelling"))
        self.microsoft_status.setObjectName("WarningBadge" if active else "StatusBadge")
        self.microsoft_status.setText(self._microsoft_status_override or tr("account.microsoft.status_available"))
        self.microsoft_status.style().unpolish(self.microsoft_status)
        self.microsoft_status.style().polish(self.microsoft_status)

    def set_security_report(self, report: object) -> None:
        healthy = bool(getattr(report, "is_healthy", False))
        backend = str(getattr(report, "credential_backend", "platform") or "platform")
        self.security_status.setObjectName("StatusBadge" if healthy else "WarningBadge")
        self.security_status.setText(
            tr(
                "account.security.summary",
                protected=getattr(report, "protected_account_count", 0),
                microsoft=getattr(report, "microsoft_account_count", 0),
                legacy=getattr(report, "legacy_account_count", 0),
                invalid=getattr(report, "invalid_account_count", 0),
            )
            + "\n"
            + tr("account.security.backend", backend=tr(f"account.security.backend.{backend}"))
        )
        self.security_status.style().unpolish(self.security_status)
        self.security_status.style().polish(self.security_status)

    def _account_changed(self, _index: int) -> None:
        self._update_details()
        account_id = self.current_account_id()
        if self._synchronizing or not account_id or account_id == self._selected_id:
            return
        self._selected_id = account_id
        self.select_requested.emit(account_id)

    def _update_details(self) -> None:
        account = self._accounts.get(self.current_account_id())
        self.skin_preview.clear()
        if account is None:
            self.username_value.setText(tr("Username: -"))
            self.type_value.setText(tr("Type: -"))
            self.uuid_value.setText(tr("UUID: -"))
            self.selection_status.setText(tr("account.selection.none"))
            return
        account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
        self.username_value.setText(tr("Username: {username}", username=account.username))
        self.type_value.setText(tr("Type: {account_type}", account_type=account_type.upper()))
        self.uuid_value.setText(tr("UUID: {uuid}", uuid=account.uuid))
        self.selection_status.setText(tr("account.selection.active", username=account.username))
        texture = AccountSkinManager.cached_texture(account)
        if texture is not None:
            face = minecraft_skin_face_pixmap(texture, 48)
            if not face.isNull():
                self.skin_preview.setPixmap(face)

    def _confirm_remove(self) -> None:
        account_id = self.current_account_id()
        if not account_id:
            return
        account = self._accounts.get(account_id)
        username = getattr(account, "username", tr("this account"))
        answer = QMessageBox.question(self, tr("Remove account"), tr("Remove '{username}' from the launcher?", username=username), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.remove_requested.emit(account_id)

    def retranslate_dynamic(self) -> None:
        self.remove_button.setText(tr("Remove"))
        self.refresh_button.setText(tr("Refresh"))
        self.create_button.setText(tr("Create and select"))
        self.microsoft_button.setText(tr("account.microsoft.add"))
        self.microsoft_button.setToolTip(tr("account.microsoft.tooltip"))
        self.microsoft_cancel_button.setText(tr("account.microsoft.cancel"))
        self.verify_button.setText(tr("account.security.verify"))
        self.reprotect_button.setText(tr("account.security.reprotect"))
        if not self._microsoft_auth_active:
            self._microsoft_status_override = ""
        self.set_microsoft_auth_state(self._microsoft_auth_active, self._microsoft_status_override)
        self._update_details()
