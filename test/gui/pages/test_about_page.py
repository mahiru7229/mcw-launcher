from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from mcw_core.api.language.language_manager import language_manager
from src.config import DEVELOPER_NAME, VERSION_ID
from src.gui.pages.about_page import AboutPage


def test_about_page_ui_components_and_logo(gui_app):
    page = AboutPage()
    page.show()

    # Logo verification
    assert page.logo_label.pixmap() is not None
    assert not page.logo_label.pixmap().isNull()
    assert page.logo_label.width() == 72
    assert page.logo_label.height() == 72

    # Hero verification
    assert page.hero_title.text() == "MCW LAUNCHER"
    assert VERSION_ID in page.hero_version.text()

    # Project info verification
    assert DEVELOPER_NAME in page.developer_label.text()
    assert "MIT" in page.license_label.text()
    assert page.repo_label.openExternalLinks() is True
    assert "github.com/mahiru7229/mcw-launcher" in page.repo_label.text()

    # Ecosystem & References
    assert page.core_desc.openExternalLinks() is True
    assert "mcw_core" in page.core_desc.text()
    assert page.credits_desc.openExternalLinks() is True
    assert "PrismLauncher" in page.credits_desc.text()

    # Ensure removed cards are NOT present
    card_titles = [card.title_label.text() for card in page.findChildren(type(page.info_card)) if card.title_label is not None]
    assert "SRP architecture" not in card_titles
    assert "Kiến trúc SRP" not in card_titles
    assert "Theme assets" not in card_titles
    assert "Tài nguyên theme" not in card_titles

    # Dynamic retranslation test
    language_manager.set_language("vi-VN", notify=False)
    page.retranslate_dynamic()
    assert "Thông tin dự án" in page.info_card.title_label.text()
    assert "Dự án liên quan" in page.ecosystem_card.title_label.text()
    assert "Nguồn tham khảo" in page.credits_card.title_label.text()

    # Reset back to en-US
    language_manager.set_language("en-US", notify=False)
    page.retranslate_dynamic()
    assert "Project Information" in page.info_card.title_label.text()

    page.close()
