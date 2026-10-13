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


def _reload_hotfixed_core_modules() -> None:
    """Ensure any modules in hotfixes/live that were pre-loaded during bootstrap are refreshed."""
    try:
        import importlib
        import logging

        logger = logging.getLogger("mcw_core.hotfix_bootstrap")

        if getattr(sys, "frozen", False):
            project_root = Path(sys.executable).resolve().parent
        else:
            project_root = Path(__file__).resolve().parents[2]

        live_dir = project_root / "hotfixes" / "live"
        if not live_dir.is_dir():
            return

        reloaded = []
        for py_file in live_dir.rglob("*.py"):
            rel_path = py_file.relative_to(live_dir)
            parts = list(rel_path.parts)
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            if parts[-1] == "__init__":
                parts.pop()
            mod_name = ".".join(parts)
            if mod_name in sys.modules and mod_name != "src.gui.application":
                del sys.modules[mod_name]
                try:
                    importlib.import_module(mod_name)
                    reloaded.append(mod_name)
                except Exception as exc:
                    logger.debug("Failed to reimport hotfix module %s: %s", mod_name, exc)

        if "mcw_core.facade" in sys.modules:
            try:
                import mcw_core.facade

                importlib.reload(mcw_core.facade)
            except Exception as exc:
                logger.debug("Failed to reload mcw_core.facade: %s", exc)
        if "mcw_core" in sys.modules:
            try:
                import mcw_core

                importlib.reload(mcw_core)
            except Exception as exc:
                logger.debug("Failed to reload mcw_core: %s", exc)

        if reloaded:
            logger.info("Successfully reloaded %d hotfix modules from live: %s", len(reloaded), reloaded)
    except Exception:
        pass


_reload_hotfixed_core_modules()


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
