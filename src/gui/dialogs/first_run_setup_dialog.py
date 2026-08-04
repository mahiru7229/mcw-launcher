from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mcw_core.api.hardware.first_run_recommendation_service import FirstRunRecommendation, FirstRunRecommendationService
from mcw_core.api.hardware.gpu_preference_manager import GraphicsDetectionResult
from mcw_core.api.instance.settings_manager import SettingsManager
from mcw_core.api.language.language_manager import language_manager, tr
from mcw_core.api.system.memory import MemoryAllocationPolicy
from src.gui.localization import retranslate_widget_tree
from src.gui.window_sizing import resize_dialog_to_screen


class FirstRunSetupDialog(QDialog):
    """First-run wizard for stable launcher defaults.

    The wizard intentionally stores Java and memory as *new-instance defaults*.
    Minecraft-version-specific Java selection remains the responsibility of the
    core resolver when the user leaves Java on Automatic.
    """

    SETUP_VERSION = 2

    def __init__(self, settings: dict, gpu_detection: GraphicsDetectionResult, recommendation: FirstRunRecommendation | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setObjectName("FirstRunSetupDialog")
        self._settings = settings if isinstance(settings, dict) else {}
        self._gpu_detection = gpu_detection
        self._recommendation = recommendation or FirstRunRecommendationService.fallback()
        self._page_index = 0
        self._build_ui()
        resize_dialog_to_screen(self, 760, 600, 640, 500)
        self._load_values()
        self._update_page()
        retranslate_widget_tree(self)
        self.retranslate_dynamic()

    @staticmethod
    def should_show(settings: dict) -> bool:
        onboarding = settings.get("onboarding", {}) if isinstance(settings, dict) else {}
        return not bool(onboarding.get("completed", False))

    def selected_settings(self) -> dict:
        defaults = SettingsManager.normalize_dict(self._settings.get("instance_defaults"))
        java = defaults.setdefault("java", {})
        selected_java = str(self.java_combo.currentData() or "")
        java["path"] = selected_java
        maximum = int(self.memory_spin.value())
        minimum = min(1024, maximum)
        java["min_memory"] = minimum
        java["max_memory"] = maximum
        return {
            "gui": {"language": str(self.language_combo.currentData() or "en-US")},
            "updates": {"auto_check": self.auto_check_updates.isChecked(), "channel": "stable"},
            "launch": {
                "prefer_dedicated_gpu": self.prefer_dedicated_gpu.isEnabled() and self.prefer_dedicated_gpu.isChecked(),
            },
            "network": {
                "download_concurrency": int(self.download_concurrency.currentData() or 0),
            },
            "instance_defaults": defaults,
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
        self.pages.addWidget(self._build_java_page())
        self.pages.addWidget(self._build_memory_page())
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

    def _base_page(self) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        return page, layout

    def _build_welcome_page(self) -> QWidget:
        page, layout = self._base_page()
        self.welcome_heading = QLabel()
        self.welcome_heading.setObjectName("SectionTitle")
        self.welcome_detail = QLabel()
        self.welcome_detail.setWordWrap(True)
        self.language_label = QLabel()
        self.language_combo = QComboBox()
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        self.language_restart_hint = QLabel()
        self.language_restart_hint.setObjectName("MutedLabel")
        self.language_restart_hint.setWordWrap(True)
        self.auto_check_updates = QCheckBox()
        self.download_concurrency_label = QLabel()
        self.download_concurrency = QComboBox()
        layout.addWidget(self.welcome_heading)
        layout.addWidget(self.welcome_detail)
        layout.addSpacing(8)
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_combo)
        layout.addWidget(self.language_restart_hint)
        layout.addWidget(self.auto_check_updates)
        layout.addWidget(self.download_concurrency_label)
        layout.addWidget(self.download_concurrency)
        layout.addStretch(1)
        return page

    def _build_java_page(self) -> QWidget:
        page, layout = self._base_page()
        self.java_heading = QLabel()
        self.java_heading.setObjectName("SectionTitle")
        self.java_detail = QLabel()
        self.java_detail.setWordWrap(True)
        self.java_combo = QComboBox()
        self.java_status = QLabel()
        self.java_status.setObjectName("MutedLabel")
        self.java_status.setWordWrap(True)
        self.java_rescan_button = QPushButton()
        self.java_rescan_button.clicked.connect(self._rescan_java)
        layout.addWidget(self.java_heading)
        layout.addWidget(self.java_detail)
        layout.addWidget(self.java_combo)
        layout.addWidget(self.java_status)
        layout.addWidget(self.java_rescan_button)
        layout.addStretch(1)
        return page

    def _build_memory_page(self) -> QWidget:
        page, layout = self._base_page()
        self.memory_heading = QLabel()
        self.memory_heading.setObjectName("SectionTitle")
        self.memory_detail = QLabel()
        self.memory_detail.setWordWrap(True)
        self.memory_status = QLabel()
        self.memory_status.setObjectName("MutedLabel")
        self.memory_status.setWordWrap(True)
        self.memory_spin = QSpinBox()
        self.memory_spin.setSingleStep(256)
        self.memory_spin.setSuffix(" MB")
        self.memory_recommend_button = QPushButton()
        self.memory_recommend_button.clicked.connect(lambda: self.memory_spin.setValue(self._recommendation.recommended_max_memory_mb))
        layout.addWidget(self.memory_heading)
        layout.addWidget(self.memory_detail)
        layout.addWidget(self.memory_status)
        layout.addWidget(self.memory_spin)
        layout.addWidget(self.memory_recommend_button)
        layout.addStretch(1)
        return page

    def _build_graphics_page(self) -> QWidget:
        page, layout = self._base_page()
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
        layout.addWidget(self.prefer_dedicated_gpu)
        layout.addWidget(self.gpu_status)
        layout.addWidget(self.gpu_notice)
        layout.addStretch(1)
        return page

    def _build_finish_page(self) -> QWidget:
        page, layout = self._base_page()
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
        network = self._settings.get("network", {}) if isinstance(self._settings.get("network"), dict) else {}

        current_locale = str(gui.get("language") or "en-US")
        language_manager.reload()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        for language in language_manager.available_languages():
            self.language_combo.addItem(language.name, language.locale)
        self.language_combo.setCurrentIndex(max(0, self.language_combo.findData(current_locale)))
        self.language_combo.blockSignals(False)
        self.auto_check_updates.setChecked(bool(updates.get("auto_check", True)))

        self._populate_download_concurrency(int(network.get("download_concurrency", 0) or 0))

        self._populate_java_combo()
        total = max(2048, self._recommendation.total_memory_mb or 4096)
        self.memory_spin.setRange(1024, total)
        self.memory_spin.setValue(self._recommendation.recommended_max_memory_mb)

        has_dgpu = self._gpu_detection.supported and self._gpu_detection.has_dedicated_gpu
        self.prefer_dedicated_gpu.setEnabled(has_dgpu)
        self.prefer_dedicated_gpu.setChecked(bool(launch.get("prefer_dedicated_gpu", False)) and has_dgpu)


    def _populate_download_concurrency(self, selected: int | None = None) -> None:
        current = int(self.download_concurrency.currentData() or 0) if selected is None else int(selected)
        self.download_concurrency.blockSignals(True)
        self.download_concurrency.clear()
        self.download_concurrency.addItem(tr("network.concurrency.auto"), 0)
        for count in (2, 4, 6, 8, 12, 16):
            self.download_concurrency.addItem(tr("network.concurrency.value", count=count), count)
        self.download_concurrency.setCurrentIndex(max(0, self.download_concurrency.findData(current)))
        self.download_concurrency.blockSignals(False)

    def _populate_java_combo(self) -> None:
        current = str(self.java_combo.currentData() or "")
        self.java_combo.blockSignals(True)
        self.java_combo.clear()
        self.java_combo.addItem(tr("first_run.java.auto"), "")
        for java in self._recommendation.java_installations:
            self.java_combo.addItem(f"Java {java.major} · {java.executable}", str(java.executable))
        preferred = self._recommendation.recommended_java_path
        self.java_combo.setCurrentIndex(max(0, self.java_combo.findData(current or preferred)))
        self.java_combo.blockSignals(False)
        self._update_java_status()

    def _rescan_java(self) -> None:
        self.java_rescan_button.setEnabled(False)
        try:
            self._recommendation = FirstRunRecommendationService.inspect()
            self._populate_java_combo()
        finally:
            self.java_rescan_button.setEnabled(True)

    def _update_java_status(self) -> None:
        if self._recommendation.java_installations:
            majors = ", ".join(str(value) for value in self._recommendation.java_majors)
            self.java_status.setText(tr("first_run.java.detected", count=len(self._recommendation.java_installations), majors=majors))
        else:
            self.java_status.setText(tr("first_run.java.none"))

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
            java_value = self.java_combo.currentText()
            gpu_value = tr("common.enabled") if self.prefer_dedicated_gpu.isChecked() else tr("common.disabled")
            updates_value = tr("common.enabled") if self.auto_check_updates.isChecked() else tr("common.disabled")
            self.finish_summary.setText(tr(
                "first_run.summary.extended",
                language=self.language_combo.currentText(),
                java=java_value,
                memory=MemoryAllocationPolicy.format_mb(self.memory_spin.value()),
                gpu=gpu_value,
                updates=updates_value,
            ))

    def _language_changed(self, _index: int) -> None:
        # The selected locale is persisted when the wizard finishes. Applying it
        # to the running process caused a partially translated launcher, so the
        # whole application now changes language only after a clean restart.
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
        super().reject()

    def _skip(self) -> None:
        self.prefer_dedicated_gpu.setChecked(False)
        self.java_combo.setCurrentIndex(0)
        self.accept()

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("first_run.title"))
        self.title_label.setText(tr("first_run.title"))
        self.skip_button.setText(tr("first_run.skip"))
        self.back_button.setText(tr("first_run.back"))
        self.welcome_heading.setText(tr("first_run.welcome.title"))
        self.welcome_detail.setText(tr("first_run.welcome.detail.extended"))
        self.language_label.setText(tr("first_run.language.label"))
        self.language_restart_hint.setText(tr("first_run.language.restart_hint"))
        self.auto_check_updates.setText(tr("first_run.updates.toggle"))
        self.download_concurrency_label.setText(tr("network.concurrency.label"))
        self._populate_download_concurrency()
        self._populate_java_combo()
        self.java_heading.setText(tr("first_run.java.title"))
        self.java_detail.setText(tr("first_run.java.detail"))
        self.java_rescan_button.setText(tr("first_run.java.rescan"))
        self._update_java_status()
        self.memory_heading.setText(tr("first_run.memory.title"))
        self.memory_detail.setText(tr("first_run.memory.detail"))
        self.memory_status.setText(tr(
            "first_run.memory.status",
            total=MemoryAllocationPolicy.format_mb(self._recommendation.total_memory_mb),
            available=MemoryAllocationPolicy.format_mb(self._recommendation.available_memory_mb),
            recommended=MemoryAllocationPolicy.format_mb(self._recommendation.recommended_max_memory_mb),
        ))
        self.memory_recommend_button.setText(tr("first_run.memory.use_recommended"))
        self.graphics_heading.setText(tr("first_run.graphics.title"))
        self.graphics_detail.setText(tr("first_run.graphics.detail"))
        self.prefer_dedicated_gpu.setText(tr("gpu.preference.toggle"))
        self.gpu_notice.setText(tr("gpu.preference.notice"))
        self.finish_heading.setText(tr("first_run.finish.title"))
        self.finish_detail.setText(tr("first_run.finish.detail"))
        self._update_gpu_text()
        self._update_page()
