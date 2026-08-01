from __future__ import annotations

import pytest

from src.core.theme.theme_palette import DEFAULT_THEME_PALETTE, derive_custom_accent, normalize_hex_color


def test_custom_accent_changes_primary_roles_but_preserves_semantic_colors() -> None:
    palette = derive_custom_accent(DEFAULT_THEME_PALETTE, "#B26CFF")

    assert palette.primary == "#b26cff"
    assert palette.primary_hover != palette.primary
    assert palette.primary_pressed != palette.primary
    assert palette.focus != DEFAULT_THEME_PALETTE.focus
    assert palette.success == DEFAULT_THEME_PALETTE.success
    assert palette.warning == DEFAULT_THEME_PALETTE.warning
    assert palette.error == DEFAULT_THEME_PALETTE.error


def test_hex_colors_are_normalized_and_invalid_values_are_rejected() -> None:
    assert normalize_hex_color("#12ABef") == "#12abef"
    with pytest.raises(ValueError):
        normalize_hex_color("blue")
