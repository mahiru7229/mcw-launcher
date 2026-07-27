from __future__ import annotations

import json
from pathlib import Path

from src.config import VERSION_TAG
from tools.release_preflight import audit_language_packs, audit_private_gateway_bundling, find_merge_markers


def write_pack(path: Path, locale: str, translations: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "meta": {"locale": locale, "name": locale, "version": 1},
                "translations": translations,
                "aliases": {},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_find_merge_markers_reports_release_text_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("before\n<<<<<<< HEAD\nafter\n", encoding="utf-8")
    errors = find_merge_markers(tmp_path)
    assert errors == ["README.md:2: unresolved merge marker"]


def test_language_audit_accepts_matching_keys_and_placeholders(tmp_path: Path) -> None:
    translations = {"hello": "Hello", "welcome": "Welcome {name}"}
    write_pack(tmp_path / "lang" / "en-US.json", "en-US", translations)
    write_pack(tmp_path / "lang" / "vi-VN.json", "vi-VN", {"hello": "Xin chào", "welcome": "Chào mừng {name}"})
    assert audit_language_packs(tmp_path) == []


def test_language_audit_reports_missing_keys_and_placeholder_mismatch(tmp_path: Path) -> None:
    write_pack(tmp_path / "lang" / "en-US.json", "en-US", {"welcome": "Welcome {name}", "missing": "Missing"})
    write_pack(tmp_path / "lang" / "vi-VN.json", "vi-VN", {"welcome": "Chào mừng {username}"})
    errors = audit_language_packs(tmp_path)
    assert "vi-VN is missing translation key: missing" in errors
    assert any(error.startswith("Placeholder mismatch for welcome:") for error in errors)


def test_current_release_notes_exist() -> None:
    project_root = Path(__file__).resolve().parents[2]
    assert (project_root / "docs" / f"RELEASE-{VERSION_TAG}.md").is_file()


def test_private_gateway_audit_rejects_unexpected_or_secret_configuration(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "config.py").write_text(
        'CURSEFORGE_GATEWAY_URL = "https://private.example/api/curseforge"\n'
        'CURSEFORGE_DEFAULT_GATEWAY_URL = "https://private.example/api/curseforge"\n'
        'CURSEFORGE_API_KEY = "secret"\n',
        encoding="utf-8",
    )
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "curseforge.example.json").write_text(
        json.dumps({
            "default_gateway_url": "https://private.example/api/curseforge",
            "bundled_gateway_urls": ["https://another-private.example/api/curseforge"],
        }),
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")

    errors = audit_private_gateway_bundling(tmp_path)

    assert any("legacy private gateway constants" in error for error in errors)
    assert "src/config.py contains an unexpected CurseForge default gateway URL" in errors
    assert "CurseForge API credentials must not be bundled in src/config.py" in errors
    assert "config/curseforge.example.json must document the public default gateway URL" in errors
    assert "config/curseforge.example.json must not contain additional bundled gateway URLs" in errors
    assert ".gitignore must exclude config/private/" in errors


def test_private_gateway_audit_accepts_public_default(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "config.py").write_text(
        'CURSEFORGE_DEFAULT_GATEWAY_URL = "https://mcw-curseforge-gateway.vercel.app/api/curseforge"\n',
        encoding="utf-8",
    )
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "curseforge.example.json").write_text(
        json.dumps({"default_gateway_url": "https://mcw-curseforge-gateway.vercel.app/api/curseforge"}),
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text("config/private/\n", encoding="utf-8")

    assert audit_private_gateway_bundling(tmp_path) == []
