from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from setupvault.mappings.package_mapper import get_mapper


@dataclass(frozen=True)
class DistroInfo:
    """Parsed distribution identification data."""

    id: str
    name: str
    version: str
    version_id: str | None = None
    id_like: tuple[str, ...] = ()


@dataclass(frozen=True)
class Package:
    """A single installed package as reported by the package manager."""

    name: str
    version: str | None = None
    repository: str | None = None
    size: int | None = None
    description: str | None = None


@dataclass(frozen=True)
class InstallResult:
    """Outcome of a package installation operation."""

    success: bool
    installed: list[str]
    failed: list[str]
    errors: list[str]


class DistroAdapter(ABC):
    """Abstract interface for distribution-specific logic.

    Every supported Linux distribution implements this interface.
    Core and service code MUST always go through this abstraction
    and never invoke package manager commands directly.
    """

    @property
    @abstractmethod
    def distro_id(self) -> str:
        """Unique identifier matching the ``ID`` field in ``/etc/os-release``."""

    @property
    def distro_names(self) -> list[str]:
        """Human-readable distribution names (for display / matching)."""
        return [self.distro_id]

    @property
    def id_like(self) -> list[str]:
        """List of distribution families, corresponding to ``ID_LIKE``."""
        return []

    @abstractmethod
    def detect(self) -> bool:
        """Probe the system to confirm this distribution is active.

        Returns:
            ``True`` if this adapter matches the current system.
        """

    @abstractmethod
    def get_package_manager(self) -> str:
        """Return the primary package manager binary name (e.g. ``pacman``)."""

    @abstractmethod
    def list_official_packages(self) -> list[Package]:
        """Return all explicitly installed packages from official repositories."""

    def list_aur_packages(self) -> list[Package]:
        """Return AUR packages.

        Only meaningful on Arch Linux derivatives. Returns an empty list
        by default.
        """
        return []

    def list_third_party_packages(self) -> list[Package]:
        """Return packages installed from third-party repositories.

        Returns an empty list by default.
        """
        return []

    @abstractmethod
    def install_packages(
        self,
        packages: list[str],
        *,
        dry_run: bool = False,
        assume_yes: bool = False,
    ) -> InstallResult:
        """Install the given list of package names.

        Args:
            packages: Package names to install.
            dry_run: If ``True``, only simulate (print what would be done).
            assume_yes: If ``True``, answer ``yes`` to prompts automatically.

        Returns:
            An ``InstallResult`` summarising the operation.
        """

    def map_package(self, package_name: str, target_distro_id: str) -> str | None:
        """Map a package name from this distro to *target_distro_id*.

        Uses the global PackageMapper database. Returns ``None`` when
        no mapping is known.
        """
        mapper = get_mapper()
        return mapper.map(package_name, target=target_distro_id)

    @abstractmethod
    def get_distro_info(self) -> DistroInfo:
        """Return parsed distribution identification data."""

    def get_os_release_content(self) -> dict[str, str]:
        """Parse ``/etc/os-release`` into a key-value dictionary.

        This is a shared helper available to all adapters.
        """
        result: dict[str, str] = {}
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    key, _, value = line.partition("=")
                    result[key] = value.strip('"')
        except (FileNotFoundError, OSError):
            pass
        return result
