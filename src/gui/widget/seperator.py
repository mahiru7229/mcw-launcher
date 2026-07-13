from PySide6.QtWidgets import *


class Separator(QFrame):
    def __init__(self, color:str = "#555555",thickness: int = 2) -> None:
        super().__init__()

        self.setFixedHeight(thickness)

        self.setStyleSheet(f"""
        QFrame {{
            background-color: {color};
            border: none;
        }}
        """)