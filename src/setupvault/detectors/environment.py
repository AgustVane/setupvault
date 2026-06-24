from __future__ import annotations

import os
from dataclasses import dataclass

from setupvault.utils.shell import SafeCommandRunner


@dataclass(frozen=True)
class EnvironmentDetection:
    """Result of desktop environment / window manager detection."""

    desktop_environment: str | None = None
    desktop_environment_version: str | None = None
    window_manager: str | None = None
    window_manager_version: str | None = None
    display_server: str | None = None
    session_type: str | None = None


_KNOWN_DE_PROCESSES: dict[str, str] = {
    "gnome-shell": "GNOME",
    "plasmashell": "KDE Plasma",
    "xfce4-session": "XFCE",
    "cinnamon-session": "Cinnamon",
    "mate-session": "MATE",
    "lxqt-session": "LXQt",
    "lxsession": "LXDE",
    "budgie-wm": "Budgie",
    "deepin-wm": "Deepin",
    "sway": "Sway",
    "hyprland": "Hyprland",
    "i3": "i3",
    "openbox": "Openbox",
    "bspwm": "bspwm",
    "dwm": "dwm",
    "qtile": "Qtile",
    "awesome": "AwesomeWM",
    "xmonad": "XMonad",
    "herbstluftwm": "herbstluftwm",
    "fluxbox": "Fluxbox",
    "icewm": "IceWM",
    "jwm": "JWM",
    "pekwm": "PekWM",
    "spectrwm": "spectrwm",
}

_RUNNER = SafeCommandRunner(timeout=5.0)


def detect_environment() -> EnvironmentDetection:
    """Detect the desktop environment, window manager, and display server.

    Detection order:
        1. Environment variables (``$XDG_CURRENT_DESKTOP``,
           ``$XDG_SESSION_TYPE``, ``$DESKTOP_SESSION``).
        2. Process scan for known DE/WM binaries.
        3. Display server variables (``$WAYLAND_DISPLAY``, ``$DISPLAY``).

    Returns:
        An ``EnvironmentDetection`` with whatever could be determined.
    """
    de_name: str | None = None
    de_version: str | None = None
    wm_name: str | None = None

    # Step 1: Environment variables
    xdg_de = os.environ.get("XDG_CURRENT_DESKTOP")
    session_type = os.environ.get("XDG_SESSION_TYPE")

    if xdg_de:
        de_name = xdg_de
        # Some DEs set version in XDG_CURRENT_DESKTOP like "KDE:6.0.5"
        if ":" in xdg_de:
            parts = xdg_de.split(":")
            de_name = parts[0]
            de_version = parts[1] if len(parts) > 1 else None

    # Step 2: Process scan
    detected_processes = _scan_processes()

    for proc_name, display_name in _KNOWN_DE_PROCESSES.items():
        if proc_name in detected_processes:
            if proc_name in (
                "sway",
                "hyprland",
                "i3",
                "openbox",
                "bspwm",
                "dwm",
                "qtile",
                "awesome",
                "xmonad",
                "herbstluftwm",
                "fluxbox",
                "icewm",
                "jwm",
                "pekwm",
                "spectrwm",
            ):
                wm_name = display_name
            else:
                if de_name is None:
                    de_name = display_name
            break

    # Step 3: Display server detection
    display_server: str | None = None
    if os.environ.get("WAYLAND_DISPLAY"):
        display_server = "wayland"
    elif os.environ.get("DISPLAY"):
        display_server = "x11"
    else:
        display_server = "tty"

    return EnvironmentDetection(
        desktop_environment=de_name,
        desktop_environment_version=de_version,
        window_manager=wm_name,
        display_server=display_server,
        session_type=session_type,
    )


def _scan_processes() -> set[str]:
    """Scan ``/proc`` for running process names.

    Returns a set of executable names found in ``/proc/*/comm``.
    This is a Linux-specific, read-only operation.
    """
    processes: set[str] = set()
    try:
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                comm_path = f"/proc/{entry}/comm"
                with open(comm_path) as f:
                    name = f.read().strip()
                    if name:
                        processes.add(name)
            except (FileNotFoundError, OSError):
                continue
    except (FileNotFoundError, PermissionError):
        pass
    return processes
