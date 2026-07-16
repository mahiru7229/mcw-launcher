from __future__ import annotations

import ast
import json
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[3]
_GUI_ROOT = _REPO_ROOT / "src" / "gui"
_LANGUAGE_PATH = _REPO_ROOT / "lang" / "en-US.json"

_WIDGET_CALL_ARGUMENTS = {
    "QLabel": (0,),
    "QPushButton": (0,),
    "QCheckBox": (0,),
    "QGroupBox": (0,),
    "CardWidget": (0, 1),
    "BasePage": (0, 1),
    "QAction": (0,),
}
_METHOD_CALL_ARGUMENTS = {
    "setText": (0,),
    "setToolTip": (0,),
    "setWindowTitle": (0,),
    "setPlaceholderText": (0,),
    "addTab": (1,),
    "setTabText": (1,),
    "addItem": (0,),
}
_ALLOWED_UNTRANSLATED = {
    "MCW LAUNCHER",
}


def _literal_argument(call: ast.Call, index: int) -> str | None:
    if index >= len(call.args):
        return None
    argument = call.args[index]
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        return argument.value
    return None


def test_static_gui_text_has_translation_key_or_english_alias() -> None:
    language_data = json.loads(_LANGUAGE_PATH.read_text(encoding="utf-8"))
    translations = set(language_data["translations"])
    aliases = language_data["aliases"]
    unresolved: list[str] = []

    for path in sorted(_GUI_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            function = node.func
            argument_indices: tuple[int, ...] = ()
            label = ""
            if isinstance(function, ast.Name) and function.id in _WIDGET_CALL_ARGUMENTS:
                label = function.id
                argument_indices = _WIDGET_CALL_ARGUMENTS[function.id]
            elif isinstance(function, ast.Attribute) and function.attr in _METHOD_CALL_ARGUMENTS:
                label = function.attr
                argument_indices = _METHOD_CALL_ARGUMENTS[function.attr]

            for index in argument_indices:
                text = _literal_argument(node, index)
                if not text or not text.strip() or text in _ALLOWED_UNTRANSLATED:
                    continue
                if text not in translations and text not in aliases:
                    relative = path.relative_to(_REPO_ROOT)
                    unresolved.append(f"{relative}:{node.lineno} [{label}] {text!r}")

            if isinstance(function, ast.Name) and function.id == "tr":
                text = _literal_argument(node, 0)
                if text and text not in translations and text not in aliases:
                    relative = path.relative_to(_REPO_ROOT)
                    unresolved.append(f"{relative}:{node.lineno} [tr] {text!r}")

    assert unresolved == [], "Untranslated static GUI text:\n" + "\n".join(unresolved)


def test_all_english_aliases_point_to_existing_translation_keys() -> None:
    language_data = json.loads(_LANGUAGE_PATH.read_text(encoding="utf-8"))
    translations = set(language_data["translations"])
    invalid = {source: key for source, key in language_data["aliases"].items() if key not in translations}

    assert invalid == {}
