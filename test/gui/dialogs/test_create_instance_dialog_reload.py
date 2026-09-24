import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.gui.dialogs.create_instance_dialog import CreateInstanceDialog
from src.models.modloader.fabric_loader_version import FabricLoaderVersion


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_create_instance_dialog_reload_button_behavior(app) -> None:
    dialog = CreateInstanceDialog()
    dialog.set_versions([
        SimpleNamespace(id="1.21.1", type="release"),
        SimpleNamespace(id="1.20.1", type="release"),
    ])

    # Initial state: vanilla selected, reload button should be disabled
    assert dialog.selected_loader() == "vanilla"
    assert not dialog.reload_loader_button.isEnabled()
    assert dialog.reload_loader_button.text() != ""
    assert not dialog.reload_loader_button.icon().isNull()

    # Track emitted reload signals
    reload_signals = []
    dialog.reload_loader_requested.connect(lambda loader, gv: reload_signals.append((loader, gv)))

    # Select Fabric
    idx = dialog.loader_combo.findData("fabric")
    assert idx >= 0
    dialog.loader_combo.setCurrentIndex(idx)

    assert dialog.selected_loader() == "fabric"
    assert dialog.reload_loader_button.isEnabled()

    # Simulate loader versions arrive
    versions = [
        FabricLoaderVersion(version="0.16.5", stable=True),
        FabricLoaderVersion(version="0.16.4", stable=False),
    ]
    dialog.set_fabric_versions("1.21.1", versions)

    assert dialog.loader_version_combo.count() == 2
    assert dialog.loader_version_combo.isEnabled()

    # Click reload button
    dialog.reload_loader_button.click()

    # Should have emitted reload_loader_requested with ("fabric", "1.21.1")
    assert len(reload_signals) == 1
    assert reload_signals[0] == ("fabric", "1.21.1")

    # The loader version combo should be cleared and disabled while reloading
    assert dialog.loader_version_combo.count() == 0
    assert not dialog.loader_version_combo.isEnabled()

    # If empty list was returned (e.g. failure), cache is not kept as valid
    dialog.set_fabric_versions("1.21.1", [])
    assert ("fabric", "1.21.1") not in dialog._pending_loader_requests
    assert dialog._loader_versions.get(("fabric", "1.21.1")) == []

    # Reload button remains enabled so user can retry
    assert dialog.reload_loader_button.isEnabled()

    dialog.reload_loader_button.click()
    assert len(reload_signals) == 2
    assert reload_signals[1] == ("fabric", "1.21.1")
