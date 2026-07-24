from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import UPDATE_CHANNEL, VERSION, VERSION_ID, VERSION_TAG

TEXT_SUFFIXES = {".json", ".md", ".ps1", ".py", ".txt", ".yml", ".yaml"}
IGNORED_DIRECTORIES = {".git", ".pytest_cache", ".venv", "__pycache__", "build", "cache", "dist", "release"}
CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
PLACEHOLDER_PATTERN = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)[^{}]*\}(?!\})")


def iter_release_text_files(project_root: Path) -> Iterable[Path]:
    for path in project_root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(project_root).parts):
            continue
        yield path


def find_merge_markers(project_root: Path) -> list[str]:
    errors: list[str] = []
    for path in iter_release_text_files(project_root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(lines, start=1):
            if line.startswith(CONFLICT_MARKERS):
                errors.append(f"{path.relative_to(project_root)}:{line_number}: unresolved merge marker")
    return errors


def load_language_pack(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("language pack root must be an object")
    translations = payload.get("translations")
    if not isinstance(translations, dict):
        raise ValueError("language pack must contain a translations object")
    return payload


def placeholder_names(value: object) -> set[str]:
    return set(PLACEHOLDER_PATTERN.findall(str(value)))


def audit_language_packs(project_root: Path) -> list[str]:
    errors: list[str] = []
    english_path = project_root / "lang" / "en-US.json"
    vietnamese_path = project_root / "lang" / "vi-VN.json"
    try:
        english = load_language_pack(english_path)
        vietnamese = load_language_pack(vietnamese_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"Language pack error: {error}"]

    english_translations = english["translations"]
    vietnamese_translations = vietnamese["translations"]
    english_keys = set(english_translations)
    vietnamese_keys = set(vietnamese_translations)

    for key in sorted(english_keys - vietnamese_keys):
        errors.append(f"vi-VN is missing translation key: {key}")
    for key in sorted(vietnamese_keys - english_keys):
        errors.append(f"en-US is missing translation key: {key}")

    for key in sorted(english_keys | vietnamese_keys):
        if key in english_translations and not str(english_translations[key]).strip():
            errors.append(f"en-US has an empty translation: {key}")
        if key in vietnamese_translations and not str(vietnamese_translations[key]).strip():
            errors.append(f"vi-VN has an empty translation: {key}")
        if key in english_translations and key in vietnamese_translations:
            english_placeholders = placeholder_names(english_translations[key])
            vietnamese_placeholders = placeholder_names(vietnamese_translations[key])
            if english_placeholders != vietnamese_placeholders:
                errors.append(
                    f"Placeholder mismatch for {key}: en-US={sorted(english_placeholders)}, "
                    f"vi-VN={sorted(vietnamese_placeholders)}"
                )
    return errors


def audit_version_metadata(project_root: Path) -> list[str]:
    errors: list[str] = []
    if VERSION_TAG != f"v{VERSION_ID}":
        errors.append(f"VERSION_TAG must be v{VERSION_ID}, got {VERSION_TAG}")
    if VERSION_ID not in VERSION_TAG:
        errors.append("VERSION_ID is not represented by VERSION_TAG")
    if not VERSION.strip():
        errors.append("VERSION must not be empty")
    if UPDATE_CHANNEL not in {"stable", "beta"}:
        errors.append(f"Unsupported UPDATE_CHANNEL: {UPDATE_CHANNEL}")
    is_prerelease = any(marker in VERSION_ID.casefold() for marker in ("alpha", "beta", "rc"))
    expected_channel = "beta" if is_prerelease else "stable"
    if UPDATE_CHANNEL != expected_channel:
        errors.append(f"{VERSION_ID} must use update channel {expected_channel}, got {UPDATE_CHANNEL}")

    release_notes = project_root / "docs" / f"RELEASE-{VERSION_TAG}.md"
    if not release_notes.is_file():
        errors.append(f"Missing release notes: {release_notes.relative_to(project_root)}")
    for required in ("README.md", "LICENSE", "mcw_launcher.spec", "tools/build_release_zip.py"):
        if not (project_root / required).is_file():
            errors.append(f"Missing release file: {required}")
    return errors


def run_preflight(project_root: Path = PROJECT_ROOT) -> list[str]:
    errors: list[str] = []
    errors.extend(audit_version_metadata(project_root))
    errors.extend(find_merge_markers(project_root))
    errors.extend(audit_language_packs(project_root))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate MCW Launcher source before building a release.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    errors = run_preflight(project_root)
    if errors:
        print("Release preflight failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    translations = load_language_pack(project_root / "lang" / "en-US.json")["translations"]
    print(f"Release preflight passed for {VERSION_TAG} ({UPDATE_CHANNEL}).")
    print(f"Language parity: {len(translations)} keys in en-US and vi-VN.")
    print("Unresolved merge markers: 0")


if __name__ == "__main__":
    main()
