from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from setupvault.core.profile import BUILTIN_PROFILES, load_all_custom_profiles
from setupvault.gui.pages import BasePage, Section
from setupvault.gui.widgets import (
    ComboField,
    FilePicker,
    LoadingIndicator,
    StatCard,
)
from setupvault.gui.worker import Worker


def _profiles() -> list[str]:
    names = list(BUILTIN_PROFILES)
    for profile in load_all_custom_profiles().values():
        if profile.name not in names:
            names.append(profile.name)
    return names


def _profile_desc(name: str) -> str:
    descs = {
        "full": "All sections: system, packages, themes, fonts, shell, environment, dotfiles",
        "minimal": "System info and packages only",
        "packages-only": "Package lists only",
    }
    return descs.get(name, "")


class _LogView(QPlainTextEdit):
    """Styled read-only log output with colored HTML entries."""

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(180)

    def log(self, message: str, status: str = "info") -> None:
        colors = {
            "info": "#6B7280",
            "success": "#10B981",
            "error": "#EF4444",
            "warning": "#F59E0B",
            "running": "#6366F1",
        }
        icons = {
            "info": "\u2139",
            "success": "\u2713",
            "error": "\u2717",
            "warning": "\u26a0",
            "running": "\u25cf",
        }
        icon = icons.get(status, "\u2139")
        color = colors.get(status, "#6B7280")
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = (
            f'<div style="display:flex;align-items:center;gap:8px;padding:2px 0;">'
            f'<span style="color:{color};font-size:13px;">{icon}</span>'
            f'<span style="color:{color};font-size:13px;">{message}</span>'
            f'<span style="color:#9CA3AF;font-size:11px;margin-left:auto;">{timestamp}</span>'
            f"</div>"
        )
        self.appendHtml(html)


class ExportPanel(BasePage):
    title = "Export"
    description = "Capture your Linux setup into a portable snapshot."

    def _build_body(self) -> None:
        card = Section("Export Options")
        self._profile = ComboField("Profile", _profiles(), "full")
        card.addWidget(self._profile)

        desc = QLabel(_profile_desc("full"))
        desc.setObjectName("CardDesc")
        desc.setWordWrap(True)
        card.addWidget(desc)

        self._compress = QCheckBox("Compress snapshot (.json.gz)")
        card.addWidget(self._compress)
        compress_desc = QLabel("Recommended to reduce snapshot size")
        compress_desc.setObjectName("CardDesc")
        compress_desc.setContentsMargins(28, 0, 0, 0)
        card.addWidget(compress_desc)

        self._out = FilePicker(
            mode="save",
            caption="Save snapshot as",
            filter="JSON (*.json);;Gzip JSON (*.json.gz)",
            placeholder="Default: auto-named in snapshots directory",
        )
        card.addWidget(self._out)

        self._run = QPushButton("Export Snapshot")
        self._run.setObjectName("Primary")
        self._run.clicked.connect(self._on_export)
        card.addWidget(self._run)
        self._body_layout.addWidget(card)

        self._loading = LoadingIndicator("Exporting")
        self._loading.setVisible(False)
        self._body_layout.addWidget(self._loading)

        self._log = _LogView()
        self._body_layout.addWidget(self._log)

        self._stats_widget = QWidget()
        self._stats_widget.setVisible(False)
        stats_layout = QGridLayout(self._stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)
        self._stat_size = StatCard("--", "Snapshot Size")
        self._stat_items = StatCard("--", "Items Collected")
        self._stat_duration = StatCard("--", "Duration")
        self._stat_path = StatCard("--", "Destination")
        stats_layout.addWidget(self._stat_size, 0, 0)
        stats_layout.addWidget(self._stat_items, 0, 1)
        stats_layout.addWidget(self._stat_duration, 1, 0)
        stats_layout.addWidget(self._stat_path, 1, 1)
        self._body_layout.addWidget(self._stats_widget)

        self._profile._combo.currentTextChanged.connect(self._on_profile_changed)

    def _on_profile_changed(self, name: str) -> None:
        desc_widgets = self.findChildren(QLabel, "CardDesc")
        for w in desc_widgets:
            text = _profile_desc(name)
            if text:
                w.setText(text)
            break

    def apply_settings(self, settings) -> None:  # type: ignore[no-untyped-def]
        settings_profile = getattr(settings, "default_profile", None)
        if settings_profile and settings_profile in _profiles():
            self._profile.set_value(settings_profile)

    def _on_export(self) -> None:
        from setupvault.services.export_service import ExportService

        self._run.setEnabled(False)
        self._loading.setVisible(True)
        self._log.clear()
        self._stats_widget.setVisible(False)
        self._log.log("Starting export", "running")
        out = self._out.path() or None
        self._worker = Worker(
            ExportService().execute,
            self._profile.value(),
            out,
            compress=self._compress.isChecked(),
        )
        self._worker.finished.connect(self._on_export_done)
        self._worker.errored.connect(lambda e: self._log.log(f"Error: {e}", "error"))
        self._worker.errored.connect(lambda _: self._run.setEnabled(True))
        self._worker.errored.connect(lambda _: self._loading.setVisible(False))
        self._worker.start()

    def _on_export_done(self, report) -> None:  # type: ignore[no-untyped-def]
        self._log.log("Snapshot exported successfully", "success")
        self._run.setEnabled(True)
        self._loading.setVisible(False)
        size = report.path.stat().st_size if report.path.exists() else 0
        self._stat_size.set_value(f"{size / 1024:.1f} KB")
        snap = report.snapshot
        total = snap.packages.counts.total if snap.packages else 0
        dotfiles = len(snap.dotfiles) if snap.dotfiles else 0
        self._stat_items.set_value(str(total + dotfiles))
        self._stat_duration.set_value(f"{report.duration_seconds:.1f}s")
        self._stat_path.set_value(str(report.path.name))
        self._stats_widget.setVisible(True)
        self._log.log(f"Saved to {report.path}", "info")


