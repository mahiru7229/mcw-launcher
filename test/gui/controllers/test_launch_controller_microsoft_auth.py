from pathlib import Path


def test_launch_controller_uses_account_authentication_dispatcher() -> None:
    source = Path("src/gui/controllers/launch_controller.py").read_text(encoding="utf-8")

    assert "AccountAuthentication.authenticate(account)" in source
    assert "OfflineAuthentication.authenticate(account)" not in source
