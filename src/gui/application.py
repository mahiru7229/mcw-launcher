from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from src.gui.dark_theme import apply_forced_dark_theme, configure_forced_dark_attributes
from src.gui.dialogs.message_box_compat import install_message_box_compatibility
from src.gui.input_guard import install_combo_box_wheel_guard


def create_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Create or reuse QApplication with a forced dark, non-native Qt appearance."""
    existing = QCoreApplication.instance()
    if existing is None:
        configure_forced_dark_attributes()
    if existing is not None and not isinstance(existing, QApplication):
        raise RuntimeError("A non-GUI Qt application already exists.")

    app = existing if isinstance(existing, QApplication) else QApplication(list(arguments) if arguments is not None else sys.argv)
    app.setApplicationName("MCW Launcher")
    apply_forced_dark_theme(app)

    if not hasattr(app, "_combo_box_wheel_guard"):
        app._combo_box_wheel_guard = install_combo_box_wheel_guard(app)
    if not hasattr(app, "_message_box_compatibility_filter"):
        app._message_box_compatibility_filter = install_message_box_compatibility(app)
    return app
