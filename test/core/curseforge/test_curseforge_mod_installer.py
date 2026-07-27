from src.core.curseforge.curseforge_mod_installer import CurseForgeModInstaller
from src.models.curseforge.file import CurseForgeFile


def make_file(*, loaders=("fabric",)) -> CurseForgeFile:
    return CurseForgeFile(
        file_id=20,
        project_id=10,
        display_name="Universal build labelled as Fabric",
        file_name="universal.jar",
        release_type="release",
        file_date="2026-07-25T00:00:00Z",
        file_length=100,
        download_url="https://example.invalid/universal.jar",
        sha1="a" * 40,
        game_versions=("1.20.1",),
        dependencies=(),
        loaders=loaders,
    )


def test_build_plan_accepts_advisory_loader_mismatch_for_jar_validation() -> None:
    root = make_file(loaders=("fabric",))

    plan = CurseForgeModInstaller._build_plan(
        root,
        game_version="1.20.1",
        loader="forge",
        install_dependencies=False,
        allowed_release_types=("release",),
    )

    assert plan == [root]


def test_build_plan_allows_missing_game_version_metadata_for_jar_validation() -> None:
    root = make_file(loaders=("fabric",))
    root = CurseForgeFile(
        file_id=root.file_id,
        project_id=root.project_id,
        display_name=root.display_name,
        file_name=root.file_name,
        release_type=root.release_type,
        file_date=root.file_date,
        file_length=root.file_length,
        download_url=root.download_url,
        sha1=root.sha1,
        game_versions=(),
        dependencies=root.dependencies,
        loaders=root.loaders,
    )

    plan = CurseForgeModInstaller._build_plan(
        root,
        game_version="1.20.1",
        loader="forge",
        install_dependencies=False,
        allowed_release_types=("release",),
    )

    assert plan == [root]
