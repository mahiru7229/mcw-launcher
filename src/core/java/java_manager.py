from src.models.java.java import JavaInstallation
from pathlib import Path
import subprocess
import re
import os



class JavaManager:

    @staticmethod
    def find_installation() -> list[JavaInstallation]:
        javas: list[JavaInstallation] = []

        # javas.extend(JavaManager._scan_java_home())
        javas.extend(JavaManager._scan_path())

        return JavaManager._remove_duplicates(javas)
    
    @staticmethod
    def _get_java_in_java_home() -> Path:
        return None
    @staticmethod
    def _get_java_in_path() -> Path:
        try:
            result = subprocess.run(["where", "java"], capture_output=True, text=True, check=True, timeout=8,)

        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

        paths = result.stdout.splitlines()

        if not paths:
            return None

        return Path(paths[0].strip())

    @staticmethod
    def _get_version(java_path: Path) -> int | None:
        try:
            info = subprocess.run(
                [str(java_path), "-version"],
                capture_output=True,
                text=True,
                check=True
            )

            version_text = info.stderr.splitlines()[0]
            match = re.search(r'"(\d+)(?:\.\d+)*"', version_text)

            if match:
                return int(match.group(1))

            return None

        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    @staticmethod
    def _remove_duplicates(javas: list[JavaInstallation]) -> list[JavaInstallation]:


        unique: dict[Path, JavaInstallation] = {}

        for java in javas:
            unique[java.executable.resolve()] = java

        return list(unique.values())
    @staticmethod
    def _scan_path() -> list[JavaInstallation]:
        java_path = JavaManager._get_java_in_path()
        if not java_path:
            return []

        java_path_version = JavaManager._get_version(java_path)
        if not java_path_version:
            return []

        return [JavaInstallation(
            version=java_path_version,
            executable = Path(java_path),
            source="PATH"
        )]



    @staticmethod
    def _scan_java_home() -> list[JavaInstallation]:
        java_path = JavaManager._get_java_in_java_home()
        if not java_path:
            return []

        java_path_version = JavaManager._get_version(java_path)
        if not java_path_version:
            return []

        return [JavaInstallation(
            version=java_path_version,
            executable = Path(java_path),
            source="JAVA_HOME"
        )]
