from __future__ import annotations

from setupvault.core.exceptions import DistributionDetectionError, UnsupportedDistributionError
from setupvault.distro_adapters.arch import ArchAdapter
from setupvault.distro_adapters.base import DistroAdapter
from setupvault.distro_adapters.debian import DebianAdapter
from setupvault.distro_adapters.fedora import FedoraAdapter
from setupvault.distro_adapters.opensuse import OpenSUSEAdapter
from setupvault.distro_adapters.ubuntu import UbuntuAdapter

_ADAPTER_CLASSES: list[type[DistroAdapter]] = [
    ArchAdapter,
    FedoraAdapter,
    OpenSUSEAdapter,
    UbuntuAdapter,
    DebianAdapter,
]

_INSTANCE_CACHE: dict[str, DistroAdapter] = {}


def register(adapter_cls: type[DistroAdapter]) -> None:
    """Register a custom adapter class.

    Registered adapters take precedence over built-in adapters.
    """
    _ADAPTER_CLASSES.insert(0, adapter_cls)


def get_adapter() -> DistroAdapter:
    """Detect the current distribution and return the matching adapter.

    Iterates through all registered adapters and returns the first
    one whose ``detect()`` returns ``True``.

    Raises:
        DistributionDetectionError: If distribution detection fails entirely
            (e.g. ``/etc/os-release`` not found).
        UnsupportedDistributionError: If the distribution is detected but
            no adapter supports it.
    """
    os_release_found = False
    try:
        with open("/etc/os-release"):
            os_release_found = True
    except FileNotFoundError:
        pass

    for adapter_cls in _ADAPTER_CLASSES:
        adapter = adapter_cls()
        try:
            if adapter.detect():
                adapter_id = adapter.distro_id
                _INSTANCE_CACHE[adapter_id] = adapter
                return adapter
        except Exception:
            continue

    if os_release_found:
        raise UnsupportedDistributionError(
            "This Linux distribution was detected but is not yet supported. "
            "Run 'setupvault doctor' for diagnostics."
        )
    raise DistributionDetectionError(
        "Could not detect the Linux distribution. "
        "Is /etc/os-release present? "
        "Run 'setupvault doctor' for diagnostics."
    )


def get_adapter_for(distro_id: str) -> DistroAdapter:
    """Return an adapter for a specific distribution by its ID.

    Args:
        distro_id: Distribution ID (e.g. ``"arch"``, ``"debian"``, ``"fedora"``).

    Returns:
        A configured adapter instance.

    Raises:
        UnsupportedDistributionError: If no adapter matches *distro_id*.
    """
    if distro_id in _INSTANCE_CACHE:
        return _INSTANCE_CACHE[distro_id]

    for adapter_cls in _ADAPTER_CLASSES:
        adapter = adapter_cls()
        if adapter.distro_id == distro_id or distro_id in adapter.id_like:
            _INSTANCE_CACHE[distro_id] = adapter
            return adapter

    raise UnsupportedDistributionError(
        f"Distribution '{distro_id}' is not supported. "
        f"Known adapters: {[c().distro_id for c in _ADAPTER_CLASSES]}"
    )


def list_supported_distros() -> list[str]:
    """Return a list of supported distribution IDs."""
    return sorted({c().distro_id for c in _ADAPTER_CLASSES})
