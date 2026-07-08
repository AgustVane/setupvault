from __future__ import annotations

import json

import pytest

from setupvault.core.snapshot import (
    DistributionInfo,
    KernelInfo,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    Snapshot,
    SystemInfo,
)
from setupvault.storage.local import dict_to_snapshot, snapshot_to_dict


def _full_snapshot() -> Snapshot:
    return Snapshot(
        snapshot_version=1,
        tool_version="1.0.0",
        created_at="2025-01-01T00:00:00",
        system=SystemInfo(
            distribution=DistributionInfo(
                id="arch",
                name="Arch Linux",
                version="rolling",
            ),
            kernel=KernelInfo(release="6.0.0", version="#1"),
            architecture="x86_64",
            hostname="box",
        ),
        packages=PackageCollection(
            counts=PackageCounts(official=100, aur=20),
            official=tuple(PackageEntry(name=f"pkg{i}", version=f"{i}.0") for i in range(100)),
            aur=tuple(PackageEntry(name=f"aur{i}", version=f"{i}.0") for i in range(20)),
        ),
    )


pytestmark = pytest.mark.benchmark(min_rounds=100)


def test_snapshot_to_dict_speed(benchmark) -> None:
    snap = _full_snapshot()
    result = benchmark(snapshot_to_dict, snap)
    assert isinstance(result, dict)
    assert result["snapshot_version"] == 1


def test_dict_to_snapshot_speed(benchmark) -> None:
    snap = _full_snapshot()
    data = snapshot_to_dict(snap)
    result = benchmark(dict_to_snapshot, data)
    assert isinstance(result, Snapshot)


def test_json_serialize_speed(benchmark) -> None:
    snap = _full_snapshot()
    data = snapshot_to_dict(snap)
    result = benchmark(json.dumps, data)
    assert isinstance(result, str)


def test_json_deserialize_speed(benchmark) -> None:
    snap = _full_snapshot()
    data = snapshot_to_dict(snap)
    raw = json.dumps(data)
    result = benchmark(json.loads, raw)
    assert isinstance(result, dict)
