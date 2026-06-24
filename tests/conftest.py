from __future__ import annotations

from pathlib import Path

import pytest

from setupvault.core.snapshot import (
    DistributionInfo,
    KernelInfo,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    Snapshot,
    SnapshotBuilder,
    SystemInfo,
)


@pytest.fixture
def sample_distro_info() -> DistributionInfo:
    return DistributionInfo(
        id="arch",
        name="Arch Linux",
        version="rolling",
        version_id="20260601",
        id_like=("arch",),
    )


@pytest.fixture
def sample_kernel_info() -> KernelInfo:
    return KernelInfo(
        release="6.6.32-arch1-1",
        version="#1 SMP PREEMPT_DYNAMIC Thu, 01 Jun 2026 00:00:00 +0000",
    )


@pytest.fixture
def sample_system_info(
    sample_distro_info: DistributionInfo, sample_kernel_info: KernelInfo
) -> SystemInfo:
    return SystemInfo(
        distribution=sample_distro_info,
        kernel=sample_kernel_info,
        architecture="x86_64",
        hostname="test-rig",
        uptime_seconds=86400,
    )


@pytest.fixture
def sample_package_collection() -> PackageCollection:
    return PackageCollection(
        counts=PackageCounts(official=1500, aur=50),
        official=(
            PackageEntry(name="linux", version="6.6.32.arch1-1", repository="core"),
            PackageEntry(name="firefox", version="127.0-1", repository="extra"),
        ),
        aur=(PackageEntry(name="yay", version="12.3.5-1"),),
    )


@pytest.fixture
def sample_snapshot(
    sample_system_info: SystemInfo,
    sample_package_collection: PackageCollection,
) -> Snapshot:
    return (
        SnapshotBuilder()
        .with_snapshot_version(1)
        .with_tool_version("1.0.0")
        .with_created_at("2026-06-24T14:30:00Z")
        .with_system(sample_system_info)
        .with_packages(sample_package_collection)
        .build()
    )


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_snapshot_path(fixture_dir: Path) -> Path:
    return fixture_dir / "snapshots" / "valid_full.json"
