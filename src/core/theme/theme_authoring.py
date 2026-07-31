from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import zipfile

from src.core.theme.theme_manager import ThemeDefinition, ThemeError, ThemeManager, theme_manager


class ThemeAuthoringError(RuntimeError):
    pass


@dataclass(frozen=True)
class ThemeValidationIssue:
    severity: str
    category: str
    message: str


@dataclass(frozen=True)
class ThemeValidationReport:
    theme_id: str
    name: str
    root: Path | None
    issues: tuple[ThemeValidationIssue, ...]

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0


class ThemeAuthoringService:
    THEME_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
    MAX_ARCHIVE_FILES = 2048
    MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
    ALLOWED_EXTENSIONS = frozenset({".json", ".png", ".ttf", ".otf", ".qss", ".md", ".txt", ".license"})
    ALLOWED_EXTENSIONLESS_NAMES = frozenset({"license", "copying", "notice"})
    EXCLUDED_NAMES = frozenset({"__pycache__", ".git", ".svn", ".hg"})

    def __init__(self, manager: ThemeManager | None = None) -> None:
        self.manager = manager or theme_manager

    def validate(self, theme_id: str) -> ThemeValidationReport:
        definition = self._definition(theme_id)
        if definition is None:
            return ThemeValidationReport(str(theme_id), str(theme_id), None, (ThemeValidationIssue("error", "manifest", f"Theme is not installed: {theme_id}"),))
        if definition.root is None:
            return ThemeValidationReport(definition.theme_id, definition.name, None, ())
        return self.validate_directory(definition.root)

    def validate_directory(self, root: Path) -> ThemeValidationReport:
        directory = Path(root).resolve()
        try:
            definition = self.manager._load_theme(directory)
        except ThemeError as error:
            issue = ThemeValidationIssue("error", self._category(str(error)), str(error))
            return ThemeValidationReport(directory.name, directory.name, directory, (issue,))
        issues = tuple(self._detail(message) for message in definition.issues)
        return ThemeValidationReport(definition.theme_id, definition.name, definition.root, issues)

    def duplicate(self, theme_id: str, new_id: str, new_name: str | None = None) -> ThemeDefinition:
        source = self._require_editable_theme(theme_id)
        normalized_id = self._normalize_theme_id(new_id)
        destination = (self.manager.root / normalized_id).resolve()
        self._ensure_inside_root(destination)
        if destination.exists():
            raise ThemeAuthoringError(f"Theme already exists: {normalized_id}")
        self._copy_theme_tree(source.root, destination)
        try:
            manifest_path = destination / self.manager.MANIFEST_NAME
            payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            payload["id"] = normalized_id
            payload["name"] = str(new_name or payload.get("name") or normalized_id).strip() or normalized_id
            manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            report = self.validate_directory(destination)
            if not report.is_valid:
                raise ThemeAuthoringError("Duplicated theme failed validation: " + "; ".join(issue.message for issue in report.issues))
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise
        self.manager.reload()
        return self._require_theme(normalized_id)

    def export(self, theme_id: str, destination: Path) -> Path:
        definition = self._require_editable_theme(theme_id)
        report = self.validate(theme_id)
        if not report.is_valid:
            raise ThemeAuthoringError("Theme contains validation errors and cannot be exported.")
        output = Path(destination)
        if output.suffix.lower() != ".zip":
            output = output.with_suffix(".zip")
        output.parent.mkdir(parents=True, exist_ok=True)
        entries = self._theme_files(definition.root)
        checksums = {relative: hashlib.sha256(path.read_bytes()).hexdigest() for path, relative in entries}
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path, relative in entries:
                archive.write(path, f"{definition.theme_id}/{relative}")
            archive.writestr(f"{definition.theme_id}/theme-checksums.json", json.dumps({"theme_id": definition.theme_id, "sha256": checksums}, indent=2) + "\n")
        return output

    def import_archive(self, archive_path: Path, overwrite: bool = False) -> ThemeDefinition:
        source = Path(archive_path)
        if not source.is_file():
            raise ThemeAuthoringError(f"Theme archive does not exist: {source}")
        self.manager.root.mkdir(parents=True, exist_ok=True)
        staging_root: Path | None = Path(tempfile.mkdtemp(prefix=".theme-import-", dir=self.manager.root))
        try:
            with zipfile.ZipFile(source) as archive:
                members = self._validated_archive_members(archive)
                prefix = self._archive_theme_prefix(members)
                for member in members:
                    relative = PurePosixPath(member.filename)
                    if prefix:
                        relative = PurePosixPath(*relative.parts[1:])
                    if not relative.parts:
                        continue
                    destination = staging_root.joinpath(*relative.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as input_file, destination.open("wb") as output_file:
                        shutil.copyfileobj(input_file, output_file)
            report = self.validate_directory(staging_root)
            if not report.is_valid:
                raise ThemeAuthoringError("Imported theme failed validation: " + "; ".join(issue.message for issue in report.issues))
            normalized_id = self._normalize_theme_id(report.theme_id)
            destination = (self.manager.root / normalized_id).resolve()
            self._ensure_inside_root(destination)
            if destination.exists():
                if not overwrite:
                    raise ThemeAuthoringError(f"Theme already exists: {normalized_id}")
                shutil.rmtree(destination)
            staging_root.replace(destination)
            staging_root = None
            self.manager.reload()
            return self._require_theme(normalized_id)
        except (OSError, zipfile.BadZipFile) as error:
            raise ThemeAuthoringError(f"Unable to import theme archive: {error}") from error
        finally:
            if staging_root is not None and staging_root.exists():
                shutil.rmtree(staging_root, ignore_errors=True)

    def _validated_archive_members(self, archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
        members = [member for member in archive.infolist() if not member.is_dir()]
        if not members or len(members) > self.MAX_ARCHIVE_FILES:
            raise ThemeAuthoringError("Theme archive has an invalid number of files.")
        total_bytes = 0
        for member in members:
            if member.flag_bits & 0x1:
                raise ThemeAuthoringError("Encrypted theme archives are not supported.")
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ThemeAuthoringError("Theme archives may not contain symbolic links.")
            path = PurePosixPath(member.filename.replace("\\", "/"))
            if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
                raise ThemeAuthoringError(f"Unsafe path in theme archive: {member.filename}")
            if any(part in self.EXCLUDED_NAMES for part in path.parts):
                raise ThemeAuthoringError(f"Disallowed directory in theme archive: {member.filename}")
            suffix = path.suffix.lower()
            if suffix not in self.ALLOWED_EXTENSIONS and path.name.casefold() not in self.ALLOWED_EXTENSIONLESS_NAMES:
                raise ThemeAuthoringError(f"Unsupported file type in theme archive: {member.filename}")
            total_bytes += int(member.file_size)
            if total_bytes > self.MAX_ARCHIVE_BYTES:
                raise ThemeAuthoringError("Theme archive exceeds the uncompressed size limit.")
        return members

    @staticmethod
    def _archive_theme_prefix(members: list[zipfile.ZipInfo]) -> str:
        paths = [PurePosixPath(member.filename.replace("\\", "/")) for member in members]
        root_manifest = any(path == PurePosixPath("theme.json") for path in paths)
        if root_manifest:
            return ""
        top_levels = {path.parts[0] for path in paths if path.parts}
        if len(top_levels) != 1:
            raise ThemeAuthoringError("Theme archive must contain one theme folder or a root theme.json.")
        prefix = next(iter(top_levels))
        if PurePosixPath(prefix, "theme.json") not in paths:
            raise ThemeAuthoringError("Theme archive does not contain theme.json.")
        return prefix

    def _theme_files(self, root: Path) -> list[tuple[Path, str]]:
        files: list[tuple[Path, str]] = []
        total_bytes = 0
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if any(part in self.EXCLUDED_NAMES for part in relative.parts) or path.is_symlink() or not path.is_file():
                continue
            if path.name.endswith((".tmp", ".bak")) or path.suffix.lower() in {".py", ".pyc", ".exe", ".dll", ".bat", ".cmd", ".ps1", ".js"}:
                continue
            total_bytes += path.stat().st_size
            if len(files) >= self.MAX_ARCHIVE_FILES or total_bytes > self.MAX_ARCHIVE_BYTES:
                raise ThemeAuthoringError("Theme exceeds export limits.")
            files.append((path, relative.as_posix()))
        return files

    def _copy_theme_tree(self, source: Path | None, destination: Path) -> None:
        if source is None:
            raise ThemeAuthoringError("Built-in CSS fallback cannot be duplicated.")
        for path in source.rglob("*"):
            if path.is_symlink():
                raise ThemeAuthoringError("Themes containing symbolic links cannot be duplicated.")
        shutil.copytree(source, destination)

    def _require_editable_theme(self, theme_id: str) -> ThemeDefinition:
        definition = self._require_theme(theme_id)
        if definition.root is None:
            raise ThemeAuthoringError("Built-in CSS fallback does not have an editable theme folder.")
        return definition

    def _require_theme(self, theme_id: str) -> ThemeDefinition:
        definition = self._definition(theme_id)
        if definition is None:
            raise ThemeAuthoringError(f"Theme is not installed: {theme_id}")
        return definition

    def _definition(self, theme_id: str) -> ThemeDefinition | None:
        normalized = str(theme_id or "").strip()
        return next((theme for theme in self.manager.available_themes() if theme.theme_id == normalized), None)

    def _normalize_theme_id(self, value: str) -> str:
        normalized = str(value or "").strip().lower().replace(" ", "-")
        if not self.THEME_ID_PATTERN.fullmatch(normalized):
            raise ThemeAuthoringError("Theme ID must use lowercase letters, numbers, dots, underscores, or hyphens.")
        return normalized

    def _ensure_inside_root(self, path: Path) -> None:
        try:
            path.relative_to(self.manager.root.resolve())
        except ValueError as error:
            raise ThemeAuthoringError("Theme path escapes the theme root.") from error

    @classmethod
    def _detail(cls, message: str) -> ThemeValidationIssue:
        lowered = message.casefold()
        warning = lowered.startswith("unknown ") or "capabilities must" in lowered
        severity = "warning" if warning else "error"
        return ThemeValidationIssue(severity, cls._category(message), message)

    @staticmethod
    def _category(message: str) -> str:
        lowered = message.casefold()
        if "font" in lowered:
            return "font"
        if "animation" in lowered or "sprite" in lowered:
            return "animation"
        if "motion" in lowered:
            return "motion"
        if "stylesheet" in lowered or "qss" in lowered:
            return "style"
        if "path" in lowered or "escapes" in lowered or "unsafe" in lowered or "symbolic" in lowered:
            return "security"
        if "manifest" in lowered or "schema" in lowered or "theme id" in lowered:
            return "manifest"
        return "asset"