class _FilePanel(BasePage):
    caption = "Select snapshot"
    file_filter = "JSON (*.json);;Gzip JSON (*.json.gz);;All files (*)"

    def _build_file_row(self) -> FilePicker:
        self._picker = FilePicker(
            mode="open",
            caption=self.caption,
            filter=self.file_filter,
            placeholder="Path to snapshot file",
        )
        card = Section("Snapshot File")
        card.addWidget(self._picker)
        self._body_layout.addWidget(card)
        return self._picker

    def _path(self) -> str:
        return self._picker.path()


class InfoPanel(_FilePanel):
    title = "Info"
    description = "View a quick summary of a snapshot."

    def _build_body(self) -> None:
        self._build_file_row()
        card = Section("Summary")
        self._run = QPushButton("Show Info")
        self._run.setObjectName("Primary")
        self._run.clicked.connect(self._on_info)
        card.addWidget(self._run)
        self._body_layout.addWidget(card)
        self._out = QPlainTextEdit()
        self._out.setReadOnly(True)
        self._out.setMaximumHeight(250)
        self._body_layout.addWidget(self._out)

    def _on_info(self) -> None:
        from setupvault.storage.local import read_snapshot

        path = self._path()
        if not path:
            self._out.setPlainText("Please select a snapshot file.")
            return
        try:
            snap = read_snapshot(Path(path))
        except Exception as exc:  # noqa: BLE001
            self._out.setPlainText(f"Failed to read: {exc}")
            return
        lines = [
            f"Distribution: {snap.system.distribution.name} {snap.system.distribution.version}",
            f"Hostname:     {snap.system.hostname}",
            f"Tool version: {snap.tool_version}",
            f"Created:      {snap.created_at}",
            f"Packages:     {snap.packages.counts.total} "
            f"(official={snap.packages.counts.official}, "
            f"aur={snap.packages.counts.aur}, "
            f"third_party={snap.packages.counts.third_party})",
            f"Dotfiles:     {len(snap.dotfiles)}",
        ]
        self._out.setPlainText("\n".join(lines))


