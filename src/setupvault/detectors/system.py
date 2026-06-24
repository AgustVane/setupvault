from __future__ import annotations

from dataclasses import dataclass

from setupvault.utils.platform import (
    detect_architecture,
    detect_hostname,
    detect_kernel_release,
    detect_kernel_version,
    detect_os,
    get_uptime_seconds,
)


@dataclass(frozen=True)
class SystemDetection:
    """Result of system-level detection."""

    os_name: str
    kernel_release: str
    kernel_version: str
    architecture: str
    hostname: str
    uptime_seconds: int | None = None


def detect_system() -> SystemDetection:
    """Detect core system information.

    Returns:
        A ``SystemDetection`` dataclass with all available fields.
    """
    return SystemDetection(
        os_name=detect_os(),
        kernel_release=detect_kernel_release(),
        kernel_version=detect_kernel_version(),
        architecture=detect_architecture(),
        hostname=detect_hostname(),
        uptime_seconds=get_uptime_seconds(),
    )


def detect_distro_from_os_release() -> dict[str, str]:
    """Parse ``/etc/os-release`` and return key-value pairs.

    Returns an empty dict if the file cannot be read.
    """
    result: dict[str, str] = {}
    try:
        with open("/etc/os-release") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                result[key] = value.strip('"')
    except (FileNotFoundError, OSError):
        pass
    return result
