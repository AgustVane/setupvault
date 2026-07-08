from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from setupvault.gui.mainwindow import MainWindow
from setupvault.gui.pages import BasePage, EmptyState, ErrorState, Section
from setupvault.gui.styles import get_theme


@pytest.fixture(scope="session")
def app():  # type: ignore[no-untyped-def]
    existing = QApplication.instance()
    if existing is None:
        existing = QApplication([])
    yield existing


class TestMainWindowShell:
    def test_builds_with_all_command_pages(self, app) -> None:  # type: ignore[no-untyped-def]
        window = MainWindow(theme=get_theme("light"))
        assert window._stack.count() == 9
        assert window._nav.count() == 9
        assert window.windowTitle() == "SetupVault"

    def test_default_pages_are_real_panels(self, app) -> None:  # type: ignore[no-untyped-def]
        window = MainWindow(theme=get_theme("light"))
        page = window._stack.widget(0)
        from setupvault.gui.panels import ExportPanel

        assert isinstance(page, ExportPanel)

    def test_navigation_switches_stack(self, app) -> None:  # type: ignore[no-untyped-def]
        window = MainWindow(theme=get_theme("light"))
        window._nav.setCurrentRow(4)
        assert window._stack.currentIndex() == 4

    def test_apply_theme_rethemes_window(self, app) -> None:  # type: ignore[no-untyped-def]
        window = MainWindow(theme=get_theme("light"))
        window.apply_theme(get_theme("dark"))
        assert window._theme.name == "dark"

    def test_show_status(self, app) -> None:  # type: ignore[no-untyped-def]
        window = MainWindow(theme=get_theme("light"))
        window.show_status("Export complete", timeout=1000)
        assert window.statusBar().currentMessage() == "Export complete"


class TestPages:
    def test_base_page_renders(self, app) -> None:  # type: ignore[no-untyped-def]
        page = BasePage()
        assert page.title == "Untitled"

    def test_section_groups_widgets(self, app) -> None:  # type: ignore[no-untyped-def]
        section = Section("Demo")
        section.addWidget(BasePage())
        assert section.layout().count() >= 2


class TestStatePages:
    def test_empty_state(self, app) -> None:  # type: ignore[no-untyped-def]
        page = EmptyState("No data", "Select a file to begin.")
        assert page.isVisible() is False  # not shown yet

    def test_error_state(self, app) -> None:  # type: ignore[no-untyped-def]
        page = ErrorState("Oops", "An error occurred.")
        assert page.isVisible() is False
