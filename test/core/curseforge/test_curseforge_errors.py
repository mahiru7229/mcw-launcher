from pathlib import Path

from src.core.curseforge.curseforge_content_manager import CurseForgeManagedFilesRequired as ReExportedError
from src.core.curseforge.curseforge_errors import CurseForgeManagedFilesRequired
from src.models.curseforge.manual_download import CurseForgeManualDownload


class _Instance:
    name = "Test Instance"
    instance_dir = Path("instances/Test Instance")


def test_managed_files_required_is_reexported_for_backward_compatibility() -> None:
    assert ReExportedError is CurseForgeManagedFilesRequired


def test_managed_files_required_preserves_recovery_context() -> None:
    requirement = CurseForgeManualDownload(
        project_id=1,
        file_id=2,
        project_name="Example",
        file_name="example.jar",
        file_size=10,
        sha1="a" * 40,
        project_url="https://www.curseforge.com/minecraft/mc-mods/example/files/2",
        reason="Manual download required",
        managed_kind="pack",
        managed_path="mods/example.jar",
    )

    error = CurseForgeManagedFilesRequired(_Instance(), (requirement,), "Files are missing")

    assert error.instance_name == "Test Instance"
    assert error.instance_dir == Path("instances/Test Instance")
    assert error.requirements == (requirement,)
    assert str(error) == "Files are missing"
