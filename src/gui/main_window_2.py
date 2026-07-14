import sys
from src.gui.widget.info_row import InfoRow
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *
from src.core.fs.paths import Paths
from src.gui.widget.launch_control_widget import LaunchControlWidget
from src.gui.widget.seperator import Separator
from src.gui.widget.instance_info_widget import InstanceInfoWidget

# ==========================================================
# Application Information
# ==========================================================

VERSION = "v0.4.0 Beta 3"
LAUNCHER_NAME = f"MCW LAUNCHER {VERSION}"
DEFAULT_THEME_NAME = "Default Theme"

# ==========================================================
# Main Window
# ==========================================================

class MainWindow(QMainWindow):

    def __init__(self, theme_name:str = DEFAULT_THEME_NAME) -> None:

        super().__init__()
        self.THEME_NAME = theme_name
        self.setWindowTitle(LAUNCHER_NAME)
        self.resize(1600, 900)

        self._build_ui()

    def _build_ui(self) -> None:

        # ==================================================
        # Central Widget & Main Layout
        # ==================================================

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # ==================================================
        # Main Widgets
        # ==================================================

        self.sidebar_widget = QWidget()
        self.center_widget = QWidget()
        self.content_widget = QStackedWidget()
        self.launch_control_widget = LaunchControlWidget(self.THEME_NAME)
        self.right_widget = InstanceInfoWidget()


        # ==================================================
        # Widget Style
        # ==================================================

        self.sidebar_widget.setStyleSheet("background: #2b2b2b;")
        self.content_widget.setStyleSheet("background: #3b3b3b;")
        self.launch_control_widget.setStyleSheet("background: #5b5b5b;")

        self.sidebar_widget.setFixedWidth(220)

        # ==================================================
        # Center Layout
        # ==================================================

        self.center_layout = QVBoxLayout(self.center_widget)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)

        # ==================================================
        # Sidebar
        # ==================================================

        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)

        self.home_button = QPushButton("Home")
        self.account_button = QPushButton("Account")
        self.instances_button = QPushButton("Instances")
        self.instance_settings_button = QPushButton("Instance Settings")
        self.launcher_settings_button = QPushButton("Launcher Settings")
        self.launcher_logs_button = QPushButton("Logs")
        self.launcher_about_button = QPushButton("About")

        self.launcher_info_label = QLabel(
            f"{LAUNCHER_NAME}\nDev by mahiru7229."
        )

        self.sidebar_layout.setSpacing(12)
        self.sidebar_layout.setContentsMargins(12, 24, 12, 24)

        for button in (
            self.home_button,
            self.account_button,
            self.instances_button,
            self.instance_settings_button,
            self.launcher_settings_button,
            self.launcher_logs_button,
            self.launcher_about_button,
        ):
            button.setFixedHeight(48)
            button.setStyleSheet("""
                QPushButton {
                    font-size: 22px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    color: green;
                }
            """)

        # ==================================================
        # Sidebar Signals
        # ==================================================

        self.home_button.clicked.connect(self._on_home_clicked)

        # ==================================================
        # Sidebar Layout
        # ==================================================

        self.sidebar_layout.addWidget(self.home_button)
        self.sidebar_layout.addWidget(self.account_button)

        self.sidebar_layout.addWidget(
            Separator("red", thickness=10)
        )

        self.sidebar_layout.addWidget(self.instances_button)
        self.sidebar_layout.addWidget(self.instance_settings_button)

        self.sidebar_layout.addWidget(
            Separator("red", thickness=10)
        )

        self.sidebar_layout.addWidget(self.launcher_settings_button)
        self.sidebar_layout.addWidget(self.launcher_logs_button)

        self.sidebar_layout.addWidget(
            Separator("red", thickness=10)
        )

        self.sidebar_layout.addWidget(self.launcher_about_button)

        self.sidebar_layout.addStretch()

        self.sidebar_layout.addWidget(self.launcher_info_label)

        # ==================================================
        # Home Page
        # ==================================================

        self.home_page = QWidget()
        self.home_page_layout = QVBoxLayout(self.home_page)

        self.logo_label = QLabel()

        pixmap = QPixmap(str(Paths.theme_asset(self.THEME_NAME,"images","logo", "main_launcher_logo.png")))

        if pixmap.isNull():
            self.logo_label.setText("Logo not found")
        else:
            pixmap = pixmap.scaled(
                300,
                300,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.logo_label.setPixmap(pixmap)

        self.logo_label.setAlignment(Qt.AlignCenter)

        self.version_info_label = QLabel(
            f"Version: {VERSION}"
        )

        self.version_info_label.setAlignment(Qt.AlignCenter)

        self.version_info_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
            }
        """)

        self.home_page_layout.addWidget(self.logo_label)
        self.home_page_layout.addWidget(self.version_info_label)
        self.home_page_layout.addStretch()

        self.content_widget.addWidget(self.home_page)
        self.content_widget.setCurrentWidget(self.home_page)

        # ==================================================
        # Launch Control
        # ==================================================

        self.launch_control_widget.launch_clicked.connect(
            self._on_launch_clicked
        )

        # ==================================================
        # Center Layout
        # ==================================================

        self.center_layout.addWidget(self.content_widget, 1)
        self.center_layout.addWidget(self.launch_control_widget)

        # ==================================================
        # Right Layout 
        # ==================================================
        self.right_widget.set_instance_info("My Survival", "1.21.1", "Fabric")
        self.right_widget.set_java_info(21, "jdk-21")
        self.right_widget.set_memory_info(1024, 4096)
        self.right_widget.set_display_info(1280, 720, False)
        self.right_widget.set_account_info("mahiru7229", "Offline")
        # ==================================================
        # Main Layout
        # ==================================================

        main_layout.addWidget(self.sidebar_widget)
        main_layout.addWidget(self.center_widget, 1)
        main_layout.addWidget(self.right_widget)
    # ======================================================
    # Events
    # ======================================================

    def _on_home_clicked(self) -> None:
        print("HOME CLICKED")

    def _on_launch_clicked(self) -> None:
        print("LAUNCH CLICKED")

        self.launch_control_widget.set_busy(True)
        self.launch_control_widget.set_status("Preparing Minecraft...")
        self.launch_control_widget.set_indeterminate(True)


# ==========================================================
# Application Entry
# ==========================================================

    def run() -> None:
        app = QApplication(sys.argv)

        window = MainWindow()
        window.show()

        sys.exit(app.exec())


if __name__ == "__main__":
    MainWindow.run()