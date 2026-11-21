from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.config.launcher_settings_manager import LauncherSettingsManager
from mcw_core.api.language.language_manager import tr
from src.config import MCW_DOWNLOAD_PAGE_URL, VERSION_ID
from src.gui.theme.runtime import set_theme_icon
from src.gui.window_sizing import resize_dialog_to_screen


class FinalReleaseNoticeDialog(QDialog):
    """Startup notice informing users that v1.8.8 is the final official release
    of this repository and directing them to MCW Launcher: Rust Edition."""

    OPEN_DOWNLOAD = "open_download"
    CONTINUE = "continue"
    DONT_SHOW_AGAIN = "dont_show_again"

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        version: str = VERSION_ID,
        download_url: str = MCW_DOWNLOAD_PAGE_URL,
    ) -> None:
        super().__init__(parent)
        self.version = str(version)
        self.download_url = str(download_url)
        self.decision = self.CONTINUE
        self.should_dismiss_forever = False

        self.setObjectName("FinalReleaseNoticeDialog")
        self.setWindowTitle(tr("final_release.dialog.title"))
        self.setModal(True)
        resize_dialog_to_screen(self, 620, 420, 500, 340)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.heading_label = QLabel(tr("final_release.dialog.heading", version=self.version))
        self.heading_label.setObjectName("PageTitle")
        self.heading_label.setWordWrap(True)
        layout.addWidget(self.heading_label)

        self.message_label = QLabel(tr("final_release.dialog.message", version=self.version))
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        link_html = f'<a href="{self.download_url}" style="color: #8ed35b;">{self.download_url}</a>'
        self.download_link_label = QLabel(tr("final_release.dialog.download_url_label", url=link_html))
        self.download_link_label.setTextFormat(Qt.TextFormat.RichText)
        self.download_link_label.setOpenExternalLinks(True)
        self.download_link_label.setWordWrap(True)
        layout.addWidget(self.download_link_label)

        layout.addStretch(1)

        self.dont_show_checkbox = QCheckBox(tr("final_release.dialog.dont_show_checkbox"))
        layout.addWidget(self.dont_show_checkbox)

        button_box = QDialogButtonBox()
        self.open_download_button = set_theme_icon(
            QPushButton(tr("final_release.dialog.open_download_page")),
            "icon.action.update",
        )
        self.open_download_button.setObjectName("PrimaryButton")
        self.continue_button = set_theme_icon(
            QPushButton(tr("final_release.dialog.continue_launcher")),
            "icon.action.previous",
        )
        self.dont_show_button = set_theme_icon(
            QPushButton(tr("final_release.dialog.dont_show_again")),
            "icon.action.disable",
        )

        button_box.addButton(self.open_download_button, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(self.continue_button, QDialogButtonBox.ButtonRole.RejectRole)
        button_box.addButton(self.dont_show_button, QDialogButtonBox.ButtonRole.DestructiveRole)
        layout.addWidget(button_box)

        self.open_download_button.clicked.connect(self._on_open_download_clicked)
        self.continue_button.clicked.connect(self._on_continue_clicked)
        self.dont_show_button.clicked.connect(self._on_dont_show_clicked)

    def _on_open_download_clicked(self) -> None:
        self.should_dismiss_forever = self.dont_show_checkbox.isChecked()
        if self.download_url:
            QDesktopServices.openUrl(QUrl(self.download_url))
        self._finish(self.OPEN_DOWNLOAD, QDialog.DialogCode.Accepted)

    def _on_continue_clicked(self) -> None:
        self.should_dismiss_forever = self.dont_show_checkbox.isChecked()
        self._finish(self.CONTINUE, QDialog.DialogCode.Rejected)

    def _on_dont_show_clicked(self) -> None:
        self.should_dismiss_forever = True
        self._finish(self.DONT_SHOW_AGAIN, QDialog.DialogCode.Rejected)

    def reject(self) -> None:
        self.should_dismiss_forever = self.should_dismiss_forever or self.dont_show_checkbox.isChecked()
        super().reject()

    def _finish(self, decision: str, result: QDialog.DialogCode) -> None:
        self.decision = decision
        self.done(int(result))

    @staticmethod
    def should_show(settings: dict) -> bool:
        updates = settings.get("updates", {}) if isinstance(settings, dict) else {}
        if not isinstance(updates, dict):
            return True
        return not bool(updates.get("dismiss_final_release_notice", False))

    @classmethod
    def show_if_needed(
        cls,
        settings: dict,
        parent: QWidget | None = None,
        *,
        settings_manager: LauncherSettingsManager | None = None,
    ) -> bool:
        if not cls.should_show(settings):
            return False
        dialog = cls(parent=parent)
        dialog.exec()
        if dialog.should_dismiss_forever:
            manager = settings_manager or LauncherSettingsManager()
            manager.update_section("updates", {"dismiss_final_release_notice": True})
            return True
        return False
