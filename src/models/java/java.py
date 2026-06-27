from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class JavaInstallation:
    version: int
    executable: Path
    source: str