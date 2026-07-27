from __future__ import annotations

from src.core.mod.mod_compatibility_manager import ModCompatibilityManager
from src.core.modloader.forge.forge_version_manager import ForgeVersionManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.models.instance.instance import Instance
from src.models.minecraft.version import Version
from src.models.mod.mod_issue import ModIssue
from src.models.modloader.forge_preflight_report import ForgePreflightReport


class ForgePreflightManager:
    @staticmethod
    def scan(instance: Instance, version: Version, verify_files: bool = False) -> ForgePreflightReport:
        loader_name, loader_version = ModLoaderManager.normalize(getattr(instance, "mod_loader", ("vanilla", "-1")))
        if loader_name != ModLoaderManager.FORGE:
            return ForgePreflightReport(issues=())

        issues: list[ModIssue] = []
        for message in ForgeVersionManager.validate_installation(
            version,
            instance.version_id,
            loader_version,
            verify_files=verify_files,
        ):
            issues.append(ModIssue(severity="error", code="forge-installation", message=message))

        mod_report = ModCompatibilityManager.scan(instance)
        issues.extend(mod_report.issues)
        issues.sort(
            key=lambda item: (
                {"error": 0, "warning": 1, "info": 2}.get(item.severity, 3),
                item.message.casefold(),
            )
        )
        return ForgePreflightReport(issues=tuple(issues))

    @staticmethod
    def validate_runtime_files(instance: Instance, version: Version) -> tuple[str, ...]:
        loader_name, loader_version = ModLoaderManager.normalize(getattr(instance, "mod_loader", ("vanilla", "-1")))
        if loader_name != ModLoaderManager.FORGE:
            return ()
        return tuple(
            ForgeVersionManager.validate_installation(
                version,
                instance.version_id,
                loader_version,
                verify_files=True,
            )
        )

    @staticmethod
    def raise_for_errors(report: ForgePreflightReport, block_compatibility_errors: bool = True) -> None:
        blocking_errors = tuple(
            issue
            for issue in report.errors
            if block_compatibility_errors or issue.code == "forge-installation"
        )
        if not blocking_errors:
            return
        details = "\n".join(f"- {issue.message}" for issue in blocking_errors)
        raise RuntimeError(
            "Forge pre-launch check failed:\n"
            f"{len(blocking_errors)} blocking error(s), {getattr(report, 'warning_count', len(getattr(report, 'warnings', ())))} warning(s)\n"
            f"{details}"
        )
