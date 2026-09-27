from pathlib import Path

import pytest

from launcher import _validate_startup_dependencies


def test_current_source_contains_required_startup_dependencies() -> None:
    project_root = Path(__file__).resolve().parents[2]

    _validate_startup_dependencies(project_root)


def test_incomplete_source_reports_all_missing_dependencies(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError) as captured:
        _validate_startup_dependencies(tmp_path)

    message = str(captured.value)
    assert "installation is incomplete" in message
    assert "mcw_core/api/lan/lan_agent_manager.py" in message
    assert "mcw_core/api/curseforge/curseforge_errors.py" in message
    assert "mcw_core/rpc/dispatcher.py" in message
    assert "runtime/mcw-lan-agent.jar" in message
