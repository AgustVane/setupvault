from __future__ import annotations

import os
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path

from setupvault.utils.shell import SafeCommandRunner


@dataclass(frozen=True)
class GtkThemeDetection:
    """Detected GTK theming state."""

    theme: str | None = None
    icon_theme: str | None = None
    cursor_theme: str | None = None
    font_name: str | None = None
    color_scheme: str | None = None


@dataclass(frozen=True)
class QtThemeDetection:
    """Detected Qt theming state."""

    theme: str | None = None
    icon_theme: str | None = None
    font_name: str | None = None


@dataclass(frozen=True)
class ThemeDetection:
    """Result of theme detection."""

    gtk: GtkThemeDetection | None = None
    qt: QtThemeDetection | None = None


_RUNNER = SafeCommandRunner(timeout=5.0)


def detect_themes() -> ThemeDetection:
    """Detect desktop theme settings (GTK and Qt).

    Detection order:
        1. Try ``gsettings`` (most reliable for GNOME/GNOME-based DEs).
        2. Fallback to reading GTK settings files (``settings.ini``).
        3. Environment variables for Qt.

    Returns:
        A ``ThemeDetection`` with whatever could be determined.
    """
    gtk = _detect_gtk_themes()
    qt = _detect_qt_themes()

    return ThemeDetection(gtk=gtk, qt=qt)


def _detect_gtk_themes() -> GtkThemeDetection | None:
    """Detect GTK theme, icon theme, cursor theme, and font."""
    theme: str | None = None
    icon_theme: str | None = None
    cursor_theme: str | None = None
    font_name: str | None = None
    color_scheme: str | None = None

    # Method 1: gsettings
    if _RUNNER.check_tool("gsettings"):
        gsettings_map = {
            "gtk-theme": "org.gnome.desktop.interface",
            "icon-theme": "org.gnome.desktop.interface",
            "cursor-theme": "org.gnome.desktop.interface",
            "font-name": "org.gnome.desktop.interface",
            "color-scheme": "org.gnome.desktop.interface",
        }
        for key, schema in gsettings_map.items():
            result = _RUNNER.run(
                ["gsettings", "get", schema, key.replace("-", "_")],
                check=False,
            )
            if result.returncode == 0:
                value = result.stdout.strip().strip("'")
                if value and value != "":
                    if key == "gtk-theme":
                        theme = value
                    elif key == "icon-theme":
                        icon_theme = value
                    elif key == "cursor-theme":
                        cursor_theme = value
                    elif key == "font-name":
                        font_name = value
                    elif key == "color-scheme":
                        color_scheme = value

    # Method 2: Read GTK 3 settings file directly
    if theme is None:
        gtk3_config = Path.home() / ".config" / "gtk-3.0" / "settings.ini"
        if gtk3_config.exists():
            try:
                config = ConfigParser()
                config.read(gtk3_config)
                if config.has_section("Settings"):
                    section = config["Settings"]
                    theme = theme or section.get("gtk-theme-name") or section.get("gtk-theme-name")
                    icon_theme = icon_theme or section.get("gtk-icon-theme-name")
                    cursor_theme = cursor_theme or section.get("gtk-cursor-theme-name")
                    font_name = font_name or section.get("gtk-font-name")
                    color_scheme = color_scheme or section.get("gtk-color-scheme")
            except Exception:
                pass

    # Method 3: GTK 2 (using gtkrc)
    if theme is None:
        gtk2rc = Path.home() / ".gtkrc-2.0"
        if not gtk2rc.exists():
            gtk2rc = Path.home() / ".gtkrc"
        if gtk2rc.exists():
            try:
                for line in gtk2rc.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("gtk-theme-name"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            theme = parts[1].strip().strip('"')
            except Exception:
                pass

    if any((theme, icon_theme, cursor_theme, font_name, color_scheme)):
        return GtkThemeDetection(
            theme=theme,
            icon_theme=icon_theme,
            cursor_theme=cursor_theme,
            font_name=font_name,
            color_scheme=color_scheme,
        )
    return None


def _detect_qt_themes() -> QtThemeDetection | None:
    """Detect Qt theme settings."""
    theme: str | None = None
    icon_theme: str | None = None
    font_name: str | None = None

    # Environment variable
    env_theme = os.environ.get("QT_STYLE_OVERRIDE")
    if env_theme:
        theme = env_theme

    # Qt5 config
    qt5_config = Path.home() / ".config" / "qt5ct" / "qt5ct.conf"
    if qt5_config.exists():
        try:
            config = ConfigParser()
            config.read(qt5_config)
            if config.has_section("Appearance"):
                section = config["Appearance"]
                theme = theme or section.get("style")
                icon_theme = section.get("icon_theme") or icon_theme
                font_name = section.get("font") or font_name
        except Exception:
            pass

    # Qt6 config
    qt6_config = Path.home() / ".config" / "qt6ct" / "qt6ct.conf"
    if qt6_config.exists():
        try:
            config = ConfigParser()
            config.read(qt6_config)
            if config.has_section("Appearance"):
                section = config["Appearance"]
                theme = theme or section.get("style")
                icon_theme = section.get("icon_theme") or icon_theme
                font_name = section.get("font") or font_name
        except Exception:
            pass

    if any((theme, icon_theme, font_name)):
        return QtThemeDetection(
            theme=theme,
            icon_theme=icon_theme,
            font_name=font_name,
        )
    return None