class ValidatePanel(_FilePanel):
    title = "Validate"
    description = "Check a snapshot for schema and semantic issues."

    def _build_body(self) -> None:
        self._build_file_row()
        card = Section("Validation")
        self._loading = LoadingIndicator("Validating")
        self._loading.setVisible(False)
        card.addWidget(self._loading)
        self._run = QPushButton("Validate")
        self._run.setObjectName("Primary")
        self._run.clicked.connect(self._on_validate)
        card.addWidget(self._run)
        self._body_layout.addWidget(card)
        self._out = QPlainTextEdit()
        self._out.setReadOnly(True)
        self._out.setMaximumHeight(250)
        self._body_layout.addWidget(self._out)

    def _on_validate(self) -> None:
        from setupvault.services.validate_service import validate_snapshot

        path = self._path()
        if not path:
            self._out.setPlainText("Please select a snapshot file.")
            return
        self._run.setEnabled(False)
        self._loading.setVisible(True)
        self._worker = Worker(validate_snapshot, Path(path))
        self._worker.finished.connect(
            lambda r: self._out.setPlainText(
                f"Valid: {r.valid}\n"
                + ("Errors:\n" + "\n".join(r.all_errors) if r.all_errors else "No errors.")
            )
        )
        self._worker.finished.connect(lambda _: self._run.setEnabled(True))
        self._worker.finished.connect(lambda _: self._loading.setVisible(False))
        self._worker.errored.connect(lambda e: self._out.setPlainText(f"Error: {e}"))
        self._worker.errored.connect(lambda _: self._run.setEnabled(True))
        self._worker.errored.connect(lambda _: self._loading.setVisible(False))
        self._worker.start()


class ReportPanel(_FilePanel):
    title = "Report"
    description = "Generate a human-readable report from a snapshot."

    def _build_body(self) -> None:
        self._build_file_row()
        card = Section("Report Options")
        self._fmt = ComboField("Format", ["markdown", "json", "html"], "markdown")
        card.addWidget(self._fmt)
        self._loading = LoadingIndicator("Generating report")
        self._loading.setVisible(False)
        card.addWidget(self._loading)
        self._run = QPushButton("Generate Report")
        self._run.setObjectName("Primary")
        self._run.clicked.connect(self._on_report)
        card.addWidget(self._run)
        self._view_html = QPushButton("View in Browser")
        self._view_html.setObjectName("Secondary")
        self._view_html.setVisible(False)
        self._view_html.clicked.connect(self._on_view_html)
        card.addWidget(self._view_html)
        self._body_layout.addWidget(card)
        self._out = QPlainTextEdit()
        self._out.setReadOnly(True)
        self._body_layout.addWidget(self._out)
        self._last_report = ""

    def apply_settings(self, settings) -> None:  # type: ignore[no-untyped-def]
        if settings.default_report_format in ("markdown", "json", "html"):
            self._fmt.set_value(settings.default_report_format)

    def _on_report(self) -> None:
        from setupvault.services.report_service import generate_report

        path = self._path()
        if not path:
            self._out.setPlainText("Please select a snapshot file.")
            return
        self._run.setEnabled(False)
        self._loading.setVisible(True)
        self._view_html.setVisible(False)
        self._worker = Worker(generate_report, Path(path), self._fmt.value())
        self._worker.finished.connect(self._on_report_done)
        self._worker.errored.connect(lambda e: self._out.setPlainText(f"Error: {e}"))
        self._worker.errored.connect(lambda _: self._run.setEnabled(True))
        self._worker.errored.connect(lambda _: self._loading.setVisible(False))
        self._worker.start()

    def _on_report_done(self, text: str) -> None:
        self._last_report = text
        self._out.setPlainText(text)
        self._run.setEnabled(True)
        self._loading.setVisible(False)
        self._view_html.setVisible(self._fmt.value() == "html")

    def _on_view_html(self) -> None:
        from setupvault.gui.widgets import HtmlViewer

        dlg = HtmlViewer(self._last_report, parent=self)
        dlg.exec()


