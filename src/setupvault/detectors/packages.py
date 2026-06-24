from __future__ import annotations

from dataclasses import dataclass

from setupvault.distro_adapters.base import DistroAdapter, Package
from setupvault.utils.shell import SafeCommandRunner


@dataclass(frozen=True)
class PackageDetection:
    """Result of package detection."""

    official: tuple[Package, ...] = ()
    aur: tuple[Package, ...] = ()
    third_party: tuple[Package, ...] = ()
    flatpak: tuple[Package, ...] = ()
    snap: tuple[Package, ...] = ()

    @property
    def total_count(self) -> int:
        return (
            len(self.official)
            + len(self.aur)
            + len(self.third_party)
            + len(self.flatpak)
            + len(self.snap)
        )


_RUNNER = SafeCommandRunner(timeout=15.0)


def detect_official_packages(adapter: DistroAdapter) -> tuple[Package, ...]:
    """Detect official packages using the given distribution adapter.

    Returns:
        A tuple of ``Package`` entries.
    """
    try:
        packages = adapter.list_official_packages()
        return tuple(packages)
    except Exception:
        return ()


def detect_aur_packages(adapter: DistroAdapter) -> tuple[Package, ...]:
    """Detect AUR packages (Arch Linux only).

    Returns:
        A tuple of ``Package`` entries (may be empty on non-Arch distros).
    """
    try:
        packages = adapter.list_aur_packages()
        return tuple(packages)
    except Exception:
        return ()


def detect_third_party_packages(adapter: DistroAdapter) -> tuple[Package, ...]:
    """Detect packages from third-party repositories."""
    try:
        packages = adapter.list_third_party_packages()
        return tuple(packages)
    except Exception:
        return ()


def detect_flatpak_packages() -> tuple[Package, ...]:
    """Detect installed Flatpak applications."""
    if not _RUNNER.check_tool("flatpak"):
        return ()
    result = _RUNNER.run(
        ["flatpak", "list", "--app", "--columns=application,version,origin"],
        check=False,
        timeout=10.0,
    )
    if result.returncode != 0:
        return ()

    packages: list[Package] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if not parts:
            continue
        app_id = parts[0]
        version = parts[1] if len(parts) > 1 else None
        origin = parts[2] if len(parts) > 2 else None
        name = app_id.rsplit(".", 1)[-1] if "." in app_id else app_id
        packages.append(Package(name=name, version=version, repository=origin))
    return tuple(packages)


def detect_snap_packages() -> tuple[Package, ...]:
    """Detect installed Snap packages."""
    if not _RUNNER.check_tool("snap"):
        return ()
    result = _RUNNER.run(
        ["snap", "list"],
        check=False,
        timeout=10.0,
    )
    if result.returncode != 0:
        return ()

    packages: list[Package] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("Name") or line.startswith("---"):
            continue
        parts = line.split()
        if not parts:
            continue
        packages.append(
            Package(
                name=parts[0],
                version=parts[1] if len(parts) > 1 else None,
            )
        )
    return tuple(packages)
