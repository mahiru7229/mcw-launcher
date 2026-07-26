from __future__ import annotations

from pathlib import Path

from src.models.curseforge.manual_download import CurseForgeManualDownload
from src.models.instance.instance import Instance


class CurseForgeManagedFilesRequired(RuntimeError):
    """Raised when managed CurseForge files require user-assisted recovery."""

    def __init__(self, instance: Instance, requirements: tuple[CurseForgeManualDownload, ...], message: str) -> None:
        super().__init__(message)
        self.instance_name = instance.name
        self.instance_dir = Path(instance.instance_dir)
        self.requirements = requirements