class DoctorPanel(BasePage):
    title = "Doctor"
    description = "Run diagnostics to verify the environment is ready."

    def _build_body(self) -> None:
        card = Section("Diagnostics")
        self._loading = LoadingIndicator("Running diagnostics")
        self._loading.setVisible(False)
        card.addWidget(self._loading)
        self._run = QPushButton("Run Diagnostics")
        self._run.setObjectName("Primary")
        self._run.clicked.connect(self._on_doctor)
        card.addWidget(self._run)
        self._body_layout.addWidget(card)
        self._out = QPlainTextEdit()
        self._out.setReadOnly(True)
        self._out.setMaximumHeight(300)
        self._body_layout.addWidget(self._out)

    def _on_doctor(self) -> None:
        from setupvault.doctor.runner import run_doctor

        self._run.setEnabled(False)
        self._loading.setVisible(True)
        self._worker = Worker(run_doctor)
        self._worker.finished.connect(
            lambda r: self._out.setPlainText(
                f"All passed: {r.all_passed}\n"
                f"Passed: {len(r.passed)}\n"
                f"Failed: {len(r.failed)}\n"
                + ("\n".join(f"- {c}: {m}" for c, m in r.failed) if r.failed else "")
            )
        )
        self._worker.finished.connect(lambda _: self._run.setEnabled(True))
        self._worker.finished.connect(lambda _: self._loading.setVisible(False))
        self._worker.errored.connect(lambda e: self._out.setPlainText(f"Error: {e}"))
        self._worker.errored.connect(lambda _: self._run.setEnabled(True))
        self._worker.errored.connect(lambda _: self._loading.setVisible(False))
        self._worker.start()


class DiffPanel(BasePage):
    title = "Diff"
    description = "Compare two snapshots and list what changed."

    def _build_body(self) -> None:
        card = Section("Snapshots")
        self._left = FilePicker(
            mode="open",
            caption="Left snapshot",
            placeholder="Left snapshot file",
        )
        card.addWidget(self._left)
        self._right = FilePicker(
            mode="open",
            caption="Right snapshot",
            placeholder="Right snapshot file",
        )
        card.addWidget(self._right)
        self._loading = LoadingIndicator("Comparing")
        self._loading.setVisible(False)
        card.addWidget(self._loading)
        self._run = QPushButton("Compare")
        self._run.setObjectName("Primary")
        self._run.clicked.connect(self._on_diff)
        card.addWidget(self._run)
        self._body_layout.addWidget(card)
        self._out = QPlainTextEdit()
        self._out.setReadOnly(True)
        self._out.setMaximumHeight(300)
        self._body_layout.addWidget(self._out)

    def _on_diff(self) -> None:
        from setupvault.services.diff_service import diff_snapshots

        left, right = self._left.path(), self._right.path()
        if not left or not right:
            self._out.setPlainText("Please select both snapshots.")
            return
        self._run.setEnabled(False)
        self._loading.setVisible(True)
        self._worker = Worker(diff_snapshots, Path(left), Path(right))
        self._worker.finished.connect(
            lambda r: self._out.setPlainText(
                f"Same: {r.same}\nChanged sections: {', '.join(r.sections_changed) or 'none'}"
            )
        )
        self._worker.finished.connect(lambda _: self._run.setEnabled(True))
        self._worker.finished.connect(lambda _: self._loading.setVisible(False))
        self._worker.errored.connect(lambda e: self._out.setPlainText(f"Error: {e}"))
        self._worker.errored.connect(lambda _: self._run.setEnabled(True))
        self._worker.errored.connect(lambda _: self._loading.setVisible(False))
        self._worker.start()


