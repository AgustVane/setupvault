from __future__ import annotations

import sys

from setupvault.gui.mainwindow import MainWindow
from setupvault.gui.settings import GuiSettings
from setupvault.gui.styles import resolve_theme, stylesheet


def launch(style: str = "system") -> int:
    """Launch the SetupVault GUI.

    Args:
        style: One of ``"light"``, ``"dark"``, or ``"system"``.

    Returns:
        Process exit code (0 on success).
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("SetupVault")

    settings = GuiSettings.load()
    # CLI --style overrides persisted setting when explicitly given.
    if style != "system":
        settings.theme = style
    theme = resolve_theme(settings.theme, settings.accent)
    app.setStyleSheet(stylesheet(theme, settings.density))

    window = MainWindow(settings=settings, theme=theme)
    window.show()
    return app.exec()


def main() -> None:
    """Console-script entry point for ``setupvault-gui``."""
    sys.exit(launch())


if __name__ == "__main__":
    main()
