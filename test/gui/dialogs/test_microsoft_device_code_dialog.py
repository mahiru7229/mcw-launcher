import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication
from src.gui.dialogs.microsoft_device_code_dialog import MicrosoftDeviceCodeDialog
from src.models.auth.microsoft.device_code_response import DeviceCodeResponse
from src.gui.media.minecraft_skin import account_skin_face_icon, default_skin_face_pixmap, default_skin_face_icon
from src.models.account.account import Account
from src.models.account.account_source import AccountSource


def test_device_code_dialog_displays_and_copies(gui_app, monkeypatch):
    dialog = MicrosoftDeviceCodeDialog()
    resp = DeviceCodeResponse(
        device_code="dev123",
        user_code="ABCD-1234",
        verification_uri="https://www.microsoft.com/link",
        expires_in=900,
        interval=5,
        message="Enter code",
    )
    dialog.set_data(resp)

    assert dialog.code_edit.text() == "ABCD-1234"
    assert "https://www.microsoft.com/link" in dialog.url_label.text()

    # Test copy button
    dialog._copy_code()
    assert dialog.copy_button.text() == "Copied!"

    # Test cancel
    cancelled = []
    dialog.cancel_requested.connect(lambda: cancelled.append(True))
    dialog._on_cancel()
    assert cancelled == [True]


def test_default_skin_face_fallback(gui_app):
    steve_pixmap = default_skin_face_pixmap("classic", 32)
    assert not steve_pixmap.isNull()
    assert steve_pixmap.width() == 32
    assert steve_pixmap.height() == 32

    alex_pixmap = default_skin_face_pixmap("slim", 32)
    assert not alex_pixmap.isNull()

    account = Account(
        account_id="acc1",
        account_type=AccountSource.OFFLINE,
        username="TestPlayer",
        uuid="11111111111111111111111111111111",
    )
    icon = account_skin_face_icon(account, 32)
    assert not icon.isNull()
