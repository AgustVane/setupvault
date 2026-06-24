from __future__ import annotations

from dataclasses import dataclass

from setupvault.core.exceptions import DistributionDetectionError, UnsupportedDistributionError
from setupvault.distro_adapters import registry as adapter_registry
from setupvault.distro_adapters.base import DistroAdapter


@dataclass(frozen=True)
class DistroDetection:
    """Result of distribution detection."""

    adapter: DistroAdapter
    distro_id: str
    distro_name: str
    id_like: tuple[str, ...]


def detect_distro() -> DistroDetection:
    """Detect the current Linux distribution and return the matching adapter.

    Returns:
        A ``DistroDetection`` instance wrapping the active ``DistroAdapter``.

    Raises:
        DistributionDetectionError: If ``/etc/os-release`` cannot be read.
        UnsupportedDistributionError: If no adapter matches.
    """
    adapter = adapter_registry.get_adapter()
    info = adapter.get_distro_info()

    return DistroDetection(
        adapter=adapter,
        distro_id=info.id,
        distro_name=info.name,
        id_like=info.id_like,
    )


def detect_distro_for_snapshot() -> dict[str, str | list[str] | None]:
    """Detect distribution info for inclusion in a snapshot.

    This is a convenience wrapper that returns a plain dict suitable
    for the snapshot ``system.distribution`` field. Returns an empty
    dict on failure (non-fatal at the snapshot level).
    """
    try:
        detection = detect_distro()
        info = detection.adapter.get_distro_info()
        return {
            "id": info.id,
            "name": info.name,
            "version": info.version,
            "version_id": info.version_id,
            "id_like": list(info.id_like),
        }
    except (DistributionDetectionError, UnsupportedDistributionError):
        return {}