class ListPanel(BasePage):
    title = "List"
    description = "Browse snapshots in the configured directory."

    def _build_body(self) -> None:
        card = Section("Available Snapshots")
        self._loading = LoadingIndicator("Loading")
        self._loading.setVisible(False)
        card.addWidget(self._loading)
        self._run = QPushButton("Refresh")
        self._run.setObjectName("Primary")
        self._run.clicked.connect(self._on_list)
        card.addWidget(self._run)
        self._body_layout.addWidget(card)
        self._list = QListWidget()
        self._body_layout.addWidget(self._list)

    def _on_list(self) -> None:
        from setupvault.services.list_service import list_snapshots

        self._run.setEnabled(False)
        self._loading.setVisible(True)
        self._list.clear()
        self._worker = Worker(list_snapshots)
        self._worker.finished.connect(self._populate)
        self._worker.finished.connect(lambda _: self._run.setEnabled(True))
        self._worker.finished.connect(lambda _: self._loading.setVisible(False))
        self._worker.errored.connect(lambda e: self._list.addItem(f"Error: {e}"))
        self._worker.errored.connect(lambda _: self._run.setEnabled(True))
        self._worker.errored.connect(lambda _: self._loading.setVisible(False))
        self._worker.start()

    def _populate(self, result) -> None:  # type: ignore[no-untyped-def]
        self._list.clear()
        if result.error:
            self._list.addItem(result.error)
            return
        for entry in result.snapshots:
            item = QListWidgetItem(f"{entry.filename}  ({entry.size_bytes} bytes)")
            item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
            self._list.addItem(item)


class RestorePanel(_FilePanel):
    title = "Restore"
    description = "Restore configuration from a snapshot (plan, then apply)."

    def _build_body(self) -> None:
        self._build_file_row()
        card = Section("Restore Options")
        self._dry = QCheckBox("Dry run (do not make changes)")
        card.addWidget(self._dry)
        self._loading = LoadingIndicator("Working")
        self._loading.setVisible(False)
        card.addWidget(self._loading)
        row = QHBoxLayout()
        self._plan_btn = QPushButton("Plan")
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setObjectName("Primary")
        row.addWidget(self._plan_btn)
        row.addWidget(self._apply_btn)
        card.addLayout(row)
        self._body_layout.addWidget(card)
        self._out = QPlainTextEdit()
        self._out.setReadOnly(True)
        self._out.setMaximumHeight(250)
        self._body_layout.addWidget(self._out)
        self._plan_btn.clicked.connect(self._on_plan)
        self._apply_btn.clicked.connect(self._on_apply)
        self._plan_result = None  # type: ignore[assignment]

    def _on_plan(self) -> None:
        from setupvault.services.restore_service import RestoreService

        path = self._path()
        if not path:
            self._out.setPlainText("Please select a snapshot file.")
            return
        self._plan_btn.setEnabled(False)
        self._apply_btn.setEnabled(False)
        self._loading.setVisible(True)
        self._loading.set_text("Planning")
        self._worker = Worker(RestoreService().plan, Path(path))
        self._worker.finished.connect(self._show_plan)
        self._worker.finished.connect(lambda _: self._plan_btn.setEnabled(True))
        self._worker.finished.connect(lambda _: self._apply_btn.setEnabled(True))
        self._worker.finished.connect(lambda _: self._loading.setVisible(False))
        self._worker.errored.connect(lambda e: self._out.setPlainText(f"Error: {e}"))
        self._worker.errored.connect(lambda _: self._plan_btn.setEnabled(True))
        self._worker.errored.connect(lambda _: self._apply_btn.setEnabled(True))
        self._worker.errored.connect(lambda _: self._loading.setVisible(False))
        self._worker.start()

    def _show_plan(self, plan) -> None:  # type: ignore[no-untyped-def]
        self._plan_result = plan
        lines = [f"Plan: {plan.snapshot_path}", f"Sections: {', '.join(plan.sections) or 'none'}"]
        if plan.errors:
            lines.append("Errors:")
            lines.extend(f"  - {e}" for e in plan.errors)
        if plan.warnings:
            lines.append("Warnings:")
            lines.extend(f"  - {w}" for w in plan.warnings)
        self._out.setPlainText("\n".join(lines))

    def _on_apply(self) -> None:
        from setupvault.services.restore_service import RestoreService

        if self._plan_result is None:
            self._out.setPlainText("Run a plan first.")
            return
        self._plan_btn.setEnabled(False)
        self._apply_btn.setEnabled(False)
        self._loading.setVisible(True)
        self._loading.set_text("Applying")
        self._worker = Worker(
            RestoreService().apply,
            self._plan_result,
            dry_run=self._dry.isChecked(),
            assume_yes=True,
        )
        self._worker.finished.connect(
            lambda r: self._out.appendPlainText(f"Apply done. Errors: {r.errors}")
        )
        self._worker.finished.connect(lambda _: self._plan_btn.setEnabled(True))
        self._worker.finished.connect(lambda _: self._apply_btn.setEnabled(True))
        self._worker.finished.connect(lambda _: self._loading.setVisible(False))
        self._worker.errored.connect(lambda e: self._out.appendPlainText(f"Error: {e}"))
        self._worker.errored.connect(lambda _: self._plan_btn.setEnabled(True))
        self._worker.errored.connect(lambda _: self._apply_btn.setEnabled(True))
        self._worker.errored.connect(lambda _: self._loading.setVisible(False))
        self._worker.start()


