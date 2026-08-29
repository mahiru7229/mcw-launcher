from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_release_asset_upload_names_repository_explicitly() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "gh release upload" in workflow
    assert '--repo "${{ github.repository }}"' in workflow
