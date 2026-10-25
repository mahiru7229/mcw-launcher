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


_RELOADING_HOTFIX_MODULES = False


def _reload_hotfixed_core_modules() -> None:
    """Ensure any modules in hotfixes/live that were pre-loaded during bootstrap are refreshed."""
    global _RELOADING_HOTFIX_MODULES
    if _RELOADING_HOTFIX_MODULES:
        return

    _RELOADING_HOTFIX_MODULES = True
    _self_module = sys.modules.get(__name__)
    try:
        if getattr(sys, "frozen", False):
            project_root = Path(sys.executable).resolve().parent
        else:
            project_root = Path(__file__).resolve().parents[2]

        live_dir = project_root / "hotfixes" / "live"
        if not live_dir.is_dir():
            return

        import importlib

        live_str = str(live_dir.resolve())
        if live_str not in sys.path:
            sys.path.insert(0, live_str)

        sys.modules.pop("mcw_core.api.update.hotfix_manager", None)
        sys.modules.pop("src.core.update.hotfix_manager", None)

        hm_mod = importlib.import_module("src.core.update.hotfix_manager")
        try:
            importlib.import_module("mcw_core.api.update.hotfix_manager")
        except Exception:
            pass

        HotfixManager = getattr(hm_mod, "HotfixManager")
        HotfixManager._install_meta_path_finder(live_dir)
        HotfixManager._evict_cached_hotfix_modules(live_dir)
    except Exception:
        pass
    finally:
        if _self_module is not None:
            sys.modules[__name__] = _self_module
        _RELOADING_HOTFIX_MODULES = False


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