class SettingsPanel(BasePage):
    title = "Settings"
    description = "Customize appearance and default behaviour."

    _ACCENTS = {
        "Default": "",
        "Blue": "#1a73e8",
        "Green": "#1e8e3e",
        "Purple": "#6366F1",
        "Red": "#d64545",
        "Orange": "#e8710a",
    }

    def _build_body(self) -> None:
        from setupvault.gui.settings import GuiSettings

        self._settings_cls = GuiSettings
        section = Section("Appearance")
        self._theme = ComboField("Theme", ["system", "light", "dark"], "system")
        section.addWidget(self._theme)
        self._accent = ComboField("Accent", list(self._ACCENTS), "Default")
        section.addWidget(self._accent)
        self._density = ComboField("Density", ["comfortable", "compact"], "comfortable")
        section.addWidget(self._density)
        self._body_layout.addWidget(section)

        section2 = Section("Defaults")
        self._report_fmt = ComboField("Report format", ["markdown", "json", "html"], "markdown")
        section2.addWidget(self._report_fmt)
        self._profile = ComboField("Default profile", _profiles(), "full")
        section2.addWidget(self._profile)
        self._body_layout.addWidget(section2)

        self._status = QLabel("")
        self._body_layout.addWidget(self._status)

        self._save = QPushButton("Save Settings")
        self._save.setObjectName("Primary")
        self._save.clicked.connect(self._on_save)
        self._body_layout.addWidget(self._save)

    def apply_settings(self, settings) -> None:  # type: ignore[no-untyped-def]
        self._pending = settings
        self._theme.set_value(settings.theme)
        accent_label = next(
            (k for k, v in self._ACCENTS.items() if v == settings.accent), "Default"
        )
        self._accent.set_value(accent_label)
        self._density.set_value(settings.density)
        self._report_fmt.set_value(settings.default_report_format)
        self._profile.set_value(settings.default_profile)

    def _on_save(self) -> None:
        settings = self._settings_cls(
            theme=self._theme.value(),
            accent=self._ACCENTS.get(self._accent.value(), ""),
            density=self._density.value(),
            default_report_format=self._report_fmt.value(),
            default_profile=self._profile.value(),
        )
        settings.save()
        window = self.window()
        if hasattr(window, "reload_settings"):
            window.reload_settings()
        self._status.setText("Settings saved.")
