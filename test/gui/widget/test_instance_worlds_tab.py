from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from mcw_core.api.models.world.world_info import WorldInfo
from src.gui.widget.instance_worlds_tab import InstanceWorldsTab, WorldCardWidget


def _make_dummy_world(name: str = "World1") -> WorldInfo:
    return WorldInfo(
        folder_name=name,
        display_name=name,
        last_played=1700000000000,
        game_mode="survival",
        is_hardcore=False,
        version_name="1.20.1",
        folder_size_bytes=1024 * 1024,
    )


def test_world_card_play_button_visibility(gui_app, tmp_path: Path) -> None:
    inst_dir = tmp_path / "inst"
    inst_dir.mkdir()
    world = _make_dummy_world()

    # When quick play is supported (>= 1.20)
    card_supported = WorldCardWidget(inst_dir, world, quick_play_supported=True)
    card_supported.show()
    assert card_supported.play_button.isVisible() is True
    card_supported.close()

    # When quick play is NOT supported (< 1.20)
    card_unsupported = WorldCardWidget(inst_dir, world, quick_play_supported=False)
    card_unsupported.show()
    assert card_unsupported.play_button.isVisible() is False
    card_unsupported.close()


def test_instance_worlds_tab_adapts_to_version(gui_app, tmp_path: Path) -> None:
    inst_dir = tmp_path / "inst_worlds"
    saves_dir = inst_dir / "saves" / "MyWorld"
    saves_dir.mkdir(parents=True)
    (saves_dir / "level.dat").write_bytes(b"")

    tab = InstanceWorldsTab()
    tab.show()

    # Mock instance with 1.16.5
    inst_old = SimpleNamespace(instance_dir=str(inst_dir), version_id="1.16.5")
    tab.set_instance(inst_old)
    # Check created cards
    cards = [tab.cards_layout.itemAt(i).widget() for i in range(tab.cards_layout.count() - 1)]
    assert len(cards) == 1
    assert isinstance(cards[0], WorldCardWidget)
    assert cards[0].quick_play_supported is False
    assert cards[0].play_button.isVisible() is False

    # Switch to 1.20.4
    inst_new = SimpleNamespace(instance_dir=str(inst_dir), version_id="1.20.4")
    tab.set_instance(inst_new)
    cards = [tab.cards_layout.itemAt(i).widget() for i in range(tab.cards_layout.count() - 1)]
    assert len(cards) == 1
    assert cards[0].quick_play_supported is True
    assert cards[0].play_button.isVisible() is True
    tab.close()
