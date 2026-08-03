from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def test_main_window_uses_instance_workspace_as_primary_instance_frontend() -> None:
    path = PROJECT_ROOT / "src" / "gui" / "main_window_2.py"
    source = path.read_text(encoding="utf-8")
    imports = _imports(path)

    assert "src.gui.pages.instance_workspace_page" in imports
    assert "self.instances_page = InstanceWorkspacePage()" in source
    assert "self.right_panel.setVisible(False)" in source


def test_primary_navigation_is_instance_centered() -> None:
    path = PROJECT_ROOT / "src" / "gui" / "config.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    navigation: tuple[tuple[str, str], ...] | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "NAVIGATION_ITEMS" for target in node.targets):
            navigation = ast.literal_eval(node.value)
            break

    assert navigation is not None
    assert navigation[0][0] == "instances"
    assert {page_id for page_id, _label in navigation} == {"instances", "accounts", "launcher_settings", "logs", "about"}


def test_instance_workspace_supports_icons_and_runtime_badges() -> None:
    path = PROJECT_ROOT / "src" / "gui" / "pages" / "instance_workspace_page.py"
    source = path.read_text(encoding="utf-8")

    assert "change_icon_requested = Signal(str, object)" in source
    assert "reset_icon_requested = Signal(str)" in source
    assert '"loading": "icon.state.busy"' in source
    assert '"running": "icon.action.launch"' in source
    assert '"crashed": "icon.state.error"' in source
    assert '"finished": "icon.state.success"' in source
    assert "QStyle.StandardPixmap.SP_BrowserReload" in source
    assert "QStyle.StandardPixmap.SP_MediaPlay" in source
    assert 'if state == "ready":' in source
    assert "def _instance_state" in source
    assert "def set_health_reports" in source
    assert "def _instance_health_state" in source
    assert "self.health_label" in source
