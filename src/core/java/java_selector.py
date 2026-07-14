from pathlib import Path

from src.core.java.java_major_policy import JavaMajorPolicy
from src.core.java.java_manager import JavaManager
from src.core.java.java_provisioner import JavaProvisioner
from src.core.progress.progress_reporter import ProgressReporter


class JavaSelector:
    @staticmethod
    def select_java(required_major: int, allow_higher: bool = True, reporter: ProgressReporter | None = None, auto_install: bool = True) -> Path:
        managed_major = JavaMajorPolicy.resolve(required_major)
        exact_matches = [java for java in JavaManager.find_installation() if java.version == managed_major]
        if exact_matches:
            return exact_matches[0].executable

        if auto_install:
            return JavaProvisioner.ensure(managed_major, reporter)

        if allow_higher:
            supported_higher = [java for java in JavaManager.find_installation() if java.version in JavaMajorPolicy.SUPPORTED_MAJORS and java.version > managed_major]
            if supported_higher:
                return min(supported_higher, key=lambda java: java.version).executable

        raise RuntimeError(f"Java {managed_major} was not found.")

    @staticmethod
    def select_latest_java() -> Path:
        javas = JavaManager.find_installation()
        if not javas:
            raise RuntimeError("No Java found.")
        return max(javas, key=lambda java: java.version).executable
