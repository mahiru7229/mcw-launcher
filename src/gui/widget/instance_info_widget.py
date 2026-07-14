from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.gui.widget.info_row import InfoRow
from src.gui.widget.info_section import InfoSection


class InstanceInfoWidget(QWidget):

    def __init__(self) -> None:
        super().__init__()

        self.main_layout = QVBoxLayout(self)

        self._build_rows()
        self._build_sections()
        self._build_ui()

    def _build_rows(self) -> None:
        self.instance_name_row = InfoRow("Instance", "-")
        self.minecraft_version_row = InfoRow("Minecraft", "-")
        self.mod_loader_row = InfoRow("Mod Loader", "-")

        self.java_version_row = InfoRow("Version", "-")
        self.java_runtime_row = InfoRow("Runtime", "-")

        self.min_memory_row = InfoRow("Minimum", "-")
        self.max_memory_row = InfoRow("Maximum", "-")

        self.resolution_row = InfoRow("Resolution", "-")
        self.fullscreen_row = InfoRow("Fullscreen", "-")

        self.username_row = InfoRow("Username", "-")
        self.account_type_row = InfoRow("Type", "-")

    def _build_sections(self) -> None:
        self.instance_section = InfoSection("INSTANCE")
        self.java_section = InfoSection("JAVA")
        self.memory_section = InfoSection("MEMORY")
        self.display_section = InfoSection("DISPLAY")
        self.account_section = InfoSection("ACCOUNT")

        self.instance_section.add_row(self.instance_name_row)
        self.instance_section.add_row(self.minecraft_version_row)
        self.instance_section.add_row(self.mod_loader_row)

        self.java_section.add_row(self.java_version_row)
        self.java_section.add_row(self.java_runtime_row)

        self.memory_section.add_row(self.min_memory_row)
        self.memory_section.add_row(self.max_memory_row)

        self.display_section.add_row(self.resolution_row)
        self.display_section.add_row(self.fullscreen_row)

        self.account_section.add_row(self.username_row)
        self.account_section.add_row(self.account_type_row)

    def _build_ui(self) -> None:
        self.main_layout.setContentsMargins(12, 16, 12, 16)
        self.main_layout.setSpacing(14)

        self.main_layout.addWidget(self.instance_section)
        self.main_layout.addWidget(self.java_section)
        self.main_layout.addWidget(self.memory_section)
        self.main_layout.addWidget(self.display_section)
        self.main_layout.addWidget(self.account_section)
        self.main_layout.addStretch()

    def set_instance_info(self, instance_name: str, minecraft_version: str, mod_loader: str) -> None:
        self.instance_name_row.set_value(instance_name)
        self.minecraft_version_row.set_value(minecraft_version)
        self.mod_loader_row.set_value(mod_loader)

    def set_java_info(self, java_version: int | str, java_runtime: str) -> None:
        self.java_version_row.set_value(str(java_version))
        self.java_runtime_row.set_value(java_runtime)

    def set_memory_info(self, min_memory: int, max_memory: int) -> None:
        self.min_memory_row.set_value(f"{min_memory} MB")
        self.max_memory_row.set_value(f"{max_memory} MB")

    def set_display_info(self, width: int, height: int, fullscreen: bool) -> None:
        self.resolution_row.set_value(f"{width} x {height}")
        self.fullscreen_row.set_value("Yes" if fullscreen else "No")

    def set_account_info(self, username: str, account_type: str) -> None:
        self.username_row.set_value(username)
        self.account_type_row.set_value(account_type)

    def clear(self) -> None:
        self.set_instance_info("-", "-", "-")
        self.set_java_info("-", "-")
        self.min_memory_row.set_value("-")
        self.max_memory_row.set_value("-")
        self.resolution_row.set_value("-")
        self.fullscreen_row.set_value("-")
        self.set_account_info("-", "-")