from __future__ import annotations

from setupvault.core.snapshot import (
    DistributionInfo,
    KernelInfo,
    SystemInfo,
)
from setupvault.detectors.system import SystemDetection


def export_system(
    detection: SystemDetection,
    distro_id: str,
    distro_name: str,
    distro_version: str,
    distro_version_id: str | None = None,
    distro_id_like: tuple[str, ...] = (),
) -> SystemInfo:
    """Transform system detection data into a snapshot ``SystemInfo``.

    Args:
        detection: Raw system detection result.
        distro_id: Distribution ID (e.g. ``"arch"``).
        distro_name: Human-readable distribution name.
        distro_version: Distribution version string.
        distro_version_id: Optional numeric version ID.
        distro_id_like: Distribution family identifiers.

    Returns:
        A ``SystemInfo`` ready for inclusion in a ``Snapshot``.
    """
    return SystemInfo(
        distribution=DistributionInfo(
            id=distro_id,
            name=distro_name,
            version=distro_version,
            version_id=distro_version_id,
            id_like=tuple(distro_id_like),
        ),
        kernel=KernelInfo(
            release=detection.kernel_release,
            version=detection.kernel_version,
        ),
        architecture=detection.architecture,
        hostname=detection.hostname,
        uptime_seconds=detection.uptime_seconds,
        os=detection.os_name,
    )
