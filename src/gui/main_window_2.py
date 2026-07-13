import sys
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from widget.launch_control_widget import LaunchControlWidget
from widget.seperator import Separator
VERSION = "v0.4.0 Beta 3"
LAUNCHER_NAME = f"MCW LAUNCHER {VERSION}"

class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(LAUNCHER_NAME)
        self.resize(1600, 900)

        self._build_ui()

    def _build_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        
        self.sidebar_widget = QWidget()
        self.center_widget = QWidget()
        self.content_widget = QStackedWidget()
        self.launch_control_widget = LaunchControlWidget()
        self.right_widget = QWidget()

        self.sidebar_widget.setStyleSheet("background: #2b2b2b;")
        self.content_widget.setStyleSheet("background: #3b3b3b;")
        self.right_widget.setStyleSheet("background: #4b4b4b;")
        self.launch_control_widget.setStyleSheet("background: #5b5b5b;")

        self.sidebar_widget.setFixedWidth(220)
        self.right_widget.setFixedWidth(400)
        

        #========CENTER WIDGET =======
        self.center_layout = QVBoxLayout(self.center_widget)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)
        self.center_layout.addWidget(self.content_widget, 1)
        self.center_layout.addWidget(self.launch_control_widget)
        #========CENTER WIDGET =======



        #========SIDEBAR WIDGET=========
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.home_button = QPushButton(text= "Home")
        self.account_button = QPushButton(text= "Account")
        self.instances_button = QPushButton(text= "Instances")
        self.instance_settings_button = QPushButton(text= "Instance Settings")
        self.launcher_settings_button = QPushButton(text= "Launcher Settings")
        self.launcher_logs_button = QPushButton(text= "Logs")
        self.launcher_about_button = QPushButton(text= "About")
        self.launcher_info_label = QLabel(text=f"{LAUNCHER_NAME}\nDev by mahiru7229.")
        

        self.sidebar_layout.setSpacing(12)
        self.sidebar_layout.setContentsMargins(12,24,12,24)
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
                font-size: 22px;
                font-weight: bold;
                color: green;
            }
            """)
        

        self.home_button.clicked.connect(self._on_home_clicked)



        
        self.sidebar_layout.addWidget(self.home_button)
        self.sidebar_layout.addWidget(self.account_button)
        self.sidebar_layout.addWidget(Separator("red",thickness=10)) #LINE
        self.sidebar_layout.addWidget(self.instances_button)
        self.sidebar_layout.addWidget(self.instance_settings_button)
        self.sidebar_layout.addWidget(Separator("red",thickness=10)) #LINE
        self.sidebar_layout.addWidget(self.launcher_settings_button)
        self.sidebar_layout.addWidget(self.launcher_logs_button)
        self.sidebar_layout.addWidget(Separator("red",thickness=10)) #LINE
        self.sidebar_layout.addWidget(self.launcher_about_button)
        self.sidebar_layout.addStretch()
        self.sidebar_layout.addWidget(self.launcher_info_label)
        #========SIDEBAR WIDGET=========


        #========CONTENT WIDGET=========
        self.content_layout = QVBoxLayout(self.content_widget)

        self.logo_label = QLabel()
        pixmap = QPixmap("assets/images/logo/main_launcher_logo.png")
        pixmap = pixmap.scaled(300,300,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.logo_label.setPixmap(pixmap)
        self.version_info_label = QLabel(text=f"Version: {VERSION}")
        self.version_info_label.setStyleSheet("""
            QLabel{
                font-size: 22px;
                font-weight:bold;                                  
            }
        """)

        self.content_layout.addWidget(self.logo_label,alignment=Qt.AlignCenter)
        self.content_layout.addWidget(self.version_info_label,alignment=Qt.AlignCenter)
        self.content_layout.addStretch()
        #LAUNCHER CONTROL WIDGET
        
        self.launch_control_widget.launch_clicked.connect(self._on_launch_clicked)
        self.center_layout.addWidget(self.content_widget, 1)
        self.center_layout.addWidget(self.launch_control_widget)
        #LAUNCHER CONTROL WIDGET

        #========LAUNCHER WIDGET=========


        #======== MAIN LAYOUT ===========
        main_layout.addWidget(self.sidebar_widget)
        main_layout.addWidget(self.center_widget, 1)
        main_layout.addWidget(self.right_widget)


    def _on_home_clicked(self) -> None:
        print("HOME CLICKED")

    def _on_launch_clicked(self) -> None:
        print("LAUNCH CLICKED")

        self.launch_control_widget.set_busy(True)
        self.launch_control_widget.set_status("Preparing Minecraft...")
        self.launch_control_widget.set_indeterminate(True)

def run() -> None:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()