from __future__ import annotations

from setupvault.core.snapshot import (
    FlatpakEntry,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    SnapEntry,
)
from setupvault.detectors.packages import PackageDetection


def export_packages(detection: PackageDetection) -> PackageCollection:
    """Transform package detection data into a snapshot ``PackageCollection``.

    All counts are computed automatically from the provided tuples.
    """
    official = tuple(
        PackageEntry(
            name=p.name,
            version=p.version,
            repository=p.repository,
            size=p.size,
            description=p.description,
        )
        for p in detection.official
    )

    aur = tuple(PackageEntry(name=p.name, version=p.version) for p in detection.aur)

    third_party = tuple(
        PackageEntry(name=p.name, version=p.version, repository=p.repository)
        for p in detection.third_party
    )

    flatpak = tuple(
        FlatpakEntry(
            name=p.name,
            app_id=p.name,
            version=p.version,
            origin=p.repository,
        )
        for p in detection.flatpak
    )

    snap_pkgs = tuple(SnapEntry(name=p.name, version=p.version) for p in detection.snap)

    counts = PackageCounts(
        official=len(official),
        aur=len(aur),
        third_party=len(third_party),
        flatpak=len(flatpak),
        snap=len(snap_pkgs),
    )

    return PackageCollection(
        counts=counts,
        official=official,
        aur=aur,
        third_party=third_party,
        flatpak=flatpak,
        snap=snap_pkgs,
    )
