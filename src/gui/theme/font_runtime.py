from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from mcw_core.api.theme.theme_font import ResolvedThemeFont
from mcw_core.api.theme.theme_manager import ThemeDefinition, ThemeManager, theme_manager


class ThemeFontRuntime:
    WEIGHTS = {
        100: QFont.Weight.Thin,
        200: QFont.Weight.ExtraLight,
        300: QFont.Weight.Light,
        400: QFont.Weight.Normal,
        500: QFont.Weight.Medium,
        600: QFont.Weight.DemiBold,
        700: QFont.Weight.Bold,
        800: QFont.Weight.ExtraBold,
        900: QFont.Weight.Black,
    }

    def __init__(self, manager: ThemeManager | None = None) -> None:
        self.manager = manager or theme_manager
        self._system_font: QFont | None = None
        self._registered_font_ids: list[int] = []
        self._active_family = ""
        self._active_fallback_families: tuple[str, ...] = ()
        self._active_point_size = 10.5
        self._active_weight = 400
        self._active_italic = False
        self._active_theme_id = ""

    @property
    def active_family(self) -> str:
        return self._active_family

    @property
    def active_theme_id(self) -> str:
        return self._active_theme_id

    def apply(self, application: QApplication | None = None, theme: ThemeDefinition | None = None) -> str | None:
        app = application or QApplication.instance()
        if app is None:
            return None
        if self._system_font is None:
            self._system_font = QFont(app.font())

        resolved = self.manager.resolve_font(theme, fallback_to_default=True)
        self._reset_registered_fonts(app)
        if resolved is None:
            self._active_theme_id = (theme or self.manager.current).theme_id
            return None

        loaded_families = self._load_font_files(resolved)
        if not loaded_families:
            self._reset_registered_fonts(app)
            self._active_theme_id = resolved.theme_id
            return None

        family = self._select_family(resolved, loaded_families)
        if not family:
            self._reset_registered_fonts(app)
            self._active_theme_id = resolved.theme_id
            return None

        definition = resolved.definition
        font = QFont(self._system_font)
        families = [family, *definition.fallback_families]
        if hasattr(font, "setFamilies"):
            font.setFamilies(families)
        else:
            font.setFamily(family)
        font.setPointSizeF(definition.point_size)
        font.setWeight(self.WEIGHTS[definition.weight])
        font.setItalic(definition.italic)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, definition.letter_spacing)
        app.setFont(font)

        self._active_family = family
        self._active_fallback_families = definition.fallback_families
        self._active_point_size = definition.point_size
        self._active_weight = definition.weight
        self._active_italic = definition.italic
        self._active_theme_id = resolved.theme_id
        return family

    def reset(self, application: QApplication | None = None) -> None:
        app = application or QApplication.instance()
        if app is None:
            return
        if self._system_font is None:
            self._system_font = QFont(app.font())
        self._reset_registered_fonts(app)
        self._active_theme_id = ""

    def stylesheet_rule(self) -> str:
        if not self._active_family:
            return ""
        families = [self._active_family, *self._active_fallback_families]
        encoded = ", ".join(f'"{self._escape_qss_string(family)}"' for family in families)
        style = "italic" if self._active_italic else "normal"
        size = f"{self._active_point_size:g}pt"
        return (
            "QWidget, QToolTip { "
            f"font-family: {encoded}; font-size: {size}; "
            f"font-weight: {self._active_weight}; font-style: {style}; "
            "}"
        )

    def _reset_registered_fonts(self, application: QApplication) -> None:
        if self._system_font is not None:
            application.setFont(QFont(self._system_font))
        for font_id in self._registered_font_ids:
            QFontDatabase.removeApplicationFont(font_id)
        self._registered_font_ids.clear()
        self._active_family = ""
        self._active_fallback_families = ()
        self._active_point_size = 10.5
        self._active_weight = 400
        self._active_italic = False

    def _load_font_files(self, resolved: ResolvedThemeFont) -> list[str]:
        families: list[str] = []
        for path in resolved.paths:
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id < 0:
                continue
            self._registered_font_ids.append(font_id)
            for family in QFontDatabase.applicationFontFamilies(font_id):
                normalized = str(family).strip()
                if normalized and normalized not in families:
                    families.append(normalized)
        return families

    @staticmethod
    def _select_family(resolved: ResolvedThemeFont, loaded_families: list[str]) -> str:
        requested = str(resolved.definition.family or "").strip()
        if requested:
            requested_casefold = requested.casefold()
            for family in loaded_families:
                if family.casefold() == requested_casefold:
                    return family
        return loaded_families[0] if loaded_families else ""

    @staticmethod
    def _escape_qss_string(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace('"', '\\"')


theme_font_runtime = ThemeFontRuntime()
