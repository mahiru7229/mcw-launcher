from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.gui.dark_theme import apply_forced_dark_theme, configure_forced_dark_attributes
from src.gui.dialogs.message_box_compat import install_message_box_compatibility
from src.gui.input_guard import install_combo_box_wheel_guard
from src.gui.widget.adaptive_combo_box import install_adaptive_combo_boxes


def _application_icon_path() -> Path:
    if getattr(sys, "frozen", False):
        root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        root = Path(__file__).resolve().parents[2]
    return root / "assets" / "icons" / "mcw_launcher.png"


def create_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Create or reuse QApplication with a forced dark, non-native Qt appearance."""
    existing = QCoreApplication.instance()
    if existing is None:
        configure_forced_dark_attributes()
    if existing is not None and not isinstance(existing, QApplication):
        raise RuntimeError("A non-GUI Qt application already exists.")

    app = existing if isinstance(existing, QApplication) else QApplication(list(arguments) if arguments is not None else sys.argv)
    app.setApplicationName("MCW Launcher")
    icon_path = _application_icon_path()
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    apply_forced_dark_theme(app)

    if not hasattr(app, "_combo_box_wheel_guard"):
        app._combo_box_wheel_guard = install_combo_box_wheel_guard(app)
    if not hasattr(app, "_message_box_compatibility_filter"):
        app._message_box_compatibility_filter = install_message_box_compatibility(app)
    install_adaptive_combo_boxes(app)
    return app
