from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.mod.mod_compatibility_manager import ModCompatibilityManager
from src.core.modloader.forge.forge_preflight_manager import ForgePreflightManager
from src.core.modloader.forge.forge_version_manager import ForgeVersionManager
from src.models.instance.instance import Instance
from src.models.mod.mod_issue import ModHealthReport, ModIssue


def make_instance(tmp_path: Path) -> Instance:
    return Instance(
        instance_id="id",
        name="Forge",
        version_id="1.20.1",
        instance_dir=tmp_path,
        mod_loader=("forge", "47.4.21"),
    )


def test_scan_combines_profile_and_mod_issues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    instance = make_instance(tmp_path)
    monkeypatch.setattr(ForgeVersionManager, "validate_installation", lambda *args, **kwargs: ["Profile is broken."])
    monkeypatch.setattr(
        ModCompatibilityManager,
        "scan",
        lambda _instance: ModHealthReport(
            issues=(
                ModIssue(severity="warning", code="optional", message="Optional dependency missing."),
                ModIssue(severity="error", code="loader-mismatch", message="Fabric mod in Forge instance."),
            ),
            enabled_mods=1,
            disabled_mods=0,
        ),
    )

    report = ForgePreflightManager.scan(instance, SimpleNamespace(raw_json={}))

    assert report.error_count == 2
    assert report.warning_count == 1
    assert report.issues[0].severity == "error"
    assert any("Profile is broken" in issue.message for issue in report.issues)


def test_raise_for_errors_formats_actionable_message():
    report = SimpleNamespace(
        can_launch=False,
        errors=(ModIssue(severity="error", code="dependency-missing", message="Architectury is missing."),),
        format_summary=lambda: "1 error(s), 0 warning(s)",
    )

    with pytest.raises(RuntimeError, match="Forge pre-launch check failed") as error:
        ForgePreflightManager.raise_for_errors(report)

    assert "Architectury is missing" in str(error.value)


def test_non_forge_instance_is_skipped(tmp_path: Path):
    instance = make_instance(tmp_path)
    instance.mod_loader = ("fabric", "0.16.0")

    report = ForgePreflightManager.scan(instance, SimpleNamespace(raw_json={}))

    assert report.can_launch
    assert report.issues == ()
