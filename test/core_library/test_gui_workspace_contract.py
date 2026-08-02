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
