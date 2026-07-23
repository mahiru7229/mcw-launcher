from src.gui.style import APP_STYLE


def test_message_box_has_neutral_text_readable_on_light_or_dark_backgrounds() -> None:
    assert "QMessageBox {" in APP_STYLE
    assert "background: #f1f1f1;" in APP_STYLE
    assert "QMessageBox QLabel" in APP_STYLE
    assert "color: #767676;" in APP_STYLE


def test_compact_layout_has_smaller_navigation_and_titles() -> None:
    assert 'QPushButton#NavButton[compactLayout="true"]' in APP_STYLE
    assert 'QWidget#PageViewport[compactLayout="true"] QLabel#PageTitle' in APP_STYLE
