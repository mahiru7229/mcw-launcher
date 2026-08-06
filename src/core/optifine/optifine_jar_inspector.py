from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import zipfile

from src.models.optifine.optifine_models import OptiFineVersion


@dataclass(frozen=True, slots=True)
class InspectedOptiFineJar:
    path: Path
    filename: str
    sha256: str
    sha1: str
    size: int


class OptiFineJarInspector:
    MAX_SIZE = 128 * 1024 * 1024
    REQUIRED_ANY = {"optifine/Installer.class", "optifine/Config.class", "net/optifine/Config.class"}

    @classmethod
    def inspect(cls, path: Path, selected: OptiFineVersion | None = None) -> InspectedOptiFineJar:
        source = Path(path).expanduser().resolve(strict=False)
        if not source.is_file():
            raise FileNotFoundError(f"OptiFine JAR was not found: {source}")
        size = source.stat().st_size
        if size <= 0 or size > cls.MAX_SIZE:
            raise RuntimeError("The selected OptiFine file is empty or unexpectedly large.")
        if source.suffix.casefold() != ".jar":
            raise RuntimeError("Select an official OptiFine .jar file.")
        if not source.name.casefold().startswith("optifine_"):
            raise RuntimeError("The selected file does not look like an OptiFine installer JAR.")
        if selected is not None and source.name.casefold() != selected.filename.casefold():
            raise RuntimeError(f"Selected OptiFine version expects '{selected.filename}', but '{source.name}' was provided.")
        try:
            with zipfile.ZipFile(source) as archive:
                names = {name.replace("\\", "/") for name in archive.namelist()}
                if not names.intersection(cls.REQUIRED_ANY):
                    raise RuntimeError("The selected JAR does not contain the expected OptiFine classes.")
                if "META-INF/MANIFEST.MF" not in names:
                    raise RuntimeError("The selected JAR has no Java manifest.")
        except zipfile.BadZipFile as error:
            raise RuntimeError("The selected OptiFine JAR is corrupt or incomplete.") from error
        sha256 = hashlib.sha256()
        sha1 = hashlib.sha1()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                sha256.update(chunk)
                sha1.update(chunk)
        return InspectedOptiFineJar(source, source.name, sha256.hexdigest(), sha1.hexdigest(), size)
