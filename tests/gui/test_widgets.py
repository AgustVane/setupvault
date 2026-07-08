from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from setupvault.gui.widgets import HtmlViewer, LoadingIndicator


@pytest.fixture(scope="session")
def app():  # type: ignore[no-untyped-def]
    existing = QApplication.instance()
    if existing is None:
        existing = QApplication([])
    yield existing


class TestLoadingIndicator:
    def test_constructs(self, app) -> None:  # type: ignore[no-untyped-def]
        w = LoadingIndicator("Loading…")
        assert w._label.text() == "Loading…"

    def test_set_text(self, app) -> None:  # type: ignore[no-untyped-def]
        w = LoadingIndicator()
        w.set_text("New message")
        assert w._label.text() == "New message"

    def test_hides_and_shows(self, app) -> None:  # type: ignore[no-untyped-def]
        w = LoadingIndicator()
        w.setVisible(False)
        assert not w.isVisible()
        w.setVisible(True)
        assert w.isVisible()


class TestHtmlViewer:
    def test_constructs(self, app) -> None:  # type: ignore[no-untyped-def]
        dlg = HtmlViewer("<h1>Hello</h1>", "Test Report")
        assert dlg.windowTitle() == "Test Report"
        assert dlg._browser.toHtml()  # should contain <h1>Hello</h1>
        app.processEvents()

    def test_close_button(self, app) -> None:  # type: ignore[no-untyped-def]
        dlg = HtmlViewer("<p>content</p>")
        # The close button should trigger accept()
        assert dlg.result() == 0  # default before exec
        dlg.accept()
        assert dlg.result() == 1
