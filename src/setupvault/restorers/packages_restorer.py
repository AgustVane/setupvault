from __future__ import annotations

from dataclasses import dataclass

from setupvault.core.snapshot import PackageCollection
from setupvault.distro_adapters.base import DistroAdapter, InstallResult


@dataclass(frozen=True)
class PackagesPlan:
    """Restoration plan for the packages section."""

    to_install: tuple[str, ...] = ()
    missing_names: tuple[str, ...] = ()
    already_present: int = 0
    unknown_names: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def plan_packages(
    snapshot_packages: PackageCollection,
    adapter: DistroAdapter,
) -> PackagesPlan:
    """Compare snapshot packages against currently installed and build a plan.

    Args:
        snapshot_packages: The ``PackageCollection`` from the snapshot.
        adapter: The current system's ``DistroAdapter`` for listing installed packages.

    Returns:
        A ``PackagesPlan`` describing what would be installed.
    """
    currently_installed = _get_installed_names(adapter)

    to_install: list[str] = []
    missing_names: list[str] = []
    unknown_names: list[str] = []
    warnings: list[str] = []

    all_snapshot_pkgs = (
        list(snapshot_packages.official)
        + list(snapshot_packages.aur)
        + list(snapshot_packages.third_party)
    )

    for pkg in all_snapshot_pkgs:
        name = pkg.name
        if not _is_safe_package_name(name):
            unknown_names.append(name)
            warnings.append(f"Package name '{name}' looks suspicious — skipping")
            continue
        if name in currently_installed:
            continue
        mapped = adapter.map_package(name, adapter.distro_id)
        resolved = mapped or name
        if resolved in currently_installed:
            continue
        to_install.append(resolved)

    if snapshot_packages.flatpak:
        warnings.append(
            f"Flatpak restore not implemented in v1 — {len(snapshot_packages.flatpak)} apps skipped"
        )
    if snapshot_packages.snap:
        warnings.append(
            f"Snap restore not implemented in v1 — {len(snapshot_packages.snap)} packages skipped"
        )

    return PackagesPlan(
        to_install=tuple(to_install),
        missing_names=tuple(missing_names),
        already_present=len(currently_installed & {p.name for p in all_snapshot_pkgs}),
        unknown_names=tuple(unknown_names),
        warnings=tuple(warnings),
    )


def apply_packages(
    plan: PackagesPlan,
    adapter: DistroAdapter,
    *,
    dry_run: bool = False,
    assume_yes: bool = False,
) -> InstallResult:
    """Execute the package install plan.

    Args:
        plan: The ``PackagesPlan`` returned by ``plan_packages``.
        adapter: The current system's ``DistroAdapter``.
        dry_run: If ``True``, simulate without making changes.
        assume_yes: If ``True``, answer ``yes`` to prompts automatically.

    Returns:
        An ``InstallResult`` describing the outcome.
    """
    if not plan.to_install:
        return InstallResult(success=True, installed=[], failed=[], errors=[])

    return adapter.install_packages(
        list(plan.to_install),
        dry_run=dry_run,
        assume_yes=assume_yes,
    )


def _get_installed_names(adapter: DistroAdapter) -> set[str]:
    """Get the set of installed package names from the adapter."""
    official = adapter.list_official_packages()
    aur = adapter.list_aur_packages()
    third_party = adapter.list_third_party_packages()
    return {p.name for p in official} | {p.name for p in aur} | {p.name for p in third_party}


_SAFE_PACKAGE_RE = __import__("re").compile(r"^[a-zA-Z0-9][a-zA-Z0-9@._+\-]*$")


def _is_safe_package_name(name: str) -> bool:
    return bool(_SAFE_PACKAGE_RE.match(name))
