from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from setupvault.gui.mainwindow import MainWindow
from setupvault.gui.panels import (
    DiffPanel,
    DoctorPanel,
    ExportPanel,
    InfoPanel,
    ListPanel,
    ReportPanel,
    RestorePanel,
    SettingsPanel,
    ValidatePanel,
)
from setupvault.gui.styles import get_theme


@pytest.fixture(scope="session")
def app():  # type: ignore[no-untyped-def]
    existing = QApplication.instance()
    if existing is None:
        existing = QApplication([])
    yield existing


def _window() -> MainWindow:
    return MainWindow(theme=get_theme("light"))


class TestPanelsInstantiate:
    def test_all_panels_build(self, app) -> None:  # type: ignore[no-untyped-def]
        for panel_cls in (
            ExportPanel,
            RestorePanel,
            InfoPanel,
            ValidatePanel,
            ReportPanel,
            DoctorPanel,
            DiffPanel,
            ListPanel,
        ):
            panel = panel_cls()
            assert panel is not None
        # ensure QApplication stays alive until widgets are destroyed
        app.processEvents()

    def test_export_uses_profiles(self, app) -> None:  # type: ignore[no-untyped-def]
        panel = ExportPanel()
        # The profile combobox should include built-ins.
        assert panel._profile.value() in ("full", "minimal", "packages-only")

    def test_info_reads_snapshot(self, app, tmp_path) -> None:  # type: ignore[no-untyped-def]
        snap = tmp_path / "s.json"
        snap.write_text(
            '{"snapshot_version":1,"tool_version":"2.0.0","created_at":"2025-01-01T00:00:00Z",'
            '"system":{"distribution":{"id":"arch","name":"Arch Linux","version":"rolling"},'
            '"kernel":{"release":"6.6.0","version":"#1"},"architecture":"x86_64","hostname":"box"},'
            '"packages":{"counts":{"official":0,"aur":0,"third_party":0,"flatpak":0,"snap":0},'
            '"official":[],"aur":[],"third_party":[],"flatpak":[],"snap":[]},"dotfiles":[]}'
        )
        panel = InfoPanel()
        panel._picker.set_path(str(snap))
        panel._on_info()
        assert "Arch Linux" in panel._out.toPlainText()

    def test_validate_runs_service(self, app, tmp_path) -> None:  # type: ignore[no-untyped-def]
        snap = tmp_path / "s.json"
        snap.write_text(
            '{"snapshot_version":1,"created_at":"2025-01-01T00:00:00Z","system":{},"packages":{"counts":{},"official":[],"aur":[],"third_party":[],"flatpak":[],"snap":[]},"dotfiles":[]}'
        )
        panel = ValidatePanel()
        panel._picker.set_path(str(snap))
        with patch("setupvault.services.validate_service.validate_snapshot") as mock_v:
            report = MagicMock()
            report.valid = True
            report.all_errors = []
            mock_v.return_value = report
            panel._on_validate()
            panel._worker.wait()
            app.processEvents()
        assert mock_v.called
        assert "Valid: True" in panel._out.toPlainText()

    def test_settings_panel_loads_saved(self, app) -> None:  # type: ignore[no-untyped-def]
        from setupvault.gui.settings import GuiSettings

        settings = GuiSettings(
            theme="dark",
            accent="#d64545",
            density="compact",
            default_profile="minimal",
            default_report_format="json",
        )
        panel = SettingsPanel()
        panel.apply_settings(settings)
        assert panel._theme_combo.value() == "dark"
        assert panel._density.value() == "compact"
        assert panel._profile.value() == "minimal"
        assert panel._report_fmt.value() == "json"

    def test_report_html_viewer_button(self, app) -> None:  # type: ignore[no-untyped-def]
        panel = ReportPanel()
        panel.show()  # parent must be visible for isVisible to work
        app.processEvents()
        assert not panel._view_html.isVisible()
        panel._fmt.set_value("html")
        panel._on_report_done("<h1>test</h1>")
        assert panel._view_html.isVisible()
        panel._fmt.set_value("markdown")
        panel._on_report_done("plain text")
        assert not panel._view_html.isVisible()
