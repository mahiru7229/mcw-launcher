from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from mcw_core.api.language.language_manager import tr
from src.config import DEVELOPER_NAME, GITHUB_REPOSITORY, VERSION_ID
from src.gui.application import _application_icon_path
from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class AboutPage(BasePage):
    def __init__(self) -> None:
        super().__init__(tr("navigation.about"), tr("about.subtitle"), "about")
        self._build_ui()

    def _build_ui(self) -> None:
        # Header / Hero Card (Readme Header with Logo)
        self.hero_card = CardWidget("", object_name="AboutHeroCard")
        hero_layout = QHBoxLayout()
        hero_layout.setContentsMargins(10, 8, 10, 8)
        hero_layout.setSpacing(18)

        # Logo
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(72, 72)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = _application_icon_path()
        if icon_path.is_file():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                self.logo_label.setPixmap(pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        hero_layout.addWidget(self.logo_label)

        # Title + Version + Tagline
        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(6)

        title_hbox = QHBoxLayout()
        title_hbox.setSpacing(10)
        self.hero_title = QLabel("MCW LAUNCHER")
        self.hero_title.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        self.hero_version = QLabel(f"v{VERSION_ID}")
        self.hero_version.setStyleSheet("background: rgba(142, 211, 91, 0.18); color: #8ed35b; border: 1px solid rgba(142, 211, 91, 0.35); border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold;")
        title_hbox.addWidget(self.hero_title)
        title_hbox.addWidget(self.hero_version)
        title_hbox.addStretch(1)
        info_vbox.addLayout(title_hbox)

        self.hero_summary = QLabel(tr("about.summary"))
        self.hero_summary.setObjectName("MutedLabel")
        self.hero_summary.setWordWrap(True)
        info_vbox.addWidget(self.hero_summary)

        hero_layout.addLayout(info_vbox, 1)
        self.hero_card.layout.addLayout(hero_layout)
        self.root_layout.addWidget(self.hero_card)

        # Project Info Card
        self.info_card = CardWidget(tr("about.info.title"))
        self.developer_label = QLabel(tr("about.developer", developer=DEVELOPER_NAME))
        self.developer_label.setObjectName("ValueLabel")
        self.license_label = QLabel(tr("about.license"))
        self.license_label.setObjectName("MutedLabel")
        self.stack_label = QLabel(tr("about.stack"))
        self.stack_label.setObjectName("MutedLabel")

        repo_url = f"https://github.com/{GITHUB_REPOSITORY}"
        self.repo_label = QLabel(f'{tr("about.repository")} <a href="{repo_url}" style="color: #8ed35b;">{repo_url}</a>')
        self.repo_label.setOpenExternalLinks(True)

        self.info_card.layout.addWidget(self.developer_label)
        self.info_card.layout.addWidget(self.license_label)
        self.info_card.layout.addWidget(self.stack_label)
        self.info_card.layout.addWidget(self.repo_label)
        self.root_layout.addWidget(self.info_card)

        # Ecosystem & Core Engine Card
        self.ecosystem_card = CardWidget(tr("about.ecosystem.title"))
        self.core_desc = QLabel(
            f'• <b>MCW Core Engine:</b> {tr("about.ecosystem.core")}<br>'
            f'&nbsp;&nbsp;<a href="https://mahiru7229.github.io/mcw_core/index.html" style="color: #8ed35b;">https://mahiru7229.github.io/mcw_core/index.html</a>'
        )
        self.core_desc.setOpenExternalLinks(True)
        self.core_desc.setWordWrap(True)

        self.ecosystem_card.layout.addWidget(self.core_desc)
        self.root_layout.addWidget(self.ecosystem_card)

        # Credits & References Card
        self.credits_card = CardWidget(tr("about.credits.title"))
        self.credits_desc = QLabel(
            f'{tr("about.credits.prism")}<br>'
            f'<a href="https://github.com/PrismLauncher/PrismLauncher" style="color: #8ed35b;">https://github.com/PrismLauncher/PrismLauncher</a>'
        )
        self.credits_desc.setOpenExternalLinks(True)
        self.credits_desc.setWordWrap(True)
        self.credits_card.layout.addWidget(self.credits_desc)
        self.root_layout.addWidget(self.credits_card)

        self.root_layout.addStretch()

    def retranslate_dynamic(self) -> None:
        self.title_label.setText(tr("navigation.about"))
        self.subtitle_label.setText(tr("about.subtitle"))
        self.hero_version.setText(f"v{VERSION_ID}")
        self.hero_summary.setText(tr("about.summary"))
        if self.info_card.title_label:
            self.info_card.title_label.setText(tr("about.info.title"))
        self.developer_label.setText(tr("about.developer", developer=DEVELOPER_NAME))
        self.license_label.setText(tr("about.license"))
        self.stack_label.setText(tr("about.stack"))
        repo_url = f"https://github.com/{GITHUB_REPOSITORY}"
        self.repo_label.setText(f'{tr("about.repository")} <a href="{repo_url}" style="color: #8ed35b;">{repo_url}</a>')
        if self.ecosystem_card.title_label:
            self.ecosystem_card.title_label.setText(tr("about.ecosystem.title"))
        self.core_desc.setText(
            f'• <b>MCW Core Engine:</b> {tr("about.ecosystem.core")}<br>'
            f'&nbsp;&nbsp;<a href="https://mahiru7229.github.io/mcw_core/index.html" style="color: #8ed35b;">https://mahiru7229.github.io/mcw_core/index.html</a>'
        )
        if self.credits_card.title_label:
            self.credits_card.title_label.setText(tr("about.credits.title"))
        self.credits_desc.setText(
            f'{tr("about.credits.prism")}<br>'
            f'<a href="https://github.com/PrismLauncher/PrismLauncher" style="color: #8ed35b;">https://github.com/PrismLauncher/PrismLauncher</a>'
        )
