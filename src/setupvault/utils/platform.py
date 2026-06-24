from __future__ import annotations

import os
import platform
import socket


def detect_os() -> str:
    """Return the operating system name."""
    return platform.system()


def detect_architecture() -> str:
    """Return the machine architecture (e.g. ``x86_64``, ``aarch64``)."""
    return platform.machine()


def detect_hostname() -> str:
    """Return the system hostname."""
    return socket.gethostname()


def detect_kernel_release() -> str:
    """Return the kernel release string."""
    return platform.release()


def detect_kernel_version() -> str:
    """Return the full kernel version string."""
    return platform.version()


def get_uptime_seconds() -> int | None:
    """Return system uptime in seconds, or ``None`` if unavailable."""
    try:
        with open("/proc/uptime") as f:
            return int(float(f.read().split()[0]))
    except (FileNotFoundError, OSError, IndexError, ValueError):
        return None


def is_linux() -> bool:
    """Return True if the current OS is Linux."""
    return detect_os() == "Linux"


def is_root() -> bool:
    """Return True if the current process is running as root."""
    return os.geteuid() == 0
