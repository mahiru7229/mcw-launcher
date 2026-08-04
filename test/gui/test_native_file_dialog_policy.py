from pathlib import Path


def test_launcher_does_not_disable_native_windows_file_dialogs() -> None:
    source = Path("src/gui/dark_theme.py").read_text(encoding="utf-8")
    assert "AA_DontUseNativeDialogs" not in source
