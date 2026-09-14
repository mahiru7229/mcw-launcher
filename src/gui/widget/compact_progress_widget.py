from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from mcw_core.api.language.language_manager import tr
from src.gui.presenters.progress_presenter import ProgressPresenter
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.themed_progress_bar import ThemedProgressBar
from src.models.progress.progress_state import ProgressState

if TYPE_CHECKING:
    from src.models.progress.progress_event import ProgressEvent


class CompactProgressWidget(QFrame):
    cancel_clicked = Signal()

    _DOWNLOAD_STAGES = {
        "downloading_mod_loader",
        "downloading_java",
        "downloading_client",
        "downloading_libraries",
        "downloading_asset_index",
        "downloading_assets",
        "downloading_mods",
        "downloading_content",
        "downloading_modpack",
        "downloading_update",
    }

    _INSTALL_STAGES = {
        "installing_mod_loader",
        "installing_java",
        "selecting_java",
        "checking_mods",
        "checking_modpack",
        "building_context",
        "building_command",
        "launching",
        "finished",
    }

    _STAGE_INSTALL_WEIGHTS = {
        "installing_mod_loader": 25,
        "installing_java": 35,
        "selecting_java": 40,
        "checking_mods": 50,
        "checking_modpack": 55,
        "building_context": 70,
        "building_command": 85,
        "launching": 95,
        "finished": 100,
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CompactProgressWidget")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._download_pct = 0
        self._install_pct = 0
        self._speed_str = "---"
        self._overall_pct = 0
        self._active = False

        self._build_ui()
        self._update_labels()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(6)

        metrics_layout = QHBoxLayout()
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(16)

        self.download_label = QLabel()
        self.download_label.setObjectName("ProgressMetricLabel")
        self.download_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.install_label = QLabel()
        self.install_label.setObjectName("ProgressMetricLabel")
        self.install_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.speed_label = QLabel()
        self.speed_label.setObjectName("ProgressMetricLabel")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        metrics_layout.addWidget(self.download_label)
        metrics_layout.addWidget(self.install_label)
        metrics_layout.addWidget(self.speed_label)
        metrics_layout.addStretch(1)

        self.cancel_button = set_theme_icon(QPushButton(tr("launch.cancel_button")), "icon.action.cancel", 14)
        self.cancel_button.setObjectName("SecondaryButton")
        self.cancel_button.setFixedHeight(24)
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        metrics_layout.addWidget(self.cancel_button)

        self.progress_bar = ThemedProgressBar(self)
        self.progress_bar.setObjectName("CompactProgressBar")
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")

        root_layout.addLayout(metrics_layout)
        root_layout.addWidget(self.progress_bar)

    def _update_labels(self) -> None:
        self.download_label.setText(f"📥 {tr('progress.download_percent', percent=self._download_pct)}")
        self.install_label.setText(f"⚙️ {tr('progress.install_percent', percent=self._install_pct)}")
        self.speed_label.setText(f"⚡ {tr('progress.network_speed', speed=self._speed_str)}")

    def retranslate_dynamic(self) -> None:
        self.cancel_button.setText(tr("launch.cancel_button"))
        self._update_labels()

    def set_progress_event(self, event: object) -> None:
        if event is None:
            return

        state = getattr(event, "state", ProgressState.RUNNING)
        if isinstance(state, ProgressState):
            state_val = state
        else:
            try:
                state_val = ProgressState(str(getattr(state, "value", state)))
            except ValueError:
                state_val = ProgressState.RUNNING

        if state_val is ProgressState.SUCCEEDED:
            self._download_pct = 100
            self._install_pct = 100
            self._overall_pct = 100
            self._speed_str = "---"
            self.progress_bar.setValue(100)
            self._update_labels()
            return

        if state_val in (ProgressState.FAILED, ProgressState.CANCELLED):
            self._speed_str = "---"
            self._update_labels()
            return

        stage = getattr(event, "stage", None)
        stage_str = str(getattr(stage, "value", stage or "")).strip().casefold()

        # Handle speed
        speed = getattr(event, "bytes_per_second", None)
        if speed is not None and float(speed) > 0:
            self._speed_str = ProgressPresenter._format_bytes(round(float(speed))) + "/s"
        elif stage_str in self._DOWNLOAD_STAGES:
            self._speed_str = "0 B/s"
        else:
            self._speed_str = "---"

        # Handle download vs install percentage
        raw_pct = getattr(event, "percentage", None)
        determinate_pct = round(float(raw_pct)) if raw_pct is not None else None

        if stage_str in self._DOWNLOAD_STAGES:
            if determinate_pct is not None:
                self._download_pct = max(0, min(100, determinate_pct))
            self._overall_pct = int(self._download_pct * 0.7)
        elif stage_str in self._INSTALL_STAGES:
            self._download_pct = 100
            if determinate_pct is not None:
                self._install_pct = max(0, min(100, determinate_pct))
            else:
                self._install_pct = self._STAGE_INSTALL_WEIGHTS.get(stage_str, 50)
            self._overall_pct = min(100, 70 + int(self._install_pct * 0.3))

        self.progress_bar.setValue(self._overall_pct)
        self._update_labels()

    def set_active(self, active: bool) -> None:
        self._active = bool(active)
        self.setVisible(self._active)
        if not self._active:
            self.reset()

    def reset(self) -> None:
        self._download_pct = 0
        self._install_pct = 0
        self._speed_str = "---"
        self._overall_pct = 0
        self.progress_bar.setValue(0)
        self._update_labels()
