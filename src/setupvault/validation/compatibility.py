from __future__ import annotations

from typing import Any

from setupvault.core.versions import CURRENT_SNAPSHOT_VERSION


def check_compatibility(data: dict[str, Any]) -> list[str]:
    """Run non-fatal compatibility checks on a snapshot.

    Args:
        data: Parsed snapshot dictionary.

    Returns:
        A list of warning messages (empty if all clear).
    """
    warnings: list[str] = []

    system = data.get("system", {})
    dist = system.get("distribution", {})
    if isinstance(dist, dict):
        distro_id = dist.get("id", "")
        if distro_id not in _KNOWN_DISTROS:
            warnings.append(
                f"Distribution '{distro_id}' is not in the known registry. "
                "Some features may not work."
            )

    sv = data.get("snapshot_version", 1)
    if isinstance(sv, int) and sv < CURRENT_SNAPSHOT_VERSION:
        warnings.append(
            f"Snapshot uses version {sv}; current is {CURRENT_SNAPSHOT_VERSION}. "
            "Consider re-exporting with the latest tool."
        )

    pkgs = data.get("packages", {})
    counts = pkgs.get("count", {})
    if isinstance(counts, dict):
        total = counts.get("total", 0)
        if isinstance(total, int) and total == 0:
            warnings.append("Package list is empty — snapshot may be incomplete.")

    dotfiles = data.get("dotfiles", [])
    if isinstance(dotfiles, list) and len(dotfiles) == 0:
        pass

    return warnings


_KNOWN_DISTROS = {
    "arch",
    "debian",
    "ubuntu",
    "fedora",
    "opensuse",
    "linuxmint",
    "pop",
    "manjaro",
    "endeavouros",
    "nixos",
}
