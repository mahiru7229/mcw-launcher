from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from src.core.hardware.gpu_preference_manager import GraphicsAdapter, GraphicsDetectionResult
from src.gui.dialogs.first_run_setup_dialog import FirstRunSetupDialog


def test_first_run_setup_only_enables_gpu_option_when_dgpu_is_detected(gui_app) -> None:
    detection = GraphicsDetectionResult(
        supported=True,
        adapters=(GraphicsAdapter(name="NVIDIA GeForce RTX 4060", dedicated=True),),
    )
    dialog = FirstRunSetupDialog(
        {
            "gui": {"language": "en-US"},
            "updates": {"auto_check": True},
            "launch": {"prefer_dedicated_gpu": False},
            "onboarding": {"completed": False},
        },
        detection,
    )

    assert dialog.prefer_dedicated_gpu.isEnabled()
    assert not dialog.prefer_dedicated_gpu.isChecked()
    dialog.prefer_dedicated_gpu.setChecked(True)
    selected = dialog.selected_settings()
    assert selected["launch"]["prefer_dedicated_gpu"] is True
    assert selected["onboarding"] == {"completed": True, "version": FirstRunSetupDialog.SETUP_VERSION}


def test_first_run_setup_disables_gpu_option_without_dgpu(gui_app) -> None:
    dialog = FirstRunSetupDialog({}, GraphicsDetectionResult(supported=True))

    assert not dialog.prefer_dedicated_gpu.isEnabled()
    assert dialog.selected_settings()["launch"]["prefer_dedicated_gpu"] is False
