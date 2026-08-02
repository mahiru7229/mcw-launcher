from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from mcw_core.api.language.language_manager import tr
from mcw_core.api.theme.theme_authoring import ThemeValidationReport


class ThemeIssuesDialog(QDialog):
    def __init__(self, report: ThemeValidationReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("theme.authoring.validation.title"))
        self.resize(760, 460)
        layout = QVBoxLayout(self)
        summary = QLabel(tr("theme.authoring.validation.summary", theme=report.name, errors=report.error_count, warnings=report.warning_count))
        summary.setWordWrap(True)
        layout.addWidget(summary)
        tree = QTreeWidget()
        tree.setHeaderLabels([tr("theme.authoring.validation.severity"), tr("theme.authoring.validation.category"), tr("theme.authoring.validation.message")])
        for issue in report.issues:
            item = QTreeWidgetItem([tr(f"theme.authoring.severity.{issue.severity}"), tr(f"theme.authoring.category.{issue.category}"), issue.message])
            item.setToolTip(2, issue.message)
            tree.addTopLevelItem(item)
        if not report.issues:
            tree.addTopLevelItem(QTreeWidgetItem([tr("theme.authoring.severity.info"), tr("theme.authoring.category.manifest"), tr("theme.authoring.validation.clean")]))
        tree.resizeColumnToContents(0)
        tree.resizeColumnToContents(1)
        layout.addWidget(tree)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
