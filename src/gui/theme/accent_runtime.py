from __future__ import annotations

import hashlib
from pathlib import Path

from PySide6.QtGui import QColor, QImage, QPalette, QPixmap
from PySide6.QtWidgets import QApplication

from mcw_core.api.fs.paths import Paths
from mcw_core.api.theme.theme_manager import ThemeDefinition, ThemeManager, theme_manager
from mcw_core.api.theme.theme_palette import DEFAULT_THEME_PALETTE, ThemePaletteDefinition, derive_custom_accent, derive_custom_text, normalize_hex_color
from src.gui.dark_theme import create_forced_dark_palette


class ThemeAccentRuntime:
    def __init__(self, manager: ThemeManager | None = None) -> None:
        self.manager = manager or theme_manager
        self._theme = self.manager.current
        self._mode = "theme"
        self._custom_color = DEFAULT_THEME_PALETTE.focus
        self._text_mode = "theme"
        self._custom_text_color = DEFAULT_THEME_PALETTE.text_primary
        self._palette = self._theme.palette

    @property
    def palette(self) -> ThemePaletteDefinition:
        return self._palette

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def custom_color(self) -> str:
        return self._custom_color

    def configure(self, theme: ThemeDefinition, mode: str = "theme", custom_color: str = "#8ed35b", text_mode: str = "theme", custom_text_color: str = "#f4f4f4") -> ThemePaletteDefinition:
        normalized_mode = str(mode or "theme").strip().lower()
        self._theme = theme
        self._mode = normalized_mode if normalized_mode in {"theme", "custom"} else "theme"
        try:
            self._custom_color = normalize_hex_color(custom_color or "#8ed35b")
        except ValueError:
            self._custom_color = "#8ed35b"
        self._text_mode = str(text_mode or "theme").strip().lower()
        if self._text_mode not in {"theme", "custom"}:
            self._text_mode = "theme"
        try:
            self._custom_text_color = normalize_hex_color(custom_text_color or DEFAULT_THEME_PALETTE.text_primary)
        except ValueError:
            self._custom_text_color = DEFAULT_THEME_PALETTE.text_primary
        palette = derive_custom_accent(theme.palette, self._custom_color) if self._mode == "custom" else theme.palette
        self._palette = derive_custom_text(palette, self._custom_text_color) if self._text_mode == "custom" else palette
        return self._palette

    @property
    def enabled(self) -> bool:
        return self._mode == "custom" or self._text_mode == "custom" or "theme_palette" in self._theme.capabilities

    def apply_application_palette(self, application: QApplication) -> None:
        if not self.enabled:
            application.setPalette(create_forced_dark_palette(application.palette()))
            return
        colors = self._palette
        palette = create_forced_dark_palette(
            application.palette(),
            selection_color=QColor(colors.selection),
            selection_text_color=QColor(colors.selection_text),
            link_color=QColor(colors.link),
        )
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, QColor(colors.selection))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor(colors.selection))
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor(colors.selection_text))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor(colors.selection_text))
        for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
            palette.setColor(QPalette.ColorGroup.Active, role, QColor(colors.text_primary))
            palette.setColor(QPalette.ColorGroup.Inactive, role, QColor(colors.text_primary))
            palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(colors.text_disabled))
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, QColor(colors.text_muted))
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, QColor(colors.text_muted))
        application.setPalette(palette)

    def stylesheet_rule(self) -> str:
        if not self.enabled:
            return ""
        colors = self._palette
        return f"""
QWidget {{
    color: {colors.text_primary};
}}
QLabel#MutedLabel, QLabel#CardSubtitle, QLabel#PageSubtitle, QLabel#SectionSubtitle, QLabel#TinyLabel {{
    color: {colors.text_muted};
}}
QWidget:disabled, QPushButton:disabled, QCheckBox:disabled, QRadioButton:disabled,
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {colors.text_disabled};
}}
QPushButton#PrimaryButton {{
    background-color: {colors.primary};
    color: {colors.primary_text};
}}
QPushButton#PrimaryButton:hover {{
    background-color: {colors.primary_hover};
    color: {colors.primary_text};
}}
QPushButton#PrimaryButton:pressed {{
    background-color: {colors.primary_pressed};
    color: {colors.primary_text};
}}
QPushButton#NavButton:checked {{
    background-color: {colors.selection};
    color: {colors.selection_text};
    border-color: {colors.primary_pressed};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {colors.focus};
}}
QProgressBar::chunk {{
    background-color: {colors.primary};
}}
QCheckBox::indicator:checked {{
    background-color: {colors.primary};
    border-color: {colors.primary_pressed};
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: {colors.primary_pressed};
}}
QTableWidget::item:selected, QListView::item:selected, QTreeView::item:selected,
QComboBox QAbstractItemView::item:selected, QMenu::item:selected {{
    background-color: {colors.selection};
    color: {colors.selection_text};
}}
QLabel#StatusBadge, QLabel#StageBadge[state="success"] {{
    background-color: {colors.success};
    color: {self._contrast_text(colors.success)};
}}
QLabel#WarningBadge, QLabel#StageBadge[state="warning"], QLabel#StageBadge[state="busy"] {{
    border-color: {colors.warning};
}}
QLabel#StageBadge[state="error"] {{
    border-color: {colors.error};
}}
QLabel[themeLink="true"], QPushButton[themeLink="true"] {{
    color: {colors.link};
}}
""".strip()

    def should_tint(self, key: str) -> bool:
        return str(key) in self._theme.accent_assets

    def tint_pixmap(self, pixmap: QPixmap, key: str) -> QPixmap:
        if pixmap.isNull() or not self.should_tint(key):
            return pixmap
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        tinted = self._tint_image(image, QColor(self._color_for_key(key)))
        return QPixmap.fromImage(tinted)

    def tinted_path(self, path: Path, key: str) -> Path:
        source = Path(path)
        if not self.should_tint(key):
            return source
        try:
            stat = source.stat()
        except OSError:
            return source
        token = self._color_for_key(key)
        digest = hashlib.sha256(f"{source.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|{key}|{token}".encode("utf-8")).hexdigest()[:24]
        output = Paths.CACHE_ROOT / "themes" / "accent" / self._theme.theme_id / digest / source.name
        if output.is_file():
            return output
        image = QImage(str(source))
        if image.isNull():
            return source
        output.parent.mkdir(parents=True, exist_ok=True)
        tinted = self._tint_image(image.convertToFormat(QImage.Format.Format_ARGB32), QColor(token))
        if not tinted.save(str(output), "PNG"):
            return source
        return output

    def _color_for_key(self, key: str) -> str:
        normalized = str(key).casefold()
        if "warning" in normalized:
            return self._palette.warning
        if any(token in normalized for token in ("error", "danger", "cancel")):
            return self._palette.error
        if any(token in normalized for token in ("success", "ready", "status")):
            return self._palette.success
        if "hover" in normalized:
            return self._palette.primary_hover
        if "pressed" in normalized:
            return self._palette.primary_pressed
        return self._palette.primary

    @staticmethod
    def _tint_image(image: QImage, color: QColor) -> QImage:
        output = QImage(image.size(), QImage.Format.Format_ARGB32)
        target_hue = color.hslHueF()
        target_saturation = color.hslSaturationF()
        if target_hue < 0:
            target_hue = 0.0
        for y in range(image.height()):
            for x in range(image.width()):
                source = QColor.fromRgba(image.pixel(x, y))
                if source.alpha() == 0:
                    output.setPixelColor(x, y, source)
                    continue
                lightness = source.lightnessF()
                saturation = max(0.12, min(1.0, target_saturation * (0.55 + source.saturationF() * 0.45)))
                tinted = QColor.fromHslF(target_hue, saturation, lightness, source.alphaF())
                output.setPixelColor(x, y, tinted)
        return output

    @staticmethod
    def _contrast_text(color: str) -> str:
        value = QColor(color)
        luminance = (0.2126 * value.redF()) + (0.7152 * value.greenF()) + (0.0722 * value.blueF())
        return "#111111" if luminance > 0.62 else "#ffffff"


theme_accent_runtime = ThemeAccentRuntime()
