from __future__ import annotations

from setupvault.core.snapshot import (
    GtkThemeInfo,
    QtThemeInfo,
    ThemeInfo,
)
from setupvault.detectors.themes import ThemeDetection


def export_themes(detection: ThemeDetection) -> ThemeInfo | None:
    """Transform theme detection data into a snapshot ``ThemeInfo``.

    Returns ``None`` if neither GTK nor Qt theme data was detected.
    """
    gtk: GtkThemeInfo | None = None
    qt: QtThemeInfo | None = None

    if detection.gtk is not None:
        gtk = GtkThemeInfo(
            theme=detection.gtk.theme,
            icon_theme=detection.gtk.icon_theme,
            cursor_theme=detection.gtk.cursor_theme,
            font_name=detection.gtk.font_name,
            color_scheme=detection.gtk.color_scheme,
        )

    if detection.qt is not None:
        qt = QtThemeInfo(
            theme=detection.qt.theme,
            icon_theme=detection.qt.icon_theme,
            font_name=detection.qt.font_name,
        )

    if gtk is None and qt is None:
        return None

    return ThemeInfo(gtk=gtk, qt=qt)
