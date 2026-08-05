from pathlib import Path

from src.core.language.language_manager import LanguageManager


def test_dynamic_progress_message_is_localized() -> None:
    manager = LanguageManager(Path(__file__).resolve().parents[1] / "lang")
    manager.set_language("vi-VN", notify=False)

    assert manager.translate("Downloading Fabulously Optimized manifest...") == "Đang tải manifest của Fabulously Optimized..."


def test_core_progress_messages_are_localized_in_vietnamese() -> None:
    manager = LanguageManager(Path(__file__).resolve().parents[1] / "lang")
    manager.set_language("vi-VN", notify=False)

    assert manager.translate("Preparing Minecraft libraries...") == "Đang chuẩn bị thư viện Minecraft..."
    assert manager.translate("Preparing Minecraft assets...") == "Đang chuẩn bị asset Minecraft..."
    assert manager.translate("Checking CurseForge files...") == "Đang kiểm tra các file CurseForge..."
    assert manager.translate("Checking CurseForge files after round 2/3...") == "Đang kiểm tra lại các file CurseForge sau lượt 2/3..."
