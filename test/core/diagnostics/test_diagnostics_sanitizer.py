from pathlib import Path

from src.core.diagnostics.diagnostics_sanitizer import DiagnosticsSanitizer


def test_sanitize_text_removes_windows_drive_letters_and_normalizes_paths(monkeypatch) -> None:
    monkeypatch.setattr(DiagnosticsSanitizer, "_known_roots", classmethod(lambda cls: ((Path("C:/mcw_launcher"), "root"),)))

    text = DiagnosticsSanitizer.sanitize_text(
        'File "C:\\mcw_launcher\\src\\gui\\main_window_2.py" and D:\\Private\\logs\\latest.log'
    )

    assert "C:" not in text
    assert "D:" not in text
    assert "root/src/gui/main_window_2.py" in text
    assert "root/Private/logs/latest.log" in text


def test_sanitize_text_hides_unc_server_and_share(monkeypatch) -> None:
    monkeypatch.setattr(DiagnosticsSanitizer, "_known_roots", classmethod(lambda cls: ()))

    text = DiagnosticsSanitizer.sanitize_text(r"\\NAS-SERVER\PrivateShare\folder\file.log")

    assert "NAS-SERVER" not in text
    assert "PrivateShare" not in text
    assert text == "root/folder/file.log"


def test_sanitize_text_does_not_modify_https_urls(monkeypatch) -> None:
    monkeypatch.setattr(DiagnosticsSanitizer, "_known_roots", classmethod(lambda cls: ()))
    url = "https://api.adoptium.net/v3/assets/latest/8/hotspot"

    assert DiagnosticsSanitizer.sanitize_text(url) == url


def test_runtime_sanitizer_redacts_players_and_uuids(monkeypatch) -> None:
    monkeypatch.setattr(DiagnosticsSanitizer, "_known_roots", classmethod(lambda cls: ()))
    text = "ServerPlayer['Mahiru'/123] crash id 123e4567-e89b-12d3-a456-426614174000"

    result = DiagnosticsSanitizer.sanitize_text(text, runtime_log=True)

    assert "Mahiru" not in result
    assert "123e4567-e89b-12d3-a456-426614174000" not in result
    assert "<player>" in result
    assert "<uuid>" in result


def test_sanitize_path_uses_root_alias_without_drive_letter(monkeypatch) -> None:
    monkeypatch.setattr(DiagnosticsSanitizer, "_known_roots", classmethod(lambda cls: ((Path("C:/mcw_launcher"), "root"),)))

    assert DiagnosticsSanitizer.sanitize_path(r"C:\mcw_launcher\instances\RLCraft\logs\latest.log") == "root/instances/RLCraft/logs/latest.log"
