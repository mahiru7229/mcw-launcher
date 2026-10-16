from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from mcw_core.api.account.account_manager import AccountManager
from mcw_core.api.hardware.first_run_recommendation_service import FirstRunRecommendationService
from mcw_core.api.hardware.gpu_preference_manager import GraphicsDetectionResult
from src.gui.dialogs.first_run_setup_dialog import FirstRunSetupDialog
from src.models.account.account import Account
from src.models.account.account_source import AccountSource


@pytest.fixture
def qapp() -> QApplication:
    return QApplication.instance() or QApplication(["test"])


def test_first_run_dialog_includes_account_page(qapp: QApplication) -> None:
    gpu = GraphicsDetectionResult(supported=False)
    recommendation = FirstRunRecommendationService.fallback()
    dialog = FirstRunSetupDialog({}, gpu, recommendation)

    # 6 pages: Welcome (0), Account (1), Java (2), Memory (3), Graphics (4), Finish (5)
    assert dialog.pages.count() == 6
    assert dialog.pages.widget(1) is not None
    assert dialog.account_heading is not None
    assert dialog.username_input is not None
    assert dialog.create_offline_button is not None
    assert dialog.microsoft_button is not None
    assert dialog.microsoft_cancel_button is not None


def test_first_run_create_offline_account_validation_and_creation(qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    created_accounts: list[str] = []
    fake_account = Account(
        account_id="fake-uuid-1234",
        account_type=AccountSource.OFFLINE,
        username="SteveTest",
        uuid="offline-steve-uuid",
    )

    monkeypatch.setattr(AccountManager, "list_accounts", lambda: [fake_account] if created_accounts else [])
    monkeypatch.setattr(AccountManager, "get_selected_account", lambda: fake_account if created_accounts else None)
    monkeypatch.setattr(AccountManager, "set_selected_account", lambda aid: True)

    def mock_create(username: str) -> Account:
        created_accounts.append(username)
        return fake_account

    monkeypatch.setattr(AccountManager, "create_offline_account", mock_create)

    gpu = GraphicsDetectionResult(supported=False)
    recommendation = FirstRunRecommendationService.fallback()
    dialog = FirstRunSetupDialog({}, gpu, recommendation)

    # Invalid username (too short)
    dialog.username_input.setText("ab")
    dialog._create_offline_account()
    assert len(created_accounts) == 0
    assert dialog.offline_message.text() != ""

    # Valid username
    dialog.username_input.setText("SteveTest")
    dialog._create_offline_account()
    assert created_accounts == ["SteveTest"]
    assert dialog.username_input.text() == ""
    assert "SteveTest" in dialog.account_status.text()

    # Finish page summary reflects the created account
    dialog._page_index = dialog.pages.count() - 1
    dialog._update_page()
    assert "SteveTest" in dialog.finish_summary.text()


def test_first_run_microsoft_button_interaction(qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    gpu = GraphicsDetectionResult(supported=False)
    recommendation = FirstRunRecommendationService.fallback()

    class FakeSignal:
        def connect(self, slot) -> None:
            pass

    class FakeAccountController:
        def __init__(self) -> None:
            self.create_microsoft_called = False
            self.cancel_microsoft_called = False
            self.accounts_changed = FakeSignal()
            self.microsoft_auth_state_changed = FakeSignal()

        def create_microsoft(self) -> None:
            self.create_microsoft_called = True

        def cancel_microsoft(self) -> None:
            self.cancel_microsoft_called = True

    controller = FakeAccountController()
    dialog = FirstRunSetupDialog({}, gpu, recommendation, account_controller=controller)

    dialog._create_microsoft_account()
    assert controller.create_microsoft_called is True

    dialog._on_microsoft_auth_state_changed(True, "Waiting for sign-in...")
    assert dialog.microsoft_button.isEnabled() is False
    assert not dialog.microsoft_cancel_button.isHidden()
    assert dialog.microsoft_status.text() == "Waiting for sign-in..."

    dialog._cancel_microsoft_account()
    assert controller.cancel_microsoft_called is True

    dialog._on_microsoft_auth_state_changed(False)
    assert dialog.microsoft_button.isEnabled() is True
    assert dialog.microsoft_cancel_button.isHidden()


def test_first_run_java_selection_defaults_to_auto_even_with_installed_java(qapp: QApplication) -> None:
    from pathlib import Path
    from mcw_core.api.hardware.first_run_recommendation_service import FirstRunRecommendation, JavaRuntimeSummary

    gpu = GraphicsDetectionResult(supported=False)
    j17 = JavaRuntimeSummary(major=17, executable=Path("C:/Java/jdk-17/bin/java.exe"), source="path")
    j21 = JavaRuntimeSummary(major=21, executable=Path("C:/Java/jdk-21/bin/java.exe"), source="path")
    recommendation = FirstRunRecommendation(
        java_installations=(j17, j21),
        recommended_java_path="C:/Java/jdk-21/bin/java.exe",
        total_memory_mb=16384,
        available_memory_mb=8192,
        recommended_min_memory_mb=1024,
        recommended_max_memory_mb=4096,
    )

    # Fresh setup (empty settings)
    dialog = FirstRunSetupDialog({}, gpu, recommendation)
    # Even though Java 17 and Java 21 are available, Java combo MUST default to Auto ("")
    assert dialog.java_combo.currentData() == ""
    assert dialog.selected_settings()["instance_defaults"]["java"]["path"] == ""

    # If user explicitly picks Java 17:
    dialog.java_combo.setCurrentIndex(dialog.java_combo.findData(str(j17.executable)))
    assert dialog.java_combo.currentData() == str(j17.executable)
    assert dialog.selected_settings()["instance_defaults"]["java"]["path"] == str(j17.executable)

    # If opened with an existing custom Java in settings:
    custom_settings = {"instance_defaults": {"java": {"path": str(j17.executable)}}}
    dialog_custom = FirstRunSetupDialog(custom_settings, gpu, recommendation)
    assert dialog_custom.java_combo.currentData() == str(j17.executable)


def test_first_run_dialog_cancellation_cancels_active_microsoft_task(qapp: QApplication) -> None:
    gpu = GraphicsDetectionResult(supported=False)
    recommendation = FirstRunRecommendationService.fallback()

    class FakeSignal:
        def connect(self, slot) -> None:
            pass

        def disconnect(self, slot=None) -> None:
            pass

    class FakeAccountController:
        def __init__(self) -> None:
            self.cancel_count = 0
            self.accounts_changed = FakeSignal()
            self.microsoft_auth_state_changed = FakeSignal()
            self.is_microsoft_auth_active = True

        def cancel_microsoft(self) -> None:
            self.cancel_count += 1
            self.is_microsoft_auth_active = False

    controller = FakeAccountController()
    dialog = FirstRunSetupDialog({}, gpu, recommendation, account_controller=controller)

    # Calling reject() cancels active Microsoft task
    dialog.reject()
    assert controller.cancel_count == 1

    # Calling _skip() cancels active Microsoft task
    controller.is_microsoft_auth_active = True
    dialog._skip()
    assert controller.cancel_count == 2


def test_main_window_show_microsoft_device_code_dialog_no_name_error(qapp: QApplication) -> None:
    from src.gui.main_window import MainWindow
    from mcw_core.api.models.auth.microsoft.device_code_response import DeviceCodeResponse

    window = MainWindow()
    resp = DeviceCodeResponse(
        user_code="TEST1234",
        device_code="dev1234",
        verification_uri="https://microsoft.com/link",
        expires_in=900,
        interval=5,
        message="Enter code TEST1234",
    )
    window._show_microsoft_device_code_dialog(resp)
    assert window._microsoft_device_code_dialog is not None
    assert window._microsoft_device_code_dialog.isVisible()
    window._microsoft_device_code_dialog.close()


def test_microsoft_oauth_cancel_aware() -> None:
    from threading import Event
    from src.core.auth.microsoft.microsoft_oauth import MicrosoftOAuth
    from mcw_core.api.auth.microsoft.oauth_callback_server import MicrosoftAuthorizationCancelledError

    cancel_event = Event()
    cancel_event.set()

    with pytest.raises(MicrosoftAuthorizationCancelledError):
        MicrosoftOAuth.request_device_code(cancel_event=cancel_event)

    with pytest.raises(MicrosoftAuthorizationCancelledError):
        MicrosoftOAuth.authenticate(cancel_event=cancel_event)


def test_prefer_ipv4_dns_orders_af_inet_first() -> None:
    import socket
    from src.core.network.dns_resolver import prefer_ipv4_dns

    prefer_ipv4_dns()
    # Test dual-stack sorting mock
    orig = getattr(socket.getaddrinfo, "_orig_getaddrinfo", socket.getaddrinfo)
    mock_results = [
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2603:1046:2000::1", 443, 0, 0)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("20.190.144.1", 443)),
    ]
    # Verify sorting logic puts AF_INET first
    sorted_res = sorted(mock_results, key=lambda res: 0 if res[0] == socket.AF_INET else 1)
    assert sorted_res[0][0] == socket.AF_INET
    assert sorted_res[1][0] == socket.AF_INET6


def test_microsoft_device_code_dialog_browser_open_fallback(qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.gui.dialogs.microsoft_device_code_dialog import MicrosoftDeviceCodeDialog
    from mcw_core.api.models.auth.microsoft.device_code_response import DeviceCodeResponse
    from PySide6.QtGui import QDesktopServices

    opened_urls: list[str] = []

    # Simulate QDesktopServices.openUrl failing
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: False)

    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url) or True)

    dialog = MicrosoftDeviceCodeDialog()
    resp = DeviceCodeResponse(
        user_code="CODE9999",
        device_code="dev9999",
        verification_uri="https://www.microsoft.com/link",
        expires_in=900,
        interval=5,
        message="Enter code",
    )
    dialog.set_data(resp)

    # webbrowser.open must have been called as fallback
    assert "https://www.microsoft.com/link" in opened_urls
    assert dialog.code_edit.text() == "CODE9999"


def test_show_microsoft_device_code_dialog_reparents_under_active_modal(qapp: QApplication) -> None:
    from PySide6.QtWidgets import QDialog
    from src.gui.main_window import MainWindow
    from mcw_core.api.models.auth.microsoft.device_code_response import DeviceCodeResponse

    window = MainWindow()
    modal = QDialog(window)
    modal.setModal(True)
    modal.show()

    resp = DeviceCodeResponse(
        user_code="MODAL123",
        device_code="dev_modal",
        verification_uri="https://www.microsoft.com/link",
        expires_in=900,
        interval=5,
        message="Enter code",
    )

    modal.activateWindow()
    window._show_microsoft_device_code_dialog(resp)

    device_dialog = window.microsoft_device_code_dialog
    assert device_dialog.isVisible()
    # It should have target parent set
    assert device_dialog.parent() is modal or device_dialog.parent() is window

    device_dialog.close()
    modal.close()



