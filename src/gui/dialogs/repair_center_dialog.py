from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.language.language_manager import tr
from src.core.repair.repair_service import RepairService
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.repair.repair_models import RepairComponent, RepairMode, RepairPlan, RepairReport, RepairStatus


class RepairCenterDialog(QDialog):
    scan_requested = Signal(str, str)
    repair_requested = Signal(str, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._instance_name = ""
        self._report: RepairReport | None = None
        self._checks: dict[RepairComponent, QCheckBox] = {}
        resize_dialog_to_screen(self, 1040, 650, 760, 480)
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        self.summary_label = QLabel()
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.summary_label)

        self.table = QTableWidget(0, 5)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self.table, 1)

        self.progress_label = QLabel()
        self.progress_label.setObjectName("MutedLabel")
        self.progress_label.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_label)
        root.addWidget(self.progress_bar)

        actions = QHBoxLayout()
        self.quick_button = QPushButton()
        self.full_button = QPushButton()
        self.repair_selected_button = QPushButton()
        self.repair_all_button = QPushButton()
        self.copy_report_button = QPushButton()
        self.close_button = QPushButton()
        self.quick_button.clicked.connect(lambda: self._request_scan(RepairMode.QUICK))
        self.full_button.clicked.connect(lambda: self._request_scan(RepairMode.FULL))
        self.repair_selected_button.clicked.connect(self._request_selected_repair)
        self.repair_all_button.clicked.connect(self._request_all_repair)
        self.copy_report_button.clicked.connect(self._copy_report)
        self.close_button.clicked.connect(self.accept)
        actions.addWidget(self.quick_button)
        actions.addWidget(self.full_button)
        actions.addWidget(self.repair_selected_button)
        actions.addWidget(self.repair_all_button)
        actions.addWidget(self.copy_report_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)
        self._set_actions_enabled(False)

    def set_instance(self, instance_name: str) -> None:
        self._instance_name = str(instance_name or "").strip()
        self._report = None
        self._checks.clear()
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_label.setText(tr("repair.center.ready"))
        self._update_summary()
        self._set_actions_enabled(bool(self._instance_name))

    def set_busy(self, busy: bool) -> None:
        self.quick_button.setEnabled(not busy and bool(self._instance_name))
        self.full_button.setEnabled(not busy and bool(self._instance_name))
        self.repair_selected_button.setEnabled(not busy and self._has_selected_issues())
        self.repair_all_button.setEnabled(not busy and self._has_repairable_issues())
        self.copy_report_button.setEnabled(not busy and self._report is not None)
        self.close_button.setEnabled(not busy)
        if busy:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)

    def set_progress(self, event: object) -> None:
        self.progress_label.setText(str(getattr(event, "message", tr("repair.center.working"))))
        current = getattr(event, "current", None)
        total = getattr(event, "total", None)
        if isinstance(current, int) and isinstance(total, int) and total > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(max(0, min(100, round(current * 100 / total))))
        else:
            self.progress_bar.setRange(0, 0)

    def set_report(self, report: RepairReport) -> None:
        self._report = report
        self._render_report()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        issue_count = len(report.issues)
        self.progress_label.setText(tr("repair.center.scan_complete", checked=report.checked_files, issues=issue_count, cache=report.cache_hits))
        self._update_summary()
        self.set_busy(False)

    def set_repair_result(self, result: object) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        repaired = len(tuple(getattr(result, "repaired_components", ()) or ()))
        failed = len(tuple(getattr(result, "failed_components", ()) or ()))
        if failed:
            self.progress_label.setText(tr("repair.center.repair_partial", repaired=repaired, failed=failed))
        else:
            self.progress_label.setText(tr("repair.center.repair_complete", repaired=repaired))
        self.set_busy(False)

    def set_error(self, error: Exception | str) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label.setText(tr("repair.center.failed", error=error))
        self.set_busy(False)
        QMessageBox.warning(self, tr("repair.center.title"), str(error))

    def _render_report(self) -> None:
        report = self._report
        if report is None:
            return
        self._checks.clear()
        self.table.setRowCount(len(report.components))
        for row, component_result in enumerate(report.components):
            checkbox = QCheckBox()
            checkbox.setChecked(bool(component_result.issues))
            checkbox.setEnabled(bool(component_result.issues))
            checkbox.stateChanged.connect(lambda _state: self._update_action_buttons())
            holder = QWidget()
            layout = QHBoxLayout(holder)
            layout.setContentsMargins(8, 0, 8, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(checkbox)
            self.table.setCellWidget(row, 0, holder)
            self._checks[component_result.component] = checkbox

            status_text = tr(f"repair.status.{component_result.status.value}")
            issue_text = str(len(component_result.issues))
            values = [
                tr(f"repair.component.{component_result.component.value}"),
                status_text,
                component_result.detail,
                issue_text,
            ]
            for column, value in enumerate(values, start=1):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, component_result.component.value)
                if column == 3:
                    issue_details = "\n".join(f"- {issue.message}" for issue in component_result.issues)
                    item.setToolTip(issue_details or component_result.detail)
                self.table.setItem(row, column, item)
        self._update_action_buttons()

    def _request_scan(self, mode: RepairMode) -> None:
        if not self._instance_name:
            return
        self.set_busy(True)
        self.progress_label.setText(tr("repair.center.scan_starting"))
        self.scan_requested.emit(self._instance_name, mode.value)

    def _request_selected_repair(self) -> None:
        report = self._report
        if report is None:
            return
        selected = tuple(component for component, checkbox in self._checks.items() if checkbox.isChecked())
        self._emit_repair(RepairService.build_plan(report, selected))

    def _request_all_repair(self) -> None:
        report = self._report
        if report is None:
            return
        selected = tuple(component.component for component in report.components if component.issues)
        self._emit_repair(RepairService.build_plan(report, selected))

    def _emit_repair(self, plan: RepairPlan) -> None:
        if not plan.can_repair:
            QMessageBox.information(self, tr("repair.center.title"), tr("repair.center.no_repairable"))
            return
        if plan.requires_manual_action:
            note = "\n\n" + tr("repair.center.manual_note")
        else:
            note = ""
        size_mb = plan.estimated_download_bytes / (1024 * 1024)
        message = tr("repair.center.confirm", issues=len(plan.repairable_issues), size=f"{size_mb:.1f} MB") + note
        answer = QMessageBox.question(self, tr("repair.center.title"), message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.set_busy(True)
        self.progress_label.setText(tr("repair.center.repair_starting"))
        self.repair_requested.emit(self._instance_name, plan)

    def _copy_report(self) -> None:
        if self._report is None:
            return
        lines = [
            f"Instance: {self._report.instance_name}",
            f"Mode: {self._report.mode.value}",
            f"Checked files: {self._report.checked_files}",
            f"Cache hits: {self._report.cache_hits}",
            f"Hashed files: {self._report.hashed_files}",
            "",
        ]
        for component in self._report.components:
            lines.append(f"[{component.component.value}] {component.status.value}: {component.detail}")
            lines.extend(f"- {issue.code}: {issue.message}" for issue in component.issues)
        QGuiApplication.clipboard().setText("\n".join(lines))
        self.progress_label.setText(tr("repair.center.report_copied"))

    def _has_selected_issues(self) -> bool:
        return any(checkbox.isChecked() and checkbox.isEnabled() for checkbox in self._checks.values())

    def _has_repairable_issues(self) -> bool:
        return bool(self._report and any(issue.repairable for issue in self._report.issues))

    def _update_action_buttons(self) -> None:
        self.repair_selected_button.setEnabled(self._has_selected_issues())
        self.repair_all_button.setEnabled(self._has_repairable_issues())
        self.copy_report_button.setEnabled(self._report is not None)

    def _set_actions_enabled(self, enabled: bool) -> None:
        self.quick_button.setEnabled(enabled)
        self.full_button.setEnabled(enabled)
        self.repair_selected_button.setEnabled(False)
        self.repair_all_button.setEnabled(False)
        self.copy_report_button.setEnabled(False)
        self.close_button.setEnabled(True)

    def _update_summary(self) -> None:
        if not self._instance_name:
            self.summary_label.setText(tr("repair.center.no_instance"))
        elif self._report is None:
            self.summary_label.setText(tr("repair.center.summary", instance=self._instance_name))
        else:
            self.summary_label.setText(tr("repair.center.summary_result", instance=self._instance_name, mode=self._report.mode.value, issues=len(self._report.issues)))

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("repair.center.title"))
        self.title_label.setText(tr("repair.center.title"))
        self.table.setHorizontalHeaderLabels([
            tr("repair.center.column.select"),
            tr("repair.center.column.component"),
            tr("repair.center.column.status"),
            tr("repair.center.column.details"),
            tr("repair.center.column.issues"),
        ])
        self.quick_button.setText(tr("repair.center.quick"))
        self.full_button.setText(tr("repair.center.full"))
        self.repair_selected_button.setText(tr("repair.center.repair_selected"))
        self.repair_all_button.setText(tr("repair.center.repair_all"))
        self.copy_report_button.setText(tr("repair.center.copy_report"))
        self.close_button.setText(tr("common.close"))
        self._update_summary()
        if self._report is not None:
            self._render_report()
