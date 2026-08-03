from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.hardware.gpu_preference_manager import GraphicsDetectionResult
from mcw_core.api.language.language_manager import language_manager, tr
from src.gui.localization import retranslate_widget_tree
from src.gui.window_sizing import resize_dialog_to_screen


class FirstRunSetupDialog(QDialog):
    SETUP_VERSION = 1

    def __init__(self, settings: dict, gpu_detection: GraphicsDetectionResult, parent=None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setObjectName("FirstRunSetupDialog")
        self._settings = settings if isinstance(settings, dict) else {}
        self._initial_locale = language_manager.current_locale
        self._gpu_detection = gpu_detection
        self._page_index = 0
        self._build_ui()
        resize_dialog_to_screen(self, 720, 520, 600, 440)
        self._load_values()
        self._update_page()
        retranslate_widget_tree(self)
        self.retranslate_dynamic()

    @staticmethod
    def should_show(settings: dict) -> bool:
        onboarding = settings.get("onboarding", {}) if isinstance(settings, dict) else {}
        return not bool(onboarding.get("completed", False))

    def selected_settings(self) -> dict:
        return {
            "gui": {"language": str(self.language_combo.currentData() or "en-US")},
            "updates": {"auto_check": self.auto_check_updates.isChecked()},
            "launch": {
                "prefer_dedicated_gpu": self.prefer_dedicated_gpu.isEnabled() and self.prefer_dedicated_gpu.isChecked(),
            },
            "onboarding": {"completed": True, "version": self.SETUP_VERSION},
        }

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(14)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        root.addWidget(self.title_label)

        self.page_indicator = QLabel()
        self.page_indicator.setObjectName("MutedLabel")
        root.addWidget(self.page_indicator)

        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        self.pages.addWidget(self._build_welcome_page())
        self.pages.addWidget(self._build_graphics_page())
        self.pages.addWidget(self._build_finish_page())

        button_row = QHBoxLayout()
        self.skip_button = QPushButton()
        self.back_button = QPushButton()
        self.next_button = QPushButton()
        self.next_button.setObjectName("PrimaryButton")
        self.skip_button.clicked.connect(self._skip)
        self.back_button.clicked.connect(self._back)
        self.next_button.clicked.connect(self._next)
        button_row.addWidget(self.skip_button)
        button_row.addStretch(1)
        button_row.addWidget(self.back_button)
        button_row.addWidget(self.next_button)
        root.addLayout(button_row)

    def _build_welcome_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        self.welcome_heading = QLabel()
        self.welcome_heading.setObjectName("SectionTitle")
        self.welcome_detail = QLabel()
        self.welcome_detail.setWordWrap(True)
        self.language_label = QLabel()
        self.language_combo = QComboBox()
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        self.auto_check_updates = QCheckBox()
        layout.addWidget(self.welcome_heading)
        layout.addWidget(self.welcome_detail)
        layout.addSpacing(8)
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_combo)
        layout.addWidget(self.auto_check_updates)
        layout.addStretch(1)
        return page

    def _build_graphics_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        self.graphics_heading = QLabel()
        self.graphics_heading.setObjectName("SectionTitle")
        self.graphics_detail = QLabel()
        self.graphics_detail.setWordWrap(True)
        self.gpu_status = QLabel()
        self.gpu_status.setObjectName("MutedLabel")
        self.gpu_status.setWordWrap(True)
        self.prefer_dedicated_gpu = QCheckBox()
        self.gpu_notice = QLabel()
        self.gpu_notice.setObjectName("MutedLabel")
        self.gpu_notice.setWordWrap(True)
        layout.addWidget(self.graphics_heading)
        layout.addWidget(self.graphics_detail)
        layout.addWidget(self.gpu_status)
        layout.addWidget(self.prefer_dedicated_gpu)
        layout.addWidget(self.gpu_notice)
        layout.addStretch(1)
        return page

    def _build_finish_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        self.finish_heading = QLabel()
        self.finish_heading.setObjectName("SectionTitle")
        self.finish_detail = QLabel()
        self.finish_detail.setWordWrap(True)
        self.finish_summary = QLabel()
        self.finish_summary.setWordWrap(True)
        self.finish_summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.finish_heading)
        layout.addWidget(self.finish_detail)
        layout.addWidget(self.finish_summary)
        layout.addStretch(1)
        return page

    def _load_values(self) -> None:
        gui = self._settings.get("gui", {}) if isinstance(self._settings.get("gui"), dict) else {}
        updates = self._settings.get("updates", {}) if isinstance(self._settings.get("updates"), dict) else {}
        launch = self._settings.get("launch", {}) if isinstance(self._settings.get("launch"), dict) else {}

        current_locale = str(gui.get("language") or "en-US")
        language_manager.reload()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        for language in language_manager.available_languages():
            self.language_combo.addItem(language.name, language.locale)
        index = self.language_combo.findData(current_locale)
        self.language_combo.setCurrentIndex(max(0, index))
        self.language_combo.blockSignals(False)
        self.auto_check_updates.setChecked(bool(updates.get("auto_check", True)))

        has_dgpu = self._gpu_detection.supported and self._gpu_detection.has_dedicated_gpu
        self.prefer_dedicated_gpu.setEnabled(has_dgpu)
        self.prefer_dedicated_gpu.setChecked(bool(launch.get("prefer_dedicated_gpu", False)) and has_dgpu)

    def _update_gpu_text(self) -> None:
        detection = self._gpu_detection
        if not detection.supported:
            self.gpu_status.setText(tr("gpu.preference.unsupported"))
        elif detection.error:
            self.gpu_status.setText(tr("gpu.preference.detect_failed", error=detection.error))
        elif detection.has_dedicated_gpu:
            names = ", ".join(adapter.name for adapter in detection.dedicated_adapters)
            self.gpu_status.setText(tr("gpu.preference.detected", adapters=names))
        else:
            self.gpu_status.setText(tr("gpu.preference.not_detected"))

    def _update_page(self) -> None:
        self.pages.setCurrentIndex(self._page_index)
        self.back_button.setEnabled(self._page_index > 0)
        self.page_indicator.setText(tr("first_run.page", current=self._page_index + 1, total=self.pages.count()))
        self.next_button.setText(tr("first_run.finish") if self._page_index == self.pages.count() - 1 else tr("first_run.next"))
        if self._page_index == self.pages.count() - 1:
            language_name = self.language_combo.currentText()
            gpu_value = tr("common.enabled") if self.prefer_dedicated_gpu.isChecked() else tr("common.disabled")
            updates_value = tr("common.enabled") if self.auto_check_updates.isChecked() else tr("common.disabled")
            self.finish_summary.setText(
                tr("first_run.summary", language=language_name, gpu=gpu_value, updates=updates_value)
            )

    def _language_changed(self, _index: int) -> None:
        locale = str(self.language_combo.currentData() or "en-US")
        language_manager.set_language(locale)
        retranslate_widget_tree(self)
        self.retranslate_dynamic()
        self._update_page()

    def _back(self) -> None:
        self._page_index = max(0, self._page_index - 1)
        self._update_page()

    def _next(self) -> None:
        if self._page_index < self.pages.count() - 1:
            self._page_index += 1
            self._update_page()
            return
        self.accept()

    def reject(self) -> None:
        language_manager.set_language(self._initial_locale)
        super().reject()

    def _skip(self) -> None:
        self.prefer_dedicated_gpu.setChecked(False)
        self.accept()

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("first_run.title"))
        self.title_label.setText(tr("first_run.title"))
        self.skip_button.setText(tr("first_run.skip"))
        self.back_button.setText(tr("first_run.back"))
        self.welcome_heading.setText(tr("first_run.welcome.title"))
        self.welcome_detail.setText(tr("first_run.welcome.detail"))
        self.language_label.setText(tr("first_run.language.label"))
        self.auto_check_updates.setText(tr("first_run.updates.toggle"))
        self.graphics_heading.setText(tr("first_run.graphics.title"))
        self.graphics_detail.setText(tr("first_run.graphics.detail"))
        self.prefer_dedicated_gpu.setText(tr("gpu.preference.toggle"))
        self.gpu_notice.setText(tr("gpu.preference.notice"))
        self.finish_heading.setText(tr("first_run.finish.title"))
        self.finish_detail.setText(tr("first_run.finish.detail"))
        self._update_gpu_text()
        self._update_page()
