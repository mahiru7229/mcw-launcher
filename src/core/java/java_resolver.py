from pathlib import Path

from src.core.java.java_provisioner import JavaProvisioner
from src.core.java.java_selector import JavaSelector
from src.core.progress.progress_reporter import ProgressReporter


class JavaResolver:
    @staticmethod
    def resolve(required_major: int, reporter: ProgressReporter | None = None) -> Path:
        try:
            return JavaSelector.select_java(required_major)
        except RuntimeError:
            return JavaProvisioner.ensure(required_major, reporter)
